"""攻击循环测试路由

提供攻击循环的 REST API 接口，支持：
- 配置驱动的批量攻击测试
- 断点续跑（检查点机制）
- YAML 配置文件启动
- 进度跟踪与任务管理
- 多格式报告导出
"""

import asyncio
import uuid
import os
import json
import io
import csv
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from mox.attack_loop import (
    AttackLoopRunner,
    LoopConfig,
    CheckpointManager,
    TestStatistics,
    ReportGenerator,
    AttackTestResult,
)

router = APIRouter(prefix="/attack-loop", tags=["Attack Loop"])
logger = logging.getLogger(__name__)


# ============================================================
# 数据模型
# ============================================================


class AttackLoopConfig(BaseModel):
    """攻击循环配置"""

    models: List[str] = Field(..., min_length=1, description="模型列表")
    attack_types: List[str] = Field(..., min_length=1, description="攻击类型列表")
    prompts: List[str] = Field(default_factory=list, description="测试提示列表")
    iterations_per_combo: int = Field(default=1, ge=1, le=100, description="每组合迭代次数")
    delay_between_tests: float = Field(default=1.0, ge=0, le=60, description="测试间隔时间（秒）")
    max_concurrency: int = Field(default=1, ge=1, le=10, description="最大并发数")
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    retry_delay: float = Field(default=1.0, ge=0, le=60, description="重试延迟（秒）")
    output_dir: str = Field(default="attack_loop_results", description="输出目录")
    base_url: str = Field(default="http://localhost:11434/v1", description="Ollama服务地址")
    success_threshold: float = Field(default=0.6, ge=0, le=1, description="成功阈值")
    max_iterations: int = Field(default=5, ge=1, le=100, description="攻击最大迭代次数")

    # 随机提示配置
    random_prompts: bool = Field(default=False, description="是否启用随机提示生成")
    random_prompt_templates: List[str] = Field(
        default_factory=list, description="自定义随机提示模板（留空使用内置模板）"
    )
    random_prompt_count: int = Field(default=10, ge=1, le=1000, description="随机提示生成数量")

    # 检查点配置
    checkpoint_enabled: bool = Field(default=True, description="是否启用检查点")
    checkpoint_interval: int = Field(default=10, ge=1, description="检查点保存间隔（测试数）")

    # 日志配置
    log_file: Optional[str] = Field(default=None, description="日志文件路径")
    log_level: str = Field(default="INFO", description="日志级别")


class AttackLoopProgress(BaseModel):
    """攻击循环进度"""

    task_id: str
    status: str  # pending, running, paused, completed, failed, stopped
    total: int
    completed: int
    successful: int
    failed: int
    errors: int
    progress_percent: float
    elapsed_seconds: float
    rate_per_second: float
    eta_seconds: float
    resumed_from_checkpoint: bool = False
    results: Optional[Dict[str, Any]] = None
    reports: Optional[Dict[str, str]] = None
    report_id: Optional[int] = None
    error: Optional[str] = None


class StartFromConfigResponse(BaseModel):
    """从配置文件启动响应"""

    task_id: str
    status: str
    config_summary: Dict[str, Any]
    resumed_from_checkpoint: bool = False
    checkpoint_info: Optional[Dict[str, Any]] = None


# ============================================================
# 任务管理
# ============================================================


class AttackLoopTask:
    """攻击循环任务"""

    def __init__(self, task_id: str, config: AttackLoopConfig, resume: bool = True):
        self.task_id = task_id
        self.config = config
        self.status = "pending"
        self.total = 0
        self.completed = 0
        self.successful = 0
        self.failed = 0
        self.errors = 0
        self.start_time = None
        self.end_time = None
        self.results: List[AttackTestResult] = []
        self.reports: Dict[str, str] = {}
        self.report_id: Optional[int] = None
        self.error: Optional[str] = None
        self.resumed_from_checkpoint = False

        # 内部运行器
        self._runner: Optional[AttackLoopRunner] = None
        self._run_task: Optional[asyncio.Task] = None


# 全局任务存储
tasks: Dict[str, AttackLoopTask] = {}


