"""基准测试相关路由"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from mox.evaluation import BenchmarkRunner, BenchmarkDataset
from mox.core.auth import User
from mox.routes.services import get_cached_llm, execute_registry_attack
from mox.routes.auth_helpers import require_optional_access
from mox.routes.platform import _persist_platform_report

router = APIRouter(prefix="/benchmark", tags=["Benchmark"])


# ============ 请求模型 ============


class BenchmarkRequest(BaseModel):
    dataset: str = "advbench"
    attack_type: str = "prompt_injection"
    model: str = "abab2.5-chat"
    max_cases: int = Field(default=10, ge=1, le=500)  # Upper bound to prevent DoS
    use_defense: bool = False


# ============ 依赖 ============

benchmark_runner = BenchmarkRunner()
benchmark_dataset = BenchmarkDataset()


# ============ 辅助函数 ============


# ============ 路由端点 ============


require_benchmark_access = require_optional_access


@router.get("/gcg-profile")
async def gcg_profile(
    current_user: User = Depends(require_benchmark_access),
) -> Dict[str, Any]:
    """Improved GCG 硬件与并行配置剖析（无需 LLM 调用）"""
    from mox.attacks.gcg_benchmark import profile_gcg_config

    return profile_gcg_config()


@router.post("/run")
async def run_benchmark(
    request: BenchmarkRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_benchmark_access),
) -> Dict[str, Any]:
    """运行基准测试"""
    try:
        llm = get_cached_llm(request.model)
        payloads = benchmark_dataset.get_attack_payloads(request.dataset)[: request.max_cases]

        defense_pipeline = None
        if request.use_defense:
            from mox.defense.pipeline_factory import create_default_defense_pipeline

            defense_pipeline = create_default_defense_pipeline()

        results = []
        blocked_by_defense = 0
        for payload in payloads:
            if defense_pipeline:
                check = await defense_pipeline.check(payload.prompt)
                if check.is_malicious:
                    blocked_by_defense += 1
                    results.append(
                        {
                            "result": "failure",
                            "success_score": 0.0,
                            "iterations": 0,
                            "defense_blocked": True,
                        }
                    )
                    continue
            outcome = await execute_registry_attack(
                request.attack_type,
                llm,
                payload.prompt,
                target_behavior=payload.target_behavior,
            )
            results.append(
                {
                    "result": outcome.result.value,
                    "success_score": outcome.success_score,
                    "iterations": outcome.iterations,
                    "defense_blocked": False,
                }
            )

        successful = sum(1 for r in results if r["result"] == "success")
        total = len(results)
        attack_rate = round(successful / total, 4) if total > 0 else 0.0
        defense_rate = round(1 - attack_rate, 4)

        payload = {
            "dataset": request.dataset,
            "attack_type": request.attack_type,
            "model": request.model,
            "use_defense": request.use_defense,
            "defense_blocked_count": blocked_by_defense,
            "total_cases": total,
            "successful_attacks": successful,
            "failed_attacks": total - successful,
            "attack_success_rate": attack_rate,
            "defense_success_rate": defense_rate,
            "detailed_results": results,
        }

        report_id: Optional[int] = await _persist_platform_report(
            report_name=f"基准评测 ({request.dataset} / {request.attack_type})",
            report_type="benchmark",
            model_name=request.model,
            content=payload,
            summary={
                "attack_success_rate": attack_rate,
                "defense_success_rate": defense_rate,
                "dataset": request.dataset,
                "attack_type": request.attack_type,
                "total_cases": total,
            },
            source="benchmark",
        )
        if report_id is not None:
            payload["report_id"] = report_id
        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets")
async def list_datasets() -> Dict[str, List[Dict[str, Any]]]:
    """列出可用的基准测试数据集"""
    datasets = benchmark_dataset.list_datasets()
    return {"datasets": [benchmark_dataset.get_dataset_info(name) for name in datasets]}
