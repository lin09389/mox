"""基准测试相关路由"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from mox.evaluation import BenchmarkRunner, BenchmarkDataset
from mox.attacks import PromptInjectionAttack, JailbreakAttack
from mox.core.auth import User
from mox.routes.auth_helpers import require_optional_access
from mox.routes.platform import _persist_platform_report

router = APIRouter(prefix="/benchmark", tags=["Benchmark"])


# ============ 请求模型 ============


class BenchmarkRequest(BaseModel):
    dataset: str = "advbench"
    attack_type: str = "prompt_injection"
    model: str = "abab2.5-chat"
    max_cases: int = Field(default=10, ge=1, le=500)  # Upper bound to prevent DoS


# ============ 依赖 ============

benchmark_runner = BenchmarkRunner()
benchmark_dataset = BenchmarkDataset()


# ============ 辅助函数 ============


def _get_llm(model: str):
    """获取 LLM 实例"""
    from mox.core import LLMFactory
    from mox.core.config import settings

    if model.startswith("abab") or model.startswith("minimax"):
        from mox.core import MiniMaxLLM

        return MiniMaxLLM(
            model=model,
            api_key=settings.MINIMAX_API_KEY,
            group_id=settings.MINIMAX_GROUP_ID,
        )
    return LLMFactory.create_from_model_name(model)


# ============ 路由端点 ============


require_benchmark_access = require_optional_access


@router.post("/run")
async def run_benchmark(
    request: BenchmarkRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_benchmark_access),
) -> Dict[str, Any]:
    """运行基准测试"""
    try:
        llm = _get_llm(request.model)

        attack_type_map = {
            "prompt_injection": PromptInjectionAttack,
            "jailbreak": JailbreakAttack,
        }

        attack_class = attack_type_map.get(request.attack_type, PromptInjectionAttack)
        attack = attack_class(target_llm=llm)

        payloads = benchmark_dataset.get_attack_payloads(request.dataset)[: request.max_cases]

        results = []
        for payload in payloads:
            outcome = await attack.generate_attack(payload)
            results.append(
                {
                    "result": outcome.result.value,
                    "success_score": outcome.success_score,
                    "iterations": outcome.iterations,
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
