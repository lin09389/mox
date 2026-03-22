"""
攻击链和组合模块

提供组合多个攻击的能力：
1. AttackChain - 顺序执行多个攻击
2. AttackEnsemble - 并行执行多个攻击 + 结果聚合
3. TargetModel - 目标模型抽象
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import asyncio

from mox.core import BaseLLM, AttackPayload, AttackOutcome, AttackResult
from mox.attacks.base import BaseAttack


@dataclass
class AttackChainResult:
    """攻击链结果"""
    chain_name: str
    results: List[AttackOutcome]
    overall_success: bool
    total_iterations: int
    execution_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class AttackChain:
    """攻击链 - 顺序执行多个攻击

    示例:
        chain = AttackChain("my_chain")
        chain.add_attack(prompt_injection_attack)
        chain.add_attack(jailbreak_attack)
        result = await chain.execute(payload)
    """

    def __init__(
        self,
        name: str,
        stop_on_success: bool = True,
    ):
        self.name = name
        self.attacks: List[BaseAttack] = []
        self.stop_on_success = stop_on_success

    def add_attack(self, attack: BaseAttack) -> "AttackChain":
        """添加攻击到链中（支持链式调用）"""
        self.attacks.append(attack)
        return self

    async def execute(self, payload: AttackPayload) -> AttackChainResult:
        """执行攻击链"""
        import time
        start_time = time.time()

        results = []
        for i, attack in enumerate(self.attacks):
            outcome = await attack.generate_attack(payload)

            # 克隆 outcome 以修改
            outcome_dict = {
                "result": outcome.result,
                "original_prompt": outcome.original_prompt,
                "adversarial_prompt": outcome.adversarial_prompt,
                "model_response": outcome.model_response,
                "iterations": outcome.iterations,
                "success_score": outcome.success_score,
                "metadata": {
                    **outcome.metadata,
                    "attack_index": i,
                    "attack_name": attack.__class__.__name__,
                },
            }
            results.append(outcome_dict)

            # 如果成功且设置了 stop_on_success，则停止
            if self.stop_on_success and outcome.result == AttackResult.SUCCESS:
                break

        total_iterations = sum(r["iterations"] for r in results)
        overall_success = any(r["result"] == AttackResult.SUCCESS for r in results)
        execution_time_ms = (time.time() - start_time) * 1000

        return AttackChainResult(
            chain_name=self.name,
            results=[self._dict_to_outcome(r) for r in results],
            overall_success=overall_success,
            total_iterations=total_iterations,
            execution_time_ms=execution_time_ms,
        )

    def _dict_to_outcome(self, d: Dict[str, Any]) -> AttackOutcome:
        """将字典转换回 AttackOutcome"""
        return AttackOutcome(
            result=d["result"],
            original_prompt=d["original_prompt"],
            adversarial_prompt=d["adversarial_prompt"],
            model_response=d["model_response"],
            iterations=d["iterations"],
            success_score=d["success_score"],
            metadata=d["metadata"],
        )


@dataclass
class EnsembleResult:
    """集成攻击结果"""
    ensemble_name: str
    results: List[AttackOutcome]
    successful_attacks: List[AttackOutcome]
    best_result: Optional[AttackOutcome]
    aggregated_score: float
    execution_time_ms: float


class AttackEnsemble:
    """攻击集成 - 并行执行多个攻击并聚合结果

    示例:
        ensemble = AttackEnsemble("my_ensemble")
        ensemble.add_attack(prompt_injection_attack)
        ensemble.add_attack(jailbreak_attack)
        ensemble.add_attack(gcg_attack)
        result = await ensemble.execute(payload)
    """

    def __init__(self, name: str, max_concurrency: int = 3):
        self.name = name
        self.attacks: List[BaseAttack] = []
        self.max_concurrency = max_concurrency

    def add_attack(self, attack: BaseAttack) -> "AttackEnsemble":
        """添加攻击到集成（支持链式调用）"""
        self.attacks.append(attack)
        return self

    async def execute(self, payload: AttackPayload) -> EnsembleResult:
        """并行执行攻击集成"""
        import time
        start_time = time.time()

        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def run_with_semaphore(attack: BaseAttack) -> AttackOutcome:
            async with semaphore:
                return await attack.generate_attack(payload)

        # 并行执行所有攻击
        tasks = [run_with_semaphore(attack) for attack in self.attacks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        outcomes = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 创建错误结果
                outcomes.append(AttackOutcome(
                    result=AttackResult.ERROR,
                    original_prompt=payload.prompt,
                    adversarial_prompt="",
                    model_response=str(result),
                    iterations=0,
                    success_score=0.0,
                    metadata={
                        "error": str(result),
                        "attack_name": self.attacks[i].__class__.__name__,
                    },
                ))
            else:
                outcomes.append(result)

        successful_attacks = [
            o for o in outcomes if o.result == AttackResult.SUCCESS
        ]

        # 选择最佳结果（分数最高的成功攻击）
        best_result = None
        if successful_attacks:
            best_result = max(successful_attacks, key=lambda x: x.success_score)

        # 计算聚合分数
        aggregated_score = self._aggregate_scores(outcomes)
        execution_time_ms = (time.time() - start_time) * 1000

        return EnsembleResult(
            ensemble_name=self.name,
            results=outcomes,
            successful_attacks=successful_attacks,
            best_result=best_result,
            aggregated_score=aggregated_score,
            execution_time_ms=execution_time_ms,
        )

    def _aggregate_scores(self, results: List[AttackOutcome]) -> float:
        """聚合多个攻击的分数"""
        if not results:
            return 0.0

        scores = [r.success_score for r in results]
        return sum(scores) / len(scores)


class TargetModel(ABC):
    """目标模型抽象

    支持不同类型的目标：
    - 标准 LLM
    - 多模态模型
    - RAG 系统
    - Agent 系统
    """

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """生成响应"""
        pass

    @abstractmethod
    async def batch_generate(self, prompts: List[str]) -> List[str]:
        """批量生成"""
        pass


class LLMTargetModel(TargetModel):
    """标准 LLM 目标"""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    async def generate(self, prompt: str) -> str:
        from mox.core import Message
        messages = [Message(role="user", content=prompt)]
        response = await self.llm.generate(messages)
        return response.content

    async def batch_generate(self, prompts: List[str]) -> List[str]:
        from mox.core import Message
        tasks = []
        for prompt in prompts:
            messages = [Message(role="user", content=prompt)]
            tasks.append(self.llm.generate(messages))

        results = await asyncio.gather(*tasks)
        return [r.content for r in results]


class RAGTargetModel(TargetModel):
    """RAG 系统目标"""

    def __init__(self, llm: BaseLLM, retriever=None):
        self.llm = llm
        self.retriever = retriever

    async def generate(self, prompt: str) -> str:
        # 如果有 retriever，先检索相关上下文
        context = ""
        if self.retriever:
            docs = await self.retriever.retrieve(prompt)
            context = "\n".join(docs)

        full_prompt = f"Context: {context}\n\nQuestion: {prompt}"
        return await self._generate_with_llm(full_prompt)

    async def batch_generate(self, prompts: List[str]) -> List[str]:
        tasks = [self.generate(p) for p in prompts]
        return await asyncio.gather(*tasks)

    async def _generate_with_llm(self, prompt: str) -> str:
        from mox.core import Message
        messages = [Message(role="user", content=prompt)]
        response = await self.llm.generate(messages)
        return response.content


class MultimodalTargetModel(TargetModel):
    """多模态目标"""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    async def generate(self, prompt: str) -> str:
        # 处理多模态输入（简化版本）
        from mox.core import Message
        messages = [Message(role="user", content=prompt)]
        response = await self.llm.generate(messages)
        return response.content

    async def batch_generate(self, prompts: List[str]) -> List[str]:
        tasks = [self.generate(p) for p in prompts]
        return await asyncio.gather(*tasks)

    async def generate_with_image(self, prompt: str, image_data: bytes) -> str:
        """带图像的生成"""
        # 实际实现需要根据具体的多模态 API
        return await self.generate(prompt)
