"""基准测试相关路由"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from mox.evaluation import BenchmarkRunner, BenchmarkDataset
from mox.attacks import PromptInjectionAttack, JailbreakAttack
from mox.infrastructure.auth import get_current_active_user, User

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
    from mox.infrastructure.config import settings
    
    if model.startswith("abab") or model.startswith("minimax"):
        from mox.core import MiniMaxLLM
        return MiniMaxLLM(
            model=model,
            api_key=settings.MINIMAX_API_KEY,
            group_id=settings.MINIMAX_GROUP_ID,
        )
    return LLMFactory.create_from_model_name(model)


# ============ 路由端点 ============

@router.post("/run")
async def run_benchmark(
    request: BenchmarkRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
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
            results.append({
                "result": outcome.result.value,
                "success_score": outcome.success_score,
                "iterations": outcome.iterations,
            })

        successful = sum(1 for r in results if r["result"] == "success")
        total = len(results)

        return {
            "dataset": request.dataset,
            "attack_type": request.attack_type,
            "total_cases": total,
            "successful_attacks": successful,
            "failed_attacks": total - successful,
            "attack_success_rate": successful / total if total > 0 else 0,
            "detailed_results": results,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets")
async def list_datasets() -> Dict[str, List[Dict[str, Any]]]:
    """列出可用的基准测试数据集"""
    datasets = benchmark_dataset.list_datasets()
    return {"datasets": [benchmark_dataset.get_dataset_info(name) for name in datasets]}