"""梯度优化攻击模块 - 基于梯度的对抗性攻击

实现多种基于梯度优化的攻击方法:
1. FGSM (Fast Gradient Sign Method) - 快速梯度符号方法
2. PGD (Projected Gradient Descent) - 投影梯度下降
3. 基于优化的对抗后缀攻击

核心原理:
- 攻击在连续嵌入空间中进行梯度计算和扰动
- 扰动后的嵌入向量通过最近邻搜索映射回离散token
- 在不可用torch时降级为基于词汇表替换的方法

基于论文:
- "Explaining and Harnessing Adversarial Examples" (FGSM)
- "Towards Deep Learning Models Resistant to Adversarial Attacks" (PGD)
- "Universal and Transferable Adversarial Attacks on Aligned Language Models" (GCG)
"""

import re
import string
import random
import warnings
from typing import Optional, List, Tuple
from dataclasses import dataclass

from mox.core import BaseLLM, Message, AttackType, AttackPayload, AttackOutcome, AttackResult
from .base import BaseAttack, AttackConfig
from mox.infrastructure.logging import get_logger

logger = get_logger("gradient_attack")

try:
    import torch
    import torch.nn.functional as F
    from transformers import AutoModelForCausalLM, AutoTokenizer

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@dataclass
class GradientAttackConfig:
    """梯度攻击配置"""

    max_iterations: int = 100
    batch_size: int = 32
    epsilon: float = 0.25
    step_size: float = 0.01
    num_restarts: int = 5
    target_model: str = "gpt2"
    use_targeted: bool = False
    early_stop_threshold: float = 0.9
    verbose: bool = True
    num_steps: int = 40
    random_restarts: int = 5
    suffix_length: int = 20


