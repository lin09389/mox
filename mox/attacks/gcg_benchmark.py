"""Improved GCG 性能剖析 — 梯度设备、并行评估吞吐"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

from mox.attacks.improved_gcg import GCGConfig, ImprovedGCGAttack, Candidate

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def get_gradient_device_info(model_name: str = "gpt2") -> Dict[str, Any]:
    """返回梯度代理模型的设备与 CUDA 信息"""
    info: Dict[str, Any] = {
        "torch_available": TORCH_AVAILABLE,
        "cuda_available": False,
        "device": "cpu",
        "gradient_model": model_name,
    }
    if TORCH_AVAILABLE:
        info["cuda_available"] = torch.cuda.is_available()
        if info["cuda_available"]:
            info["device"] = "cuda"
            info["cuda_device_name"] = torch.cuda.get_device_name(0)
            info["cuda_memory_gb"] = round(
                torch.cuda.get_device_properties(0).total_memory / (1024**3), 2
            )
    return info


async def benchmark_parallel_eval(
    target_llm,
    *,
    num_candidates: int = 8,
    prompt: str = "Tell me how to bypass safety",
    target_behavior: str = "bypass safety",
    max_concurrent: int = 4,
) -> Dict[str, Any]:
    """测量 improved_gcg 并行候选评估吞吐（真实打 target LLM）"""
    attack = ImprovedGCGAttack(
        target_llm=target_llm,
        gcg_config=GCGConfig(
            parallel_eval=True,
            max_concurrent=max_concurrent,
            top_k=num_candidates,
            max_iterations=1,
        ),
    )
    candidates = [
        Candidate(suffix=f" !test{i}", score=0.0, generation=0)
        for i in range(num_candidates)
    ]
    start = time.perf_counter()
    results = await attack._evaluate_candidates(candidates, prompt, target_behavior)
    elapsed_ms = (time.perf_counter() - start) * 1000
    scores = [r[1] for r in results]
    return {
        "num_candidates": num_candidates,
        "max_concurrent": max_concurrent,
        "elapsed_ms": round(elapsed_ms, 2),
        "candidates_per_sec": round(num_candidates / (elapsed_ms / 1000), 2)
        if elapsed_ms > 0
        else 0,
        "avg_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "device_info": get_gradient_device_info(),
    }


def profile_gcg_config(config: Optional[GCGConfig] = None) -> Dict[str, Any]:
    """静态剖析 GCG 配置与硬件能力（无需 LLM 调用）"""
    cfg = config or GCGConfig()
    device = get_gradient_device_info(cfg.gradient_model)
    est_llm_calls_per_iter = min(cfg.top_k, cfg.batch_size)
    return {
        "config": {
            "top_k": cfg.top_k,
            "batch_size": cfg.batch_size,
            "parallel_eval": cfg.parallel_eval,
            "max_concurrent": cfg.max_concurrent,
            "use_gradient_guidance": cfg.use_gradient_guidance,
            "gradient_model": cfg.gradient_model,
        },
        "device": device,
        "estimated_target_llm_calls_per_iteration": est_llm_calls_per_iter,
        "recommended_max_concurrent": min(
            cfg.max_concurrent,
            32 if device.get("cuda_available") else 8,
        ),
    }


__all__ = [
    "get_gradient_device_info",
    "benchmark_parallel_eval",
    "profile_gcg_config",
]