def get_task(task_id: str) -> AttackLoopTask:
    """获取任务"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    return tasks[task_id]


def _pydantic_to_loopconfig(pydantic_config: AttackLoopConfig) -> LoopConfig:
    """将 Pydantic 配置转换为核心引擎的 LoopConfig"""
    return LoopConfig(
        models=pydantic_config.models,
        attack_types=pydantic_config.attack_types,
        prompts=pydantic_config.prompts,
        iterations_per_combo=pydantic_config.iterations_per_combo,
        delay_between_tests=pydantic_config.delay_between_tests,
        max_concurrency=pydantic_config.max_concurrency,
        max_retries=pydantic_config.max_retries,
        retry_delay=pydantic_config.retry_delay,
        output_dir=pydantic_config.output_dir,
        base_url=pydantic_config.base_url,
        success_threshold=pydantic_config.success_threshold,
        max_iterations=pydantic_config.max_iterations,
        random_prompts=pydantic_config.random_prompts,
        random_prompt_templates=pydantic_config.random_prompt_templates,
        random_prompt_count=pydantic_config.random_prompt_count,
        checkpoint_enabled=pydantic_config.checkpoint_enabled,
        checkpoint_interval=pydantic_config.checkpoint_interval,
        log_file=pydantic_config.log_file,
        log_level=pydantic_config.log_level,
    )


# ============================================================
# 任务执行
# ============================================================


def _sync_task_store(task: AttackLoopTask) -> None:
    from mox.core.task_store import get_task_store

    progress = int((task.completed / task.total) * 100) if task.total else 0
    get_task_store().update(
        task.task_id,
        status=task.status,
        progress=progress,
        total=task.total,
        completed=task.completed,
        failed=task.failed,
        source="attack_loop",
        name=f"攻击循环 ({task.task_id})",
        report_id=task.report_id,
    )


async def _persist_attack_loop_report(task: AttackLoopTask) -> Optional[int]:
    """Save completed attack-loop stats as an evaluation report."""
    if not task.results:
        return None
    try:
        from mox.core.database import get_extended_database

        stats = TestStatistics.calculate(task.results)
        stats_dict = stats.to_dict()
        total = stats.total_tests or 1
        attack_rate = round(stats.successful_tests / total, 4)
        defense_rate = round(1 - attack_rate, 4)
        models_label = ", ".join(task.config.models[:3])
        if len(task.config.models) > 3:
            models_label += "..."

        report_id = await get_extended_database().save_report(
            {
                "report_name": f"攻击循环报告 ({task.task_id})",
                "report_type": "evaluation",
                "model_name": models_label,
                "format": "json",
                "content": json.dumps(stats_dict, ensure_ascii=False, default=str),
                "summary": {
                    "attack_success_rate": attack_rate,
                    "defense_success_rate": defense_rate,
                    "task_id": task.task_id,
                    "total_tests": stats.total_tests,
                },
                "created_by": "attack_loop",
            }
        )
        try:
            from mox.core.audit import get_audit_logger

            await get_audit_logger().log(
                action="report_create",
                resource=f"report:{report_id}",
                context=get_audit_logger().create_context(
                    endpoint="/api/v1/attack-loop",
                    method="POST",
                ),
                request_body={
                    "task_id": task.task_id,
                    "report_id": report_id,
                    "source": "attack_loop",
                },
                response_status=200,
            )
        except Exception:
            pass
        return report_id
    except Exception as exc:
        logger.warning(f"保存攻击循环报告失败: {exc}")
    return None


def _notify_ws_progress(task: AttackLoopTask) -> None:
    """Push progress updates to WebSocket listeners (best-effort)."""
    try:
        from mox.routes.websocket import manager

        elapsed = (datetime.now() - task.start_time).total_seconds() if task.start_time else 0
        rate = task.completed / elapsed if elapsed > 0 else 0
        eta = (task.total - task.completed) / rate if rate > 0 else 0
        progress_percent = (task.completed / task.total * 100) if task.total > 0 else 0

        payload = {
            "status": task.status,
            "total": task.total,
            "completed": task.completed,
            "successful": task.successful,
            "failed": task.failed,
            "errors": task.errors,
            "progress_percent": round(progress_percent, 1),
            "elapsed_seconds": round(elapsed, 1),
            "rate_per_second": round(rate, 2),
            "eta_seconds": round(eta, 0),
        }
        loop = asyncio.get_running_loop()
        loop.create_task(manager.notify_task_update(task.task_id, payload))
    except Exception:
        pass


async def _run_attack_loop(task: AttackLoopTask, resume: bool = True):
    """执行攻击循环（异步后台任务）"""
    try:
        task.status = "running"
        task.start_time = datetime.now()

        # 转换配置
        loop_config = _pydantic_to_loopconfig(task.config)

        # 创建运行器
        runner = AttackLoopRunner(loop_config)
        task._runner = runner

        # 设置进度回调
        def _progress_callback(total, completed, successful, failed, errors, current_result=None):
            task.total = total
            task.completed = completed
            task.successful = successful
            task.failed = failed
            task.errors = errors
            _sync_task_store(task)
            _notify_ws_progress(task)

        runner.set_progress_callback(_progress_callback)

        # 运行
        result = await runner.run(resume=resume)

        # 保存结果
        task.results = result["results"]
        task.reports = {k: str(v) for k, v in result.get("reports", {}).items()}
        task.status = "completed"
        task.end_time = datetime.now()
        _sync_task_store(task)
        _notify_ws_progress(task)
        report_id = await _persist_attack_loop_report(task)
        if report_id is not None:
            task.report_id = report_id
            _sync_task_store(task)

    except asyncio.CancelledError:
        task.status = "stopped"
        task.end_time = datetime.now()
        _sync_task_store(task)
        if task._runner:
            # 保存检查点
            if task.config.checkpoint_enabled and task.results:
                try:
                    cp_mgr = CheckpointManager(str(Path(task.config.output_dir) / "checkpoints"))
                    cp_mgr.save(
                        [r.test_id for r in task.results],
                        task.results,
                    )
                except Exception as e:
                    logger.warning(f"停止时保存检查点失败: {e}")
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.end_time = datetime.now()
        _sync_task_store(task)
        _notify_ws_progress(task)
        # 出错时也尝试保存检查点
        if task.config.checkpoint_enabled and task.results:
            try:
                cp_mgr = CheckpointManager(str(Path(task.config.output_dir) / "checkpoints"))
                cp_mgr.save(
                    [r.test_id for r in task.results],
                    task.results,
                )
            except Exception as e:
                logger.warning(f"失败时保存检查点失败: {e}")


# ============================================================
# API 端点
# ============================================================


@router.post("/start")
async def start_attack_loop(config: AttackLoopConfig, background_tasks: BackgroundTasks):
    """启动攻击循环测试

    使用 JSON 配置启动一个新的攻击循环任务。
    如果启用了检查点且存在有效检查点，将自动续跑。
    """
    from mox.core.task_store import get_task_store

    task_id = str(uuid.uuid4())[:8]
    task = AttackLoopTask(task_id, config)
    tasks[task_id] = task
    get_task_store().set(
        task_id,
        {
            "id": task_id,
            "source": "attack_loop",
            "name": f"攻击循环 ({task_id})",
            "status": "running",
            "progress": 0,
            "total": 0,
            "completed": 0,
            "failed": 0,
        },
    )

    # 检查是否有可续跑的检查点
    if config.checkpoint_enabled:
        cp_dir = Path(config.output_dir) / "checkpoints"
        cp_mgr = CheckpointManager(str(cp_dir))
        if cp_mgr.exists():
            task.resumed_from_checkpoint = True

    # 在后台执行任务
    loop = asyncio.get_event_loop()
    run_coro = _run_attack_loop(task, resume=True)
    task._run_task = loop.create_task(run_coro)

    return {
        "task_id": task_id,
        "status": "started",
        "resumed_from_checkpoint": task.resumed_from_checkpoint,
    }


@router.post("/start-from-config")
async def start_from_config_file(
    config_file: UploadFile = File(..., description="YAML 配置文件"),
    resume: bool = Form(True, description="是否从检查点续跑"),
):
    """从 YAML 配置文件启动攻击循环

    上传一个 YAML 配置文件，解析后启动攻击循环任务。
    字段缺失时返回清晰的字段级错误提示。

    支持 `resume=true` 时自动从检查点续跑（如果存在）。
    """
    # 读取并验证配置文件
    if not config_file.filename:
        raise HTTPException(status_code=400, detail="请提供配置文件名")

    # 检查文件扩展名
    if not (config_file.filename.endswith(".yaml") or config_file.filename.endswith(".yml")):
        raise HTTPException(status_code=400, detail="仅支持 .yaml 或 .yml 格式的配置文件")

    # 读取文件内容
    try:
        content = await config_file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取配置文件失败: {e}")

    # 保存到临时文件以使用 LoopConfig.from_yaml
    import tempfile

    try:
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".yaml", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建临时文件失败: {e}")

    # 解析配置
    try:
        loop_config = LoopConfig.from_yaml(tmp_path)
    except ValueError as e:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise HTTPException(status_code=400, detail=f"配置解析失败: {e}")

    # 清理临时文件
    try:
        os.unlink(tmp_path)
    except OSError:
        pass

    # 验证 prompts：如果既没有 prompts 也没开 random_prompts，报错
    if not loop_config.prompts and not loop_config.random_prompts:
        raise HTTPException(
            status_code=400, detail="配置错误: 必须提供 prompts 或启用 random_prompts"
        )

    # 转换为 Pydantic 配置（供 API 层使用）
    pydantic_config = AttackLoopConfig(
        models=loop_config.models,
        attack_types=loop_config.attack_types,
        prompts=loop_config.prompts,
        iterations_per_combo=loop_config.iterations_per_combo,
        delay_between_tests=loop_config.delay_between_tests,
        max_concurrency=loop_config.max_concurrency,
        max_retries=loop_config.max_retries,
        retry_delay=loop_config.retry_delay,
        output_dir=loop_config.output_dir,
        base_url=loop_config.base_url,
        success_threshold=loop_config.success_threshold,
        max_iterations=loop_config.max_iterations,
        random_prompts=loop_config.random_prompts,
        random_prompt_templates=loop_config.random_prompt_templates,
        random_prompt_count=loop_config.random_prompt_count,
        checkpoint_enabled=loop_config.checkpoint_enabled,
        checkpoint_interval=loop_config.checkpoint_interval,
        log_file=loop_config.log_file,
        log_level=loop_config.log_level,
    )

    # 创建任务
    task_id = str(uuid.uuid4())[:8]
    task = AttackLoopTask(task_id, pydantic_config, resume=resume)
    tasks[task_id] = task

    # 检查检查点信息
    checkpoint_info = None
    if loop_config.checkpoint_enabled and resume:
        cp_dir = Path(loop_config.output_dir) / "checkpoints"
        cp_mgr = CheckpointManager(str(cp_dir))
        if cp_mgr.exists():
            cp_data = cp_mgr.load()
            task.resumed_from_checkpoint = True
            checkpoint_info = {
                "completed_tests": len(cp_data.get("completed_tests", [])),
                "results_count": cp_data.get("results_count", 0),
                "timestamp": cp_data.get("timestamp"),
            }

    # 在后台执行任务
    loop = asyncio.get_event_loop()
    run_coro = _run_attack_loop(task, resume=resume)
    task._run_task = loop.create_task(run_coro)

    # 配置摘要
    config_summary = {
        "models_count": len(loop_config.models),
        "attack_types_count": len(loop_config.attack_types),
        "prompts_count": len(loop_config.prompts),
        "random_prompts": loop_config.random_prompts,
        "random_prompt_count": loop_config.random_prompt_count if loop_config.random_prompts else 0,
        "iterations_per_combo": loop_config.iterations_per_combo,
        "max_concurrency": loop_config.max_concurrency,
        "checkpoint_enabled": loop_config.checkpoint_enabled,
        "estimated_total": (
            len(loop_config.models)
            * len(loop_config.attack_types)
            * (
                len(loop_config.prompts)
                + (loop_config.random_prompt_count if loop_config.random_prompts else 0)
            )
            * loop_config.iterations_per_combo
        ),
    }

    return StartFromConfigResponse(
        task_id=task_id,
        status="started",
        config_summary=config_summary,
        resumed_from_checkpoint=task.resumed_from_checkpoint,
        checkpoint_info=checkpoint_info,
    )


@router.get("/progress/{task_id}")
async def get_progress(task_id: str) -> AttackLoopProgress:
    """获取任务进度"""
    task = get_task(task_id)

    # 计算进度
    elapsed = (datetime.now() - task.start_time).total_seconds() if task.start_time else 0
    rate = task.completed / elapsed if elapsed > 0 else 0
    eta = (task.total - task.completed) / rate if rate > 0 else 0
    progress_percent = (task.completed / task.total * 100) if task.total > 0 else 0

    # 计算统计信息
    results_stats = None
    if task.status == "completed" and task.results:
        stats = TestStatistics.calculate(task.results)
        results_stats = stats.to_dict()

    return AttackLoopProgress(
        task_id=task_id,
        status=task.status,
        total=task.total,
        completed=task.completed,
        successful=task.successful,
        failed=task.failed,
        errors=task.errors,
        progress_percent=round(progress_percent, 1),
        elapsed_seconds=round(elapsed, 1),
        rate_per_second=round(rate, 2),
        eta_seconds=round(eta, 0),
        resumed_from_checkpoint=task.resumed_from_checkpoint,
        results=results_stats,
        reports=task.reports if task.status == "completed" else None,
        report_id=task.report_id,
        error=task.error,
    )


@router.post("/pause/{task_id}")
async def pause_task(task_id: str):
    """暂停任务"""
    task = get_task(task_id)
    if task.status != "running":
        raise HTTPException(status_code=400, detail="任务未在运行中")

    if task._runner:
        task._runner.pause()
    task.status = "paused"
    return {"status": "paused", "task_id": task_id}


@router.post("/resume/{task_id}")
async def resume_task(task_id: str):
    """恢复任务"""
    task = get_task(task_id)
    if task.status != "paused":
        raise HTTPException(status_code=400, detail="任务未暂停")

    if task._runner:
        task._runner.resume()
    task.status = "running"
    return {"status": "resumed", "task_id": task_id}


@router.post("/stop/{task_id}")
async def stop_task(task_id: str):
    """停止任务

    停止后会自动保存检查点（如果启用）。
    可以在下次使用相同配置启动时续跑。
    """
    task = get_task(task_id)
    if task.status not in ["running", "paused", "pending"]:
        raise HTTPException(status_code=400, detail="任务无法停止")

    if task._runner:
        task._runner.stop()

    if task._run_task and not task._run_task.done():
        task._run_task.cancel()

    task.status = "stopped"
    return {"status": "stopped", "task_id": task_id}


@router.get("/checkpoint/{task_id}")
async def get_checkpoint_info(task_id: str):
    """获取检查点信息"""
    task = get_task(task_id)

    if not task.config.checkpoint_enabled:
        return {
            "checkpoint_enabled": False,
            "exists": False,
        }

    cp_dir = Path(task.config.output_dir) / "checkpoints"
    cp_mgr = CheckpointManager(str(cp_dir))
    checkpoints = cp_mgr.list_checkpoints()

    return {
        "checkpoint_enabled": True,
        "checkpoint_dir": str(cp_dir),
        "exists": len(checkpoints) > 0,
        "checkpoints": checkpoints,
    }


@router.post("/checkpoint/clear/{task_id}")
async def clear_checkpoint(task_id: str):
    """清除任务的检查点"""
    task = get_task(task_id)

    cp_dir = Path(task.config.output_dir) / "checkpoints"
    cp_mgr = CheckpointManager(str(cp_dir))

    if not cp_mgr.exists():
        raise HTTPException(status_code=404, detail="没有找到检查点")

    cp_mgr.clear()
    return {"status": "cleared", "task_id": task_id}


@router.get("/download/{task_id}")
async def download_results(task_id: str, format: str = "json"):
    """下载测试结果

    支持格式: json, csv, html, txt
    """
    task = get_task(task_id)

    if not task.results:
        raise HTTPException(status_code=400, detail="没有可下载的结果")

    if format == "json":
        content = json.dumps([r.to_dict() for r in task.results], ensure_ascii=False, indent=2)
        media_type = "application/json"
        filename = f"attack_loop_{task_id}.json"

    elif format == "csv":
        output = io.StringIO()
        if task.results:
            writer = csv.DictWriter(output, fieldnames=task.results[0].to_dict().keys())
            writer.writeheader()
            for r in task.results:
                writer.writerow(r.to_dict())
        content = output.getvalue()
        media_type = "text/csv"
        filename = f"attack_loop_{task_id}.csv"

    elif format == "html":
        # 使用 ReportGenerator 生成 HTML
        stats = TestStatistics.calculate(task.results)
        loop_config = _pydantic_to_loopconfig(task.config)
        report_gen = ReportGenerator(task.config.output_dir)
        content = report_gen._generate_html_content(task.results, stats, loop_config)
        media_type = "text/html"
        filename = f"attack_loop_{task_id}.html"

    elif format == "txt":
        lines = []
        lines.append("=" * 60)
        lines.append("攻击循环测试报告")
        lines.append("=" * 60)
        lines.append(f"任务ID: {task_id}")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"总测试数: {task.completed}")
        lines.append(f"成功: {task.successful}")
        lines.append(f"失败: {task.failed}")
        lines.append("")
        lines.append("详细结果:")
        lines.append("-" * 60)
        for r in task.results:
            status = "成功" if r.success else "失败"
            lines.append(f"[{r.test_id}] {r.model} - {r.attack_name}")
            lines.append(f"  状态: {status}")
            lines.append(f"  分数: {r.success_score:.2f}")
            lines.append(f"  耗时: {r.duration:.1f}s")
            if r.error:
                lines.append(f"  错误: {r.error}")
            lines.append("")
        content = "\n".join(lines)
        media_type = "text/plain"
        filename = f"attack_loop_{task_id}.txt"

    else:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {format}")

    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/history")
async def get_history(limit: int = 10, offset: int = 0):
    """获取任务历史"""
    history = []
    all_tasks = list(tasks.items())
    for task_id, task in all_tasks[offset : offset + limit]:
        history.append(
            {
                "task_id": task_id,
                "status": task.status,
                "total": task.total,
                "completed": task.completed,
                "successful": task.successful,
                "failed": task.failed,
                "errors": task.errors,
                "created_at": task.start_time.isoformat() if task.start_time else None,
                "finished_at": task.end_time.isoformat() if task.end_time else None,
                "config": {
                    "models_count": len(task.config.models),
                    "attack_types_count": len(task.config.attack_types),
                    "prompts_count": len(task.config.prompts),
                    "checkpoint_enabled": task.config.checkpoint_enabled,
                },
                "reports": task.reports if task.status == "completed" else None,
                "resumed_from_checkpoint": task.resumed_from_checkpoint,
            }
        )

    return {"history": history, "total": len(tasks)}


def _build_attack_types_response() -> Dict[str, Any]:
    """Build attack type list from the global registry."""
    from mox.attacks.registry import get_all_attack_types

    all_types = get_all_attack_types()
    attack_types = []
    for key, info in all_types.items():
        attack_types.append(
            {
                "key": key,
                "value": key,
                "name": info.name,
                "category": (
                    info.category.value if hasattr(info.category, "value") else str(info.category)
                ),
                "description": info.description,
            }
        )

    return {"attack_types": attack_types, "total": len(attack_types)}


@router.get("/attack-types")
async def get_available_attack_types():
    """获取可用的攻击类型列表（来自全局主注册表）"""
    return _build_attack_types_response()


@router.get("/types")
async def get_attack_types_alias():
    """兼容前端 /attack-loop/types 路径"""
    return _build_attack_types_response()