class GradientBasedAttack(BaseAttack):
    """基于梯度的攻击基类 (白盒攻击)

    WARNING: These attacks require white-box access to the target model's
    gradients. They work by computing gradients in the continuous embedding
    space and projecting perturbations back to discrete tokens.

    On black-box targets (GPT-4, Claude, etc.), the attack loads a local
    proxy model (default: GPT-2) for gradient computation. Transferability
    from GPT-2 to modern LLMs is limited, so effectiveness will be lower.

    When torch/transformers are not available, the attack falls back to
    random token substitution (not gradient-guided).
    """

    def __init__(
        self,
        target_llm: BaseLLM,
        config: Optional[AttackConfig] = None,
        gradient_config: Optional[GradientAttackConfig] = None,
    ):
        super().__init__(target_llm, config)
        self.gradient_config = gradient_config or GradientAttackConfig()
        self._victim_model = None
        self._tokenizer = None

    async def evaluate_success(
        self,
        response: str,
        target_behavior: str,
    ) -> float:
        from mox.core.evaluation import is_target_in_response_with_refusal_check

        return is_target_in_response_with_refusal_check(response, target_behavior)

    def _init_victim_model(self):
        """初始化受害模型用于梯度计算"""
        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch and transformers are required for gradient-based attacks in "
                "embedding space. Install with: pip install torch transformers"
            )

        if self._victim_model is None:
            try:
                self._victim_model = AutoModelForCausalLM.from_pretrained(
                    self.gradient_config.target_model,
                    revision="main",
                    torch_dtype=torch.float32,
                    device_map="cpu",
                )
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.gradient_config.target_model,
                    revision="main",
                )
                if self._tokenizer.pad_token is None:
                    self._tokenizer.pad_token = self._tokenizer.eos_token
            except Exception as e:
                self._victim_model = None
                self._tokenizer = None
                raise ImportError(
                    f"Failed to load victim model '{self.gradient_config.target_model}': {e}. "
                    f"Ensure the model name is valid and accessible."
                ) from e

    def _embed_and_perturb(
        self,
        input_ids: "torch.Tensor",
        epsilon: float,
        targeted: bool = False,
        target_ids: Optional["torch.Tensor"] = None,
    ) -> "torch.Tensor":
        """在连续嵌入空间中计算梯度并施加扰动

        Args:
            input_ids: 输入token IDs, shape [1, seq_len]
            epsilon: 扰动幅度
            targeted: 是否为目标攻击
            target_ids: 目标token IDs

        Returns:
            扰动后的连续嵌入向量, shape [1, seq_len, embed_dim]
        """
        if self._victim_model is None:
            self._init_victim_model()

        embedding_layer = self._victim_model.get_input_embeddings()
        embed_weights = embedding_layer.weight.data

        continuous_embeds = embedding_layer(input_ids).detach().clone()
        continuous_embeds.requires_grad_(True)

        outputs = self._victim_model(
            inputs_embeds=continuous_embeds,
            attention_mask=torch.ones_like(input_ids),
        )
        logits = outputs.logits

        if targeted and target_ids is not None:
            loss = -F.cross_entropy(logits[:, -1, :], target_ids[:, 0])
        else:
            if target_ids is not None:
                loss = F.cross_entropy(logits[:, -1, :], target_ids[:, 0])
            else:
                loss = logits[:, -1, :].max()

        if continuous_embeds.grad is not None:
            continuous_embeds.grad.zero_()
        loss.backward()

        grad_sign = continuous_embeds.grad.sign()
        perturbed_embeds = continuous_embeds.detach() + epsilon * grad_sign

        return perturbed_embeds

    def _project_to_nearest_tokens(self, perturbed_embeds: "torch.Tensor") -> "torch.Tensor":
        """将扰动后的嵌入向量映射回最近的token IDs

        通过计算扰动嵌入与词嵌入矩阵之间的余弦相似度，
        找到最接近的token作为离散化结果。

        Args:
            perturbed_embeds: 扰动后嵌入, shape [1, seq_len, embed_dim]

        Returns:
            最近token IDs, shape [1, seq_len]
        """
        if self._victim_model is None:
            self._init_victim_model()

        embedding_layer = self._victim_model.get_input_embeddings()
        embed_weights = embedding_layer.weight.data

        embed_norms = embed_weights.norm(dim=1, keepdim=True).clamp(min=1e-8)
        normalized_weights = embed_weights / embed_norms

        perturbed_flat = perturbed_embeds.view(-1, perturbed_embeds.size(-1))
        pert_norms = perturbed_flat.norm(dim=1, keepdim=True).clamp(min=1e-8)
        normalized_perturbed = perturbed_flat / pert_norms

        similarities = torch.mm(normalized_perturbed, normalized_weights.t())
        nearest_ids = similarities.argmax(dim=1)
        nearest_ids = nearest_ids.view(perturbed_embeds.size(0), perturbed_embeds.size(1))

        return nearest_ids

    def _pgd_perturb_in_embed_space(
        self,
        input_ids: "torch.Tensor",
        epsilon: float,
        step_size: float,
        num_steps: int,
        targeted: bool = False,
        target_ids: Optional["torch.Tensor"] = None,
    ) -> "torch.Tensor":
        """在嵌入空间中执行多步PGD扰动

        Args:
            input_ids: 原始输入token IDs
            epsilon: 最大扰动范围
            step_size: 每步步长
            num_steps: 迭代步数
            targeted: 是否为目标攻击
            target_ids: 目标token IDs

        Returns:
            扰动后映射回的最近token IDs
        """
        if self._victim_model is None:
            self._init_victim_model()

        embedding_layer = self._victim_model.get_input_embeddings()

        original_embeds = embedding_layer(input_ids).detach().clone()
        perturbed_embeds = original_embeds.clone()

        for _ in range(num_steps):
            perturbed_embeds.requires_grad_(True)

            outputs = self._victim_model(
                inputs_embeds=perturbed_embeds,
                attention_mask=torch.ones_like(input_ids),
            )
            logits = outputs.logits

            if targeted and target_ids is not None:
                loss = -F.cross_entropy(logits[:, -1, :], target_ids[:, 0])
            else:
                if target_ids is not None:
                    loss = F.cross_entropy(logits[:, -1, :], target_ids[:, 0])
                else:
                    loss = logits[:, -1, :].max()

            loss.backward()

            grad_sign = perturbed_embeds.grad.sign()
            with torch.no_grad():
                perturbed_embeds = perturbed_embeds.detach() + step_size * grad_sign

                delta = perturbed_embeds - original_embeds
                delta = torch.clamp(delta, -epsilon, epsilon)
                perturbed_embeds = original_embeds + delta

        nearest_ids = self._project_to_nearest_tokens(perturbed_embeds)
        return nearest_ids

    def _fallback_token_substitution(
        self,
        text: str,
        target_text: str,
    ) -> str:
        """无torch时的降级方法：基于词汇表的token替换

        通过逐步替换文本中的token，在目标模型的词汇表中
        寻找可能导致不同输出的替代token。

        Args:
            text: 原始文本
            target_text: 目标行为文本

        Returns:
            替换后的文本
        """
        if self._tokenizer is not None:
            tokens = self._tokenizer.encode(text, add_special_tokens=False)
            vocab_size = self._tokenizer.vocab_size
            num_positions = max(1, len(tokens) // 4)

            positions = random.sample(range(len(tokens)), min(num_positions, len(tokens)))
            for pos in positions:
                original_token_id = tokens[pos]
                step = random.randint(1, max(1, vocab_size // 100))
                new_token_id = min(original_token_id + step, vocab_size - 1)
                tokens[pos] = new_token_id

            return self._tokenizer.decode(tokens)

        words = text.split()
        num_positions = max(1, len(words) // 4)
        positions = random.sample(range(len(words)), min(num_positions, len(words)))
        mutable_chars = string.ascii_letters + string.digits

        for pos in positions:
            word = words[pos]
            if word and word.isalpha():
                char_pos = random.randint(0, len(word) - 1)
                words[pos] = word[:char_pos] + random.choice(mutable_chars) + word[char_pos + 1 :]

        return " ".join(words)

    def _generate_random_suffix(self, length: int) -> str:
        """生成随机后缀"""
        chars = string.ascii_letters + string.digits + " "
        return "".join(random.choices(chars, k=length))


class FGSMAttack(GradientBasedAttack):
    """FGSM (Fast Gradient Sign Method) 攻击

    在嵌入空间中执行单步梯度符号扰动，然后映射回最近的token。
    无torch时降级为token替换方法。
    """

    attack_type = AttackType.FGSM

    def __init__(
        self,
        target_llm: BaseLLM,
        config: Optional[AttackConfig] = None,
        gradient_config: Optional[GradientAttackConfig] = None,
    ):
        super().__init__(target_llm, config, gradient_config)

    async def generate_attack(
        self,
        payload: AttackPayload,
    ) -> AttackOutcome:
        """执行FGSM攻击"""

        best_suffix = ""
        best_score = 0.0
        best_response = ""
        best_adversarial_prompt = ""

        if not TORCH_AVAILABLE:
            warnings.warn(
                "PyTorch not available. FGSMAttack will use token substitution fallback, "
                "which is less effective than embedding-space gradient attacks.",
                UserWarning,
                stacklevel=2,
            )
            return await self._generate_attack_fallback(payload)

        try:
            self._init_victim_model()
        except ImportError as e:
            warnings.warn(
                f"Could not initialize victim model: {e}. Falling back to token substitution.",
                UserWarning,
                stacklevel=2,
            )
            return await self._generate_attack_fallback(payload)

        base_text = payload.prompt
        target_text = payload.target_behavior

        try:
            base_inputs = self._tokenizer(base_text, return_tensors="pt")
            base_input_ids = base_inputs["input_ids"]
            target_inputs = self._tokenizer(target_text, return_tensors="pt")
            target_input_ids = target_inputs["input_ids"]

            for restart in range(self.gradient_config.num_restarts):
                current_suffix = self._generate_random_suffix(self.gradient_config.suffix_length)
                adversarial_prompt = f"{base_text} {current_suffix}"

                adv_inputs = self._tokenizer(adversarial_prompt, return_tensors="pt")
                adv_input_ids = adv_inputs["input_ids"]

                self._victim_model.zero_grad()
                perturbed_embeds = self._embed_and_perturb(
                    adv_input_ids,
                    epsilon=self.gradient_config.epsilon,
                    targeted=self.gradient_config.use_targeted,
                    target_ids=target_input_ids,
                )

                nearest_ids = self._project_to_nearest_tokens(perturbed_embeds)
                new_prompt = self._tokenizer.decode(nearest_ids[0], skip_special_tokens=True)

                messages = [Message(role="user", content=new_prompt)]
                response = await self.target_llm.generate(messages)

                score = await self.evaluate_success(response.content, target_text)

                if score > best_score:
                    best_score = score
                    best_suffix = current_suffix
                    best_response = response.content
                    best_adversarial_prompt = new_prompt

                    if score >= self.gradient_config.early_stop_threshold:
                        return await self._create_outcome(
                            result=AttackResult.SUCCESS,
                            original_prompt=payload.prompt,
                            adversarial_prompt=new_prompt,
                            model_response=response.content,
                            iterations=restart + 1,
                            success_score=score,
                            metadata={
                                "method": "fgsm_embedding",
                                "epsilon": self.gradient_config.epsilon,
                            },
                        )

        except Exception as e:
            logger.error(f"FGSM embedding-space attack failed: {e}")
            return await self._create_outcome(
                result=AttackResult.ERROR,
                original_prompt=payload.prompt,
                adversarial_prompt="",
                model_response=str(e),
                iterations=0,
                success_score=0.0,
                metadata={"method": "fgsm_embedding", "error": str(e)},
            )

        result = (
            AttackResult.SUCCESS
            if best_score >= self.config.success_threshold
            else AttackResult.FAILURE
        )

        adversarial_prompt = best_adversarial_prompt or f"{payload.prompt} {best_suffix}"
        return await self._create_outcome(
            result=result,
            original_prompt=payload.prompt,
            adversarial_prompt=adversarial_prompt,
            model_response=best_response,
            iterations=self.gradient_config.num_restarts,
            success_score=best_score,
            metadata={"method": "fgsm_embedding", "epsilon": self.gradient_config.epsilon},
        )

    async def _generate_attack_fallback(
        self,
        payload: AttackPayload,
    ) -> AttackOutcome:
        """torch不可用时的降级方法：基于token替换"""

        best_suffix = ""
        best_score = 0.0
        best_response = ""
        target_text = payload.target_behavior

        for restart in range(self.gradient_config.num_restarts):
            current_suffix = self._generate_random_suffix(self.gradient_config.suffix_length)
            adversarial_prompt = f"{payload.prompt} {current_suffix}"

            perturbed_prompt = self._fallback_token_substitution(adversarial_prompt, target_text)

            messages = [Message(role="user", content=perturbed_prompt)]
            try:
                response = await self.target_llm.generate(messages)
                score = await self.evaluate_success(response.content, target_text)

                if score > best_score:
                    best_score = score
                    best_suffix = current_suffix
                    best_response = response.content

                    if score >= self.gradient_config.early_stop_threshold:
                        break
            except Exception as e:
                logger.debug(f"FGSM fallback attempt {restart} failed: {e}")
                continue

        result = (
            AttackResult.SUCCESS
            if best_score >= self.config.success_threshold
            else AttackResult.FAILURE
        )

        return await self._create_outcome(
            result=result,
            original_prompt=payload.prompt,
            adversarial_prompt=f"{payload.prompt} {best_suffix}",
            model_response=best_response,
            iterations=self.gradient_config.num_restarts,
            success_score=best_score,
            metadata={"method": "fgsm_token_substitution", "fallback": True},
        )


class PGDAttack(GradientBasedAttack):
    """PGD (Projected Gradient Descent) 攻击

    在嵌入空间中执行多步迭代投影梯度下降，
    每步扰动后投影到epsilon球内，最后映射回最近的token。
    无torch时降级为token替换方法。
    """

    attack_type = AttackType.PGD

    def __init__(
        self,
        target_llm: BaseLLM,
        config: Optional[AttackConfig] = None,
        gradient_config: Optional[GradientAttackConfig] = None,
    ):
        super().__init__(target_llm, config, gradient_config)

    async def generate_attack(
        self,
        payload: AttackPayload,
    ) -> AttackOutcome:

        best_suffix = ""
        best_score = 0.0
        best_response = ""
        best_adversarial_prompt = ""

        if not TORCH_AVAILABLE:
            warnings.warn(
                "PyTorch not available. PGDAttack will use token substitution fallback, "
                "which is less effective than embedding-space gradient attacks.",
                UserWarning,
                stacklevel=2,
            )
            return await self._generate_attack_fallback(payload)

        try:
            self._init_victim_model()
        except ImportError as e:
            warnings.warn(
                f"Could not initialize victim model: {e}. Falling back to token substitution.",
                UserWarning,
                stacklevel=2,
            )
            return await self._generate_attack_fallback(payload)

        base_text = payload.prompt
        target_text = payload.target_behavior

        try:
            target_inputs = self._tokenizer(target_text, return_tensors="pt")
            target_input_ids = target_inputs["input_ids"]

            for restart in range(self.gradient_config.random_restarts):
                current_suffix = self._generate_random_suffix(self.gradient_config.suffix_length)

                adversarial_prompt = f"{base_text} {current_suffix}"
                adv_inputs = self._tokenizer(adversarial_prompt, return_tensors="pt")
                adv_input_ids = adv_inputs["input_ids"]

                self._victim_model.zero_grad()

                nearest_ids = self._pgd_perturb_in_embed_space(
                    adv_input_ids,
                    epsilon=self.gradient_config.epsilon,
                    step_size=self.gradient_config.step_size,
                    num_steps=self.gradient_config.num_steps,
                    targeted=self.gradient_config.use_targeted,
                    target_ids=target_input_ids,
                )

                current_suffix = self._tokenizer.decode(nearest_ids[0], skip_special_tokens=True)
                if len(current_suffix) > len(base_text):
                    current_suffix = current_suffix[len(base_text) :].strip()

                adversarial_prompt = f"{base_text} {current_suffix}"

                messages = [Message(role="user", content=adversarial_prompt)]
                response = await self.target_llm.generate(messages)

                score = await self.evaluate_success(response.content, target_text)

                if score > best_score:
                    best_score = score
                    best_suffix = current_suffix
                    best_response = response.content
                    best_adversarial_prompt = adversarial_prompt

                    if score >= self.gradient_config.early_stop_threshold:
                        return await self._create_outcome(
                            result=AttackResult.SUCCESS,
                            original_prompt=payload.prompt,
                            adversarial_prompt=adversarial_prompt,
                            model_response=response.content,
                            iterations=(restart + 1) * self.gradient_config.num_steps,
                            success_score=score,
                            metadata={
                                "method": "pgd_embedding",
                                "epsilon": self.gradient_config.epsilon,
                                "num_steps": self.gradient_config.num_steps,
                            },
                        )

        except Exception as e:
            logger.error(f"PGD embedding-space attack failed: {e}")
            return await self._create_outcome(
                result=AttackResult.ERROR,
                original_prompt=payload.prompt,
                adversarial_prompt="",
                model_response=str(e),
                iterations=0,
                success_score=0.0,
                metadata={"method": "pgd_embedding", "error": str(e)},
            )

        result = (
            AttackResult.SUCCESS
            if best_score >= self.config.success_threshold
            else AttackResult.FAILURE
        )

        adversarial_prompt = best_adversarial_prompt or f"{payload.prompt} {best_suffix}"
        return await self._create_outcome(
            result=result,
            original_prompt=payload.prompt,
            adversarial_prompt=adversarial_prompt,
            model_response=best_response,
            iterations=self.gradient_config.num_steps * self.gradient_config.random_restarts,
            success_score=best_score,
            metadata={"method": "pgd_embedding", "epsilon": self.gradient_config.epsilon},
        )

    async def _generate_attack_fallback(
        self,
        payload: AttackPayload,
    ) -> AttackOutcome:
        """torch不可用时的降级方法：迭代token替换"""

        best_suffix = ""
        best_score = 0.0
        best_response = ""
        target_text = payload.target_behavior

        for restart in range(self.gradient_config.random_restarts):
            current_suffix = self._generate_random_suffix(self.gradient_config.suffix_length)

            for step in range(min(self.gradient_config.num_steps, 10)):
                adversarial_prompt = f"{payload.prompt} {current_suffix}"
                perturbed_prompt = self._fallback_token_substitution(
                    adversarial_prompt, target_text
                )

                messages = [Message(role="user", content=perturbed_prompt)]
                try:
                    response = await self.target_llm.generate(messages)
                    score = await self.evaluate_success(response.content, target_text)

                    if score > best_score:
                        best_score = score
                        best_suffix = current_suffix
                        best_response = response.content

                        if score >= self.gradient_config.early_stop_threshold:
                            break
                except Exception as e:
                    logger.debug(f"PGD fallback step {step} failed: {e}")
                    continue

            if best_score >= self.gradient_config.early_stop_threshold:
                break

        result = (
            AttackResult.SUCCESS
            if best_score >= self.config.success_threshold
            else AttackResult.FAILURE
        )

        return await self._create_outcome(
            result=result,
            original_prompt=payload.prompt,
            adversarial_prompt=f"{payload.prompt} {best_suffix}",
            model_response=best_response,
            iterations=self.gradient_config.num_steps * self.gradient_config.random_restarts,
            success_score=best_score,
            metadata={"method": "pgd_token_substitution", "fallback": True},
        )


class AdversarialSuffixAttack(GradientBasedAttack):
    """对抗后缀攻击 - 类似于GCG但使用梯度优化

    在嵌入空间中利用梯度信息优化对抗后缀token，
    通过token级搜索在词汇表中找到最优替代。
    无torch时降级为纯随机搜索方法。
    """

    attack_type = AttackType.ADVERSARIAL_SUFFIX

    def __init__(
        self,
        target_llm: BaseLLM,
        config: Optional[AttackConfig] = None,
        gradient_config: Optional[GradientAttackConfig] = None,
    ):
        super().__init__(target_llm, config, gradient_config)
        self.candidate_tokens = self._init_candidate_tokens()

    def _init_candidate_tokens(self) -> List[str]:
        """初始化候选token列表

        当torch可用时会使用tokenizer的词汇表，
        否则使用可打印字符集。
        """
        if TORCH_AVAILABLE and self._tokenizer is not None:
            vocab = self._tokenizer.get_vocab()
            printable_tokens = []
            for token_str, token_id in vocab.items():
                decoded = self._tokenizer.decode([token_id]).strip()
                if decoded and all(c.isprintable() or c == " " for c in decoded):
                    printable_tokens.append(decoded)
            if printable_tokens:
                return printable_tokens

        printable = string.printable.replace("\n", "").replace("\r", "").replace("\t", "")
        tokens = [c for c in printable if c.isprintable()]
        tokens.extend([" ", "  ", "   "])
        return tokens

    async def generate_attack(
        self,
        payload: AttackPayload,
    ) -> AttackOutcome:

        best_suffix = ""
        best_score = 0.0
        best_response = ""

        if not TORCH_AVAILABLE:
            warnings.warn(
                "PyTorch not available. AdversarialSuffixAttack will use random search "
                "fallback, which is less effective than gradient-guided token optimization.",
                UserWarning,
                stacklevel=2,
            )
            return await self._generate_attack_fallback(payload)

        try:
            self._init_victim_model()
        except ImportError as e:
            warnings.warn(
                f"Could not initialize victim model: {e}. Falling back to random search.",
                UserWarning,
                stacklevel=2,
            )
            return await self._generate_attack_fallback(payload)

        self.candidate_tokens = self._init_candidate_tokens()

        initial_suffix = self._generate_initial_suffix(self.gradient_config.suffix_length)

        best_suffix = initial_suffix

        base_text = payload.prompt
        target_text = payload.target_behavior

        try:
            target_inputs = self._tokenizer(target_text, return_tensors="pt")
            target_input_ids = target_inputs["input_ids"]

            for iteration in range(self.gradient_config.max_iterations):
                suffix_token_ids = self._tokenizer.encode(initial_suffix, add_special_tokens=False)
                if not suffix_token_ids:
                    initial_suffix = self._generate_initial_suffix(
                        self.gradient_config.suffix_length
                    )
                    continue

                suffix_ids_tensor = torch.tensor([suffix_token_ids], dtype=torch.long)

                self._victim_model.zero_grad()
                suffix_embeds = (
                    self._victim_model.get_input_embeddings()(suffix_ids_tensor).detach().clone()
                )
                suffix_embeds.requires_grad_(True)

                base_ids = self._tokenizer.encode(base_text, add_special_tokens=False)
                full_ids = base_ids + suffix_token_ids
                full_ids_tensor = torch.tensor([full_ids], dtype=torch.long)

                base_embeds = (
                    self._victim_model.get_input_embeddings()(full_ids_tensor).detach().clone()
                )
                base_len = len(base_ids)
                base_embeds[0, :base_len, :] = base_embeds[0, :base_len, :].detach()
                base_embeds[0, base_len:, :] = suffix_embeds[0, :, :]

                outputs = self._victim_model(
                    inputs_embeds=base_embeds,
                    attention_mask=torch.ones_like(full_ids_tensor),
                )
                logits = outputs.logits

                if target_input_ids.size(1) > 0:
                    loss = F.cross_entropy(logits[:, -1, :], target_input_ids[:, 0])
                else:
                    loss = logits[:, -1, :].max()

                loss.backward()

                if suffix_embeds.grad is not None:
                    grad_magnitudes = suffix_embeds.grad.norm(dim=-1).squeeze(0)
                    num_replace = max(1, len(suffix_token_ids) // 2)
                    _, top_positions = torch.topk(
                        grad_magnitudes, k=min(num_replace, len(suffix_token_ids))
                    )

                    embedding_layer = self._victim_model.get_input_embeddings()
                    embed_weights = embedding_layer.weight.data
                    embed_norms = embed_weights.norm(dim=1, keepdim=True).clamp(min=1e-8)
                    normalized_weights = embed_weights / embed_norms

                    for pos_idx in top_positions:
                        pos = pos_idx.item()
                        if pos >= len(suffix_token_ids):
                            continue

                        token_grad = suffix_embeds.grad[0, pos, :]
                        perturbed_embed = (
                            suffix_embeds[0, pos, :].detach()
                            + self.gradient_config.epsilon * token_grad.sign()
                        )

                        perturbed_norm = perturbed_embed.norm().clamp(min=1e-8)
                        normalized_perturbed = perturbed_embed / perturbed_norm

                        similarities = torch.mm(
                            normalized_perturbed.unsqueeze(0), normalized_weights.t()
                        )
                        best_token_id = similarities.argmax(dim=1).item()

                        suffix_token_ids[pos] = best_token_id

                    initial_suffix = self._tokenizer.decode(
                        suffix_token_ids, skip_special_tokens=True
                    )

                candidates = self._generate_candidates(initial_suffix)

                for candidate in candidates[: self.gradient_config.batch_size]:
                    adversarial_prompt = f"{base_text} {candidate}"

                    try:
                        response = await self.target_llm.generate(
                            [Message(role="user", content=adversarial_prompt)]
                        )
                        score = await self.evaluate_success(response.content, target_text)

                        if score > best_score:
                            best_score = score
                            best_suffix = candidate
                            best_response = response.content

                            if score >= self.gradient_config.early_stop_threshold:
                                return await self._create_outcome(
                                    result=AttackResult.SUCCESS,
                                    original_prompt=payload.prompt,
                                    adversarial_prompt=adversarial_prompt,
                                    model_response=response.content,
                                    iterations=iteration + 1,
                                    success_score=score,
                                    metadata={"method": "adversarial_suffix_embedding"},
                                )
                    except Exception as e:
                        logger.debug(f"LLM evaluation failed for candidate: {e}")
                        continue

                if self.gradient_config.verbose and iteration % 10 == 0:
                    print(f"Iteration {iteration}: Best score = {best_score:.4f}")

        except Exception as e:
            logger.error(f"Adversarial suffix embedding attack failed: {e}")
            return await self._create_outcome(
                result=AttackResult.ERROR,
                original_prompt=payload.prompt,
                adversarial_prompt="",
                model_response=str(e),
                iterations=0,
                success_score=0.0,
                metadata={"method": "adversarial_suffix_embedding", "error": str(e)},
            )

        result = (
            AttackResult.SUCCESS
            if best_score >= self.config.success_threshold
            else AttackResult.FAILURE
        )

        return await self._create_outcome(
            result=result,
            original_prompt=payload.prompt,
            adversarial_prompt=f"{payload.prompt} {best_suffix}",
            model_response=best_response,
            iterations=self.gradient_config.max_iterations,
            success_score=best_score,
            metadata={"method": "adversarial_suffix_embedding"},
        )

    async def _generate_attack_fallback(
        self,
        payload: AttackPayload,
    ) -> AttackOutcome:
        """torch不可用时的降级方法：纯随机搜索"""

        best_suffix = ""
        best_score = 0.0
        best_response = ""
        target_text = payload.target_behavior

        initial_suffix = self._generate_initial_suffix(self.gradient_config.suffix_length)

        for iteration in range(self.gradient_config.max_iterations):
            candidates = self._generate_candidates(initial_suffix)

            for candidate in candidates[: self.gradient_config.batch_size]:
                adversarial_prompt = f"{payload.prompt} {candidate}"

                try:
                    response = await self.target_llm.generate(
                        [Message(role="user", content=adversarial_prompt)]
                    )
                    score = await self.evaluate_success(response.content, target_text)

                    if score > best_score:
                        best_score = score
                        best_suffix = candidate
                        best_response = response.content
                        initial_suffix = candidate

                        if score >= self.gradient_config.early_stop_threshold:
                            return await self._create_outcome(
                                result=AttackResult.SUCCESS,
                                original_prompt=payload.prompt,
                                adversarial_prompt=adversarial_prompt,
                                model_response=response.content,
                                iterations=iteration + 1,
                                success_score=score,
                                metadata={
                                    "method": "adversarial_suffix_random",
                                    "fallback": True,
                                },
                            )
                except Exception as e:
                    logger.debug(f"Random search evaluation failed: {e}")
                    continue

            if self.gradient_config.verbose and iteration % 10 == 0:
                print(f"Iteration {iteration}: Best score = {best_score:.4f}")

        result = (
            AttackResult.SUCCESS
            if best_score >= self.config.success_threshold
            else AttackResult.FAILURE
        )

        return await self._create_outcome(
            result=result,
            original_prompt=payload.prompt,
            adversarial_prompt=f"{payload.prompt} {best_suffix}",
            model_response=best_response,
            iterations=self.gradient_config.max_iterations,
            success_score=best_score,
            metadata={"method": "adversarial_suffix_random", "fallback": True},
        )

    def _generate_initial_suffix(self, length: int = 20) -> str:
        return "".join(random.choices(self.candidate_tokens, k=length))

    def _generate_candidates(self, current_suffix: str) -> List[str]:
        candidates = [current_suffix]

        for _ in range(self.gradient_config.batch_size):
            new_candidate = self._mutate(current_suffix)
            candidates.append(new_candidate)

        return candidates

    def _mutate(self, suffix: str) -> str:
        suffix_list = list(suffix)

        if random.random() < 0.3 and suffix_list:
            pos = random.randint(0, len(suffix_list) - 1)
            new_char = random.choice(self.candidate_tokens)
            suffix_list[pos] = new_char

        if random.random() < 0.1 and suffix_list:
            pos = random.randint(0, len(suffix_list) - 1)
            suffix_list.pop(pos)

        if random.random() < 0.1:
            pos = random.randint(0, len(suffix_list)) if suffix_list else 0
            new_char = random.choice(self.candidate_tokens)
            suffix_list.insert(pos, new_char)

        return "".join(suffix_list)


__all__ = [
    "GradientAttackConfig",
    "GradientBasedAttack",
    "FGSMAttack",
    "PGDAttack",
    "AdversarialSuffixAttack",
]
