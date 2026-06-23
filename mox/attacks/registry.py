"""统一攻击注册表

提供统一的攻击注册和创建机制:
1. 统一的攻击类型定义
2. 统一的工厂函数接口
3. 支持动态注册新攻击
4. 支持攻击类型查询
5. 支持批量创建

改进点:
- 统一所有攻击类型的注册
- 支持动态添加新攻击类型
- 提供攻击类型元数据
- 支持配置验证
"""

from __future__ import annotations

from typing import Callable, Dict, Any, Optional, Type, List, Set
from dataclasses import dataclass, field
from enum import Enum

from mox.core import BaseLLM
from .base import AttackConfig, BaseAttack


# 攻击类型枚举
class AttackCategory(Enum):
    """攻击类别"""

    BASIC = "basic"  # 基础攻击
    NOVEL = "novel"  # 新型攻击
    GRADIENT = "gradient"  # 梯度攻击
    ADVANCED = "advanced"  # 高级攻击
    MULTIMODAL = "multimodal"  # 多模态攻击
    KNOWLEDGE = "knowledge"  # 知识提取攻击
    AGENT = "agent"  # Agent攻击


@dataclass
class AttackTypeInfo:
    """攻击类型信息"""

    name: str
    category: AttackCategory
    attack_class: Type[BaseAttack]
    config_class: Optional[Type] = None
    description: str = ""
    requires_grad: bool = False
    requires_image: bool = False
    requires_llm: bool = False
    aliases: List[str] = field(default_factory=list)


# 攻击工厂类型
AttackFactory = Callable[[BaseLLM, int], BaseAttack]


class AttackRegistry:
    """攻击注册表"""

    def __init__(self):
        self._factories: Dict[str, AttackFactory] = {}
        self._attack_types: Dict[str, AttackTypeInfo] = {}
        self._categories: Dict[AttackCategory, Set[str]] = {
            category: set() for category in AttackCategory
        }
        self._aliases: Dict[str, str] = {}

    def register(
        self,
        name: str,
        factory: AttackFactory,
        category: AttackCategory,
        attack_class: Type[BaseAttack],
        config_class: Optional[Type] = None,
        description: str = "",
        requires_grad: bool = False,
        requires_image: bool = False,
        requires_llm: bool = False,
        aliases: Optional[List[str]] = None,
    ):
        """注册攻击类型

        Args:
            name: 攻击名称
            category: 攻击类别
            attack_class: 攻击类
            factory: 工厂函数
            config_class: 配置类
            description: 描述
            requires_grad: 是否需要梯度
            requires_image: 是否需要图像
            requires_llm: 是否需要LLM
            aliases: 别名列表
        """
        # 注册工厂函数
        self._factories[name] = factory

        # 注册攻击类型信息
        info = AttackTypeInfo(
            name=name,
            category=category,
            attack_class=attack_class,
            config_class=config_class,
            description=description,
            requires_grad=requires_grad,
            requires_image=requires_image,
            requires_llm=requires_llm,
            aliases=aliases or [],
        )
        self._attack_types[name] = info

        # 添加到类别
        self._categories[category].add(name)

        # 注册别名
        for alias in aliases or []:
            self._aliases[alias] = name

    def create(
        self,
        attack_type: str,
        llm: BaseLLM,
        max_iterations: int = 100,
        **kwargs,
    ) -> BaseAttack:
        """创建攻击实例

        Args:
            attack_type: 攻击类型
            llm: 目标LLM
            max_iterations: 最大迭代次数
            **kwargs: 额外配置参数

        Returns:
            BaseAttack: 攻击实例

        Raises:
            ValueError: 未知的攻击类型
        """
        # 解析别名
        resolved_type = self._aliases.get(attack_type, attack_type)

        # 查找工厂函数
        factory = self._factories.get(resolved_type)
        if factory is None:
            raise ValueError(f"Unknown attack type: {attack_type}")

        import inspect

        sig = inspect.signature(factory)
        params = list(sig.parameters.values())
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params):
            return factory(llm, max_iterations, **kwargs)
        extra = {k: v for k, v in kwargs.items() if k in sig.parameters}
        if extra or len(params) > 2:
            try:
                return factory(llm, max_iterations, **extra)
            except TypeError:
                pass
        attack = factory(llm, max_iterations)
        for key, val in kwargs.items():
            if hasattr(attack, key):
                setattr(attack, key, val)
        return attack

    def get_attack_type(self, name: str) -> Optional[AttackTypeInfo]:
        """获取攻击类型信息"""
        resolved_name = self._aliases.get(name, name)
        return self._attack_types.get(resolved_name)

    def get_category(self, category: AttackCategory) -> Set[str]:
        """获取类别下的所有攻击类型"""
        return self._categories.get(category, set())

    def get_all_types(self) -> Dict[str, AttackTypeInfo]:
        """获取所有攻击类型"""
        return self._attack_types.copy()

    def get_all_names(self) -> List[str]:
        """获取所有攻击名称"""
        return list(self._factories.keys())

    def get_aliases(self) -> Dict[str, str]:
        """获取所有别名"""
        return self._aliases.copy()

    def has_type(self, name: str) -> bool:
        """检查是否存在指定攻击类型"""
        resolved_name = self._aliases.get(name, name)
        return resolved_name in self._factories

    def get_statistics(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        return {
            "total_types": len(self._factories),
            "total_aliases": len(self._aliases),
            "by_category": {
                category.value: len(types) for category, types in self._categories.items() if types
            },
        }


# 全局攻击注册表
_registry: Optional[AttackRegistry] = None


def get_registry() -> AttackRegistry:
    """获取全局攻击注册表"""
    global _registry
    if _registry is None:
        _registry = _create_default_registry()
    return _registry


def _create_default_registry() -> AttackRegistry:
    """创建默认攻击注册表"""
    registry = AttackRegistry()

    # 注册基础攻击
    _register_basic_attacks(registry)

    # 注册 LLM 驱动攻击
    _register_llm_driven_attacks(registry)

    # 注册 RAG / Agent / 多轮攻击
    _register_rag_agent_attacks(registry)

    # 注册新型攻击
    _register_novel_attacks(registry)

    # 注册梯度攻击
    _register_gradient_attacks(registry)

    # 注册高级攻击
    _register_advanced_attacks(registry)

    # 注册多模态攻击
    _register_multimodal_attacks(registry)

    # 注册知识提取攻击
    _register_knowledge_attacks(registry)

    # 注册Agent攻击
    _register_agent_attacks(registry)

    # 注册元攻击 / 改进算法
    _register_meta_attacks(registry)

    return registry


def _register_basic_attacks(registry: AttackRegistry):
    """注册基础攻击"""
    from .prompt_injection import PromptInjectionAttack
    from .jailbreak import JailbreakAttack
    from .gcg import GCGAttack, AutoDANAttack

    registry.register(
        name="prompt_injection",
        factory=lambda llm, iter: PromptInjectionAttack(
            target_llm=llm, config=AttackConfig(max_iterations=iter)
        ),
        category=AttackCategory.BASIC,
        attack_class=PromptInjectionAttack,
        description="直接提示注入攻击",
        aliases=["pi", "prompt_inject"],
    )

    registry.register(
        name="jailbreak",
        factory=lambda llm, iter: JailbreakAttack(
            target_llm=llm, config=AttackConfig(max_iterations=iter)
        ),
        category=AttackCategory.BASIC,
        attack_class=JailbreakAttack,
        description="越狱攻击",
        aliases=["jb", "dan"],
    )

    registry.register(
        name="gcg",
        factory=lambda llm, iter: GCGAttack(
            target_llm=llm, config=AttackConfig(max_iterations=iter)
        ),
        category=AttackCategory.BASIC,
        attack_class=GCGAttack,
        description="贪心坐标梯度攻击",
        aliases=["gcg_basic"],
    )

    registry.register(
        name="autodan",
        factory=lambda llm, iter: AutoDANAttack(
            target_llm=llm, config=AttackConfig(max_iterations=iter)
        ),
        category=AttackCategory.BASIC,
        attack_class=AutoDANAttack,
        description="自动DAN攻击",
    )


def _register_llm_driven_attacks(registry: AttackRegistry):
    """注册 LLM 驱动的自动红队攻击"""
    from .llm_driven import TAPAttack, CrescendoAttack, TAPConfig

    registry.register(
        name="tap",
        factory=lambda llm, iter: TAPAttack(target_llm=llm, config=TAPConfig(max_iterations=iter)),
        category=AttackCategory.BASIC,
        attack_class=TAPAttack,
        config_class=TAPConfig,
        description="Tree of Attacks 自动越狱",
        requires_llm=True,
        aliases=["tree_of_attacks"],
    )

    registry.register(
        name="pair",
        factory=lambda llm, iter: TAPAttack(
            target_llm=llm,
            config=TAPConfig(max_iterations=iter, use_refinement=True),
        ),
        category=AttackCategory.BASIC,
        attack_class=TAPAttack,
        config_class=TAPConfig,
        description="PAIR 提示自动迭代精炼攻击",
        requires_llm=True,
        aliases=["prompt_automatic_iterative_refinement"],
    )

    registry.register(
        name="crescendo",
        factory=lambda llm, iter: CrescendoAttack(
            target_llm=llm, config=AttackConfig(max_iterations=iter)
        ),
        category=AttackCategory.BASIC,
        attack_class=CrescendoAttack,
        description="Crescendo 渐进式多轮越狱",
        requires_llm=True,
        aliases=["crescendo_jailbreak"],
    )


def _register_rag_agent_attacks(registry: AttackRegistry):
    """注册 RAG / Agent / 多轮攻击"""
    from .llm_driven import MultiTurnJailbreakAttack, TAPConfig
    from .rag_attacks import RAGContextInjectionAttack, AgentToolManipulationAttack

    registry.register(
        name="multi_turn",
        factory=lambda llm, iter: MultiTurnJailbreakAttack(
            target_llm=llm, config=TAPConfig(max_iterations=iter, max_depth=5)
        ),
        category=AttackCategory.BASIC,
        attack_class=MultiTurnJailbreakAttack,
        config_class=TAPConfig,
        description="多轮对话越狱攻击",
        requires_llm=True,
        aliases=["multi_turn_jailbreak", "goat"],
    )

    registry.register(
        name="rag_context_injection",
        factory=lambda llm, iter: RAGContextInjectionAttack(target_llm=llm),
        category=AttackCategory.NOVEL,
        attack_class=RAGContextInjectionAttack,
        description="RAG 上下文注入攻击",
        aliases=["rag"],
    )

    registry.register(
        name="agent_tool_manipulation",
        factory=lambda llm, iter: AgentToolManipulationAttack(
            target_llm=llm, config=AttackConfig(max_iterations=iter)
        ),
        category=AttackCategory.AGENT,
        attack_class=AgentToolManipulationAttack,
        description="Agent 工具操纵攻击",
        aliases=["agent"],
    )


def _register_novel_attacks(registry: AttackRegistry):
    """注册新型攻击"""
    from .novel_attacks import (
        TokenLevelAttack,
        EncodingAttack,
        PolicyPuppetryAttack,
        ControlCharInjectionAttack,
        DistractAndAttack,
        CascadingAttack,
    )

    registry.register(
        name="token_level",
        factory=lambda llm, iter: TokenLevelAttack(target_llm=llm),
        category=AttackCategory.NOVEL,
        attack_class=TokenLevelAttack,
        description="Token级攻击",
    )

    registry.register(
        name="encoding",
        factory=lambda llm, iter: EncodingAttack(target_llm=llm),
        category=AttackCategory.NOVEL,
        attack_class=EncodingAttack,
        description="编码混淆攻击",
        aliases=["base64", "rot13"],
    )

    registry.register(
        name="policy_puppetry",
        factory=lambda llm, iter: PolicyPuppetryAttack(target_llm=llm),
        category=AttackCategory.NOVEL,
        attack_class=PolicyPuppetryAttack,
        description="策略伪装攻击",
        aliases=["policy"],
    )

    registry.register(
        name="control_char",
        factory=lambda llm, iter: ControlCharInjectionAttack(target_llm=llm),
        category=AttackCategory.NOVEL,
        attack_class=ControlCharInjectionAttack,
        description="控制字符注入攻击",
    )

    registry.register(
        name="distract_attack",
        factory=lambda llm, iter: DistractAndAttack(target_llm=llm),
        category=AttackCategory.NOVEL,
        attack_class=DistractAndAttack,
        description="分散注意力攻击",
    )

    registry.register(
        name="cascading",
        factory=lambda llm, iter: CascadingAttack(target_llm=llm),
        category=AttackCategory.NOVEL,
        attack_class=CascadingAttack,
        description="级联攻击",
        aliases=["rag_poisoning"],
    )


def _register_gradient_attacks(registry: AttackRegistry):
    """注册梯度攻击"""
    from .gradient_attack import (
        GCGAttack as GradientGCGAttack,
        AutoPromptAttack,
        GradientBasedSuffixAttack,
        GradientAttackConfig,
    )

    def _build_gradient_gcg(llm: BaseLLM, max_iterations: int):
        config = GradientAttackConfig(max_iterations=max_iterations)
        return GradientGCGAttack(target_llm=llm, gradient_config=config)

    def _build_autoprompt(llm: BaseLLM, max_iterations: int):
        config = GradientAttackConfig(max_iterations=max_iterations)
        return AutoPromptAttack(target_llm=llm, gradient_config=config)

    def _build_gradient_suffix(llm: BaseLLM, max_iterations: int):
        config = GradientAttackConfig(max_iterations=max_iterations)
        return GradientBasedSuffixAttack(target_llm=llm, gradient_config=config)

    registry.register(
        name="gradient_gcg",
        factory=_build_gradient_gcg,
        category=AttackCategory.GRADIENT,
        attack_class=GradientGCGAttack,
        config_class=GradientAttackConfig,
        description="基于梯度的GCG攻击",
        requires_grad=True,
        aliases=["gcg_gradient"],
    )

    registry.register(
        name="autoprompt",
        factory=_build_autoprompt,
        category=AttackCategory.GRADIENT,
        attack_class=AutoPromptAttack,
        config_class=GradientAttackConfig,
        description="自动提示攻击",
        requires_grad=True,
    )

    registry.register(
        name="gradient_optimization",
        factory=_build_gradient_suffix,
        category=AttackCategory.GRADIENT,
        attack_class=GradientBasedSuffixAttack,
        config_class=GradientAttackConfig,
        description="梯度优化攻击",
        requires_grad=True,
        aliases=["adversarial_suffix"],
    )


def _register_advanced_attacks(registry: AttackRegistry):
    """注册高级攻击"""
    from .advanced_attacks import (
        TextBasedAdversarialAttack,
        ZeroShotAdversarialAttack,
        HallucinationInductionAttack,
        CollaborativeAttack,
        EvasionAttack,
        AdvancedAttackConfig,
    )
    from .meta_adversarial import MetaAdversarialAttack, MetaAdversarialConfig

    def _build_text_based(llm: BaseLLM, max_iterations: int):
        config = AdvancedAttackConfig(max_iterations=max_iterations)
        return TextBasedAdversarialAttack(target_llm=llm, advanced_config=config)

    def _build_zero_shot(llm: BaseLLM, max_iterations: int):
        config = AdvancedAttackConfig(max_iterations=max_iterations)
        return ZeroShotAdversarialAttack(target_llm=llm, advanced_config=config)

    def _build_hallucination(llm: BaseLLM, max_iterations: int):
        config = AdvancedAttackConfig(max_iterations=max_iterations)
        return HallucinationInductionAttack(target_llm=llm, advanced_config=config)

    def _build_collaborative(llm: BaseLLM, max_iterations: int):
        config = AdvancedAttackConfig(max_iterations=max_iterations)
        return CollaborativeAttack(target_llm=llm, advanced_config=config)

    def _build_evasion(llm: BaseLLM, max_iterations: int):
        config = AdvancedAttackConfig(max_iterations=max_iterations)
        return EvasionAttack(target_llm=llm, advanced_config=config)

    def _build_meta_adversarial(llm: BaseLLM, max_iterations: int):
        config = MetaAdversarialConfig(max_iterations=max_iterations, use_adversarial_trinity=True)
        return MetaAdversarialAttack(target_llm=llm, meta_config=config)

    registry.register(
        name="text_based_adversarial",
        factory=_build_text_based,
        category=AttackCategory.ADVANCED,
        attack_class=TextBasedAdversarialAttack,
        config_class=AdvancedAttackConfig,
        description="基于文本的对抗攻击",
        aliases=["multimodal_adversarial"],
    )

    registry.register(
        name="zero_shot_adversarial",
        factory=_build_zero_shot,
        category=AttackCategory.ADVANCED,
        attack_class=ZeroShotAdversarialAttack,
        config_class=AdvancedAttackConfig,
        description="零样本对抗攻击",
    )

    registry.register(
        name="hallucination_induction",
        factory=_build_hallucination,
        category=AttackCategory.ADVANCED,
        attack_class=HallucinationInductionAttack,
        config_class=AdvancedAttackConfig,
        description="幻觉诱导攻击",
    )

    registry.register(
        name="collaborative_attack",
        factory=_build_collaborative,
        category=AttackCategory.ADVANCED,
        attack_class=CollaborativeAttack,
        config_class=AdvancedAttackConfig,
        description="协同攻击",
    )

    registry.register(
        name="evasion_attack",
        factory=_build_evasion,
        category=AttackCategory.ADVANCED,
        attack_class=EvasionAttack,
        config_class=AdvancedAttackConfig,
        description="逃逸攻击",
    )

    registry.register(
        name="meta_adversarial",
        factory=_build_meta_adversarial,
        category=AttackCategory.ADVANCED,
        attack_class=MetaAdversarialAttack,
        config_class=MetaAdversarialConfig,
        description="元对抗攻击",
    )


def _register_multimodal_attacks(registry: AttackRegistry):
    """注册多模态攻击"""
    from .multimodal_attacks import (
        ImageInjectionAttack,
        VisualPromptAttack,
        TextImageHybridAttack,
        MultimodalAttackEnsemble,
        MultimodalAttackConfig,
    )

    def _build_image_injection(llm: BaseLLM, max_iterations: int):
        config = MultimodalAttackConfig(max_iterations=max_iterations)
        return ImageInjectionAttack(target_llm=llm, multimodal_config=config)

    def _build_visual_prompt(llm: BaseLLM, max_iterations: int):
        config = MultimodalAttackConfig(max_iterations=max_iterations)
        return VisualPromptAttack(target_llm=llm, multimodal_config=config)

    def _build_text_image_hybrid(llm: BaseLLM, max_iterations: int):
        config = MultimodalAttackConfig(max_iterations=max_iterations)
        return TextImageHybridAttack(target_llm=llm, multimodal_config=config)

    def _build_multimodal_ensemble(llm: BaseLLM, max_iterations: int):
        config = MultimodalAttackConfig(max_iterations=max_iterations)
        return MultimodalAttackEnsemble(target_llm=llm, multimodal_config=config)

    registry.register(
        name="image_injection",
        factory=_build_image_injection,
        category=AttackCategory.MULTIMODAL,
        attack_class=ImageInjectionAttack,
        config_class=MultimodalAttackConfig,
        description="图像注入攻击",
        requires_image=True,
        aliases=["audio_injection"],
    )

    registry.register(
        name="visual_prompt",
        factory=_build_visual_prompt,
        category=AttackCategory.MULTIMODAL,
        attack_class=VisualPromptAttack,
        config_class=MultimodalAttackConfig,
        description="视觉提示攻击",
        requires_image=True,
        aliases=["figstep", "multimodal_jailbreak"],
    )

    registry.register(
        name="text_image_hybrid",
        factory=_build_text_image_hybrid,
        category=AttackCategory.MULTIMODAL,
        attack_class=TextImageHybridAttack,
        config_class=MultimodalAttackConfig,
        description="图文混合攻击",
        requires_image=True,
        aliases=["cross_modal"],
    )

    registry.register(
        name="multimodal_ensemble",
        factory=_build_multimodal_ensemble,
        category=AttackCategory.MULTIMODAL,
        attack_class=MultimodalAttackEnsemble,
        config_class=MultimodalAttackConfig,
        description="多模态攻击集成",
        requires_image=True,
    )


def _register_knowledge_attacks(registry: AttackRegistry):
    """注册知识提取攻击"""
    from .knowledge_extraction import (
        ProgressiveKnowledgeExtraction,
        FeatureProbingAttack,
        SoftLabelExtractionAttack,
        KnowledgeDistillationAttack,
        KnowledgeExtractionEnsemble,
        KnowledgeExtractionConfig,
    )
    from .advanced_attacks import KnowledgeExtractionAttack

    def _build_progressive_extraction(llm: BaseLLM, max_iterations: int):
        config = KnowledgeExtractionConfig(max_iterations=max_iterations)
        return ProgressiveKnowledgeExtraction(target_llm=llm, extraction_config=config)

    def _build_feature_probing(llm: BaseLLM, max_iterations: int):
        config = KnowledgeExtractionConfig(max_iterations=max_iterations)
        return FeatureProbingAttack(target_llm=llm, extraction_config=config)

    def _build_soft_label(llm: BaseLLM, max_iterations: int):
        config = KnowledgeExtractionConfig(max_iterations=max_iterations)
        return SoftLabelExtractionAttack(target_llm=llm, extraction_config=config)

    def _build_knowledge_distillation(llm: BaseLLM, max_iterations: int):
        config = KnowledgeExtractionConfig(max_iterations=max_iterations)
        return KnowledgeDistillationAttack(target_llm=llm, extraction_config=config)

    def _build_knowledge_ensemble(llm: BaseLLM, max_iterations: int):
        config = KnowledgeExtractionConfig(max_iterations=max_iterations)
        return KnowledgeExtractionEnsemble(target_llm=llm, extraction_config=config)

    def _build_knowledge_extraction(llm: BaseLLM, max_iterations: int):
        from .advanced_attacks import AdvancedAttackConfig

        config = AdvancedAttackConfig(max_iterations=max_iterations)
        return KnowledgeExtractionAttack(target_llm=llm, advanced_config=config)

    registry.register(
        name="progressive_extraction",
        factory=_build_progressive_extraction,
        category=AttackCategory.KNOWLEDGE,
        attack_class=ProgressiveKnowledgeExtraction,
        config_class=KnowledgeExtractionConfig,
        description="渐进式知识提取",
        aliases=["progressive_knowledge"],
    )

    registry.register(
        name="feature_probing",
        factory=_build_feature_probing,
        category=AttackCategory.KNOWLEDGE,
        attack_class=FeatureProbingAttack,
        config_class=KnowledgeExtractionConfig,
        description="特征探测攻击",
    )

    registry.register(
        name="soft_label_extraction",
        factory=_build_soft_label,
        category=AttackCategory.KNOWLEDGE,
        attack_class=SoftLabelExtractionAttack,
        config_class=KnowledgeExtractionConfig,
        description="软标签提取攻击",
        aliases=["soft_label"],
    )

    registry.register(
        name="knowledge_distillation",
        factory=_build_knowledge_distillation,
        category=AttackCategory.KNOWLEDGE,
        attack_class=KnowledgeDistillationAttack,
        config_class=KnowledgeExtractionConfig,
        description="知识蒸馏攻击",
    )

    registry.register(
        name="knowledge_extraction",
        factory=_build_knowledge_extraction,
        category=AttackCategory.KNOWLEDGE,
        attack_class=KnowledgeExtractionAttack,
        description="知识提取攻击",
        aliases=["knowledge_extract"],
    )

    registry.register(
        name="knowledge_ensemble",
        factory=_build_knowledge_ensemble,
        category=AttackCategory.KNOWLEDGE,
        attack_class=KnowledgeExtractionEnsemble,
        config_class=KnowledgeExtractionConfig,
        description="知识提取攻击集成",
    )


def _register_agent_attacks(registry: AttackRegistry):
    """注册Agent攻击"""
    from .agent_attacks import (
        ToolAbuseAttack,
        MemoryInjectionAttack,
        RoleHijackingAttack,
        AuthorityEscalationAttack,
        ChainOfThoughtInjectionAttack,
        AgentAttackConfig,
    )

    def _build_tool_abuse(llm: BaseLLM, max_iterations: int):
        config = AgentAttackConfig(max_iterations=max_iterations)
        return ToolAbuseAttack(target_llm=llm, config=config)

    def _build_memory_injection(llm: BaseLLM, max_iterations: int):
        config = AgentAttackConfig(max_iterations=max_iterations)
        return MemoryInjectionAttack(target_llm=llm, config=config)

    def _build_role_hijacking(llm: BaseLLM, max_iterations: int):
        config = AgentAttackConfig(max_iterations=max_iterations)
        return RoleHijackingAttack(target_llm=llm, config=config)

    def _build_authority_escalation(llm: BaseLLM, max_iterations: int):
        config = AgentAttackConfig(max_iterations=max_iterations)
        return AuthorityEscalationAttack(target_llm=llm, config=config)

    def _build_cot_injection(llm: BaseLLM, max_iterations: int):
        config = AgentAttackConfig(max_iterations=max_iterations)
        return ChainOfThoughtInjectionAttack(target_llm=llm, config=config)

    registry.register(
        name="tool_abuse",
        factory=_build_tool_abuse,
        category=AttackCategory.AGENT,
        attack_class=ToolAbuseAttack,
        config_class=AgentAttackConfig,
        description="工具滥用攻击",
        requires_llm=True,
    )

    registry.register(
        name="memory_injection",
        factory=_build_memory_injection,
        category=AttackCategory.AGENT,
        attack_class=MemoryInjectionAttack,
        config_class=AgentAttackConfig,
        description="记忆注入攻击",
        requires_llm=True,
    )

    registry.register(
        name="role_hijacking",
        factory=_build_role_hijacking,
        category=AttackCategory.AGENT,
        attack_class=RoleHijackingAttack,
        config_class=AgentAttackConfig,
        description="角色劫持攻击",
        requires_llm=True,
    )

    registry.register(
        name="authority_escalation",
        factory=_build_authority_escalation,
        category=AttackCategory.AGENT,
        attack_class=AuthorityEscalationAttack,
        config_class=AgentAttackConfig,
        description="权限提升攻击",
        requires_llm=True,
    )

    registry.register(
        name="cot_injection",
        factory=_build_cot_injection,
        category=AttackCategory.AGENT,
        attack_class=ChainOfThoughtInjectionAttack,
        config_class=AgentAttackConfig,
        description="思维链注入攻击",
        requires_llm=True,
    )

    from .agent_attacks_advanced import (
        ToolChainingAttack,
        IndirectToolInjection,
        PrivilegeEscalationAttack,
        ToolConfusionAttack,
        DataExfiltrationAttack,
        MultiAgentAttack,
        CompositeAgentAttack,
    )

    def _build_agent_advanced(factory_fn):
        def builder(llm: BaseLLM, max_iterations: int):
            config = AgentAttackConfig(max_iterations=max_iterations)
            return factory_fn(llm, config)

        return builder

    registry.register(
        name="tool_chaining",
        factory=_build_agent_advanced(ToolChainingAttack),
        category=AttackCategory.AGENT,
        attack_class=ToolChainingAttack,
        config_class=AgentAttackConfig,
        description="工具链攻击",
        requires_llm=True,
    )
    registry.register(
        name="indirect_injection",
        factory=_build_agent_advanced(IndirectToolInjection),
        category=AttackCategory.AGENT,
        attack_class=IndirectToolInjection,
        config_class=AgentAttackConfig,
        description="间接工具注入攻击",
        requires_llm=True,
    )
    registry.register(
        name="privilege_escalation",
        factory=_build_agent_advanced(PrivilegeEscalationAttack),
        category=AttackCategory.AGENT,
        attack_class=PrivilegeEscalationAttack,
        config_class=AgentAttackConfig,
        description="权限提升攻击（Agent）",
        requires_llm=True,
        aliases=["authority_escalation_agent"],
    )
    registry.register(
        name="tool_confusion",
        factory=_build_agent_advanced(ToolConfusionAttack),
        category=AttackCategory.AGENT,
        attack_class=ToolConfusionAttack,
        config_class=AgentAttackConfig,
        description="工具混淆攻击",
        requires_llm=True,
    )
    registry.register(
        name="data_exfiltration",
        factory=_build_agent_advanced(DataExfiltrationAttack),
        category=AttackCategory.AGENT,
        attack_class=DataExfiltrationAttack,
        config_class=AgentAttackConfig,
        description="数据外泄攻击",
        requires_llm=True,
    )
    registry.register(
        name="multi_agent",
        factory=_build_agent_advanced(MultiAgentAttack),
        category=AttackCategory.AGENT,
        attack_class=MultiAgentAttack,
        config_class=AgentAttackConfig,
        description="多 Agent 攻击",
        requires_llm=True,
    )
    registry.register(
        name="composite",
        factory=_build_agent_advanced(CompositeAgentAttack),
        category=AttackCategory.AGENT,
        attack_class=CompositeAgentAttack,
        config_class=AgentAttackConfig,
        description="组合 Agent 攻击",
        requires_llm=True,
        aliases=["composite_agent"],
    )

    from .novel_attacks import (
        ManyShotJailbreakAttack,
        SkeletonKeyAttack,
        DeceptiveAlignmentAttack,
        CognitiveOverloadAttack,
        ContextOverflowAttack,
        RoleConfusionAttack,
    )

    def _build_novel(factory_fn):
        def builder(llm: BaseLLM, max_iterations: int):
            return factory_fn(target_llm=llm)

        return builder

    registry.register(
        name="many_shot",
        factory=_build_novel(ManyShotJailbreakAttack),
        category=AttackCategory.NOVEL,
        attack_class=ManyShotJailbreakAttack,
        description="Many-shot 越狱攻击",
        aliases=["many_shot_jailbreak"],
    )
    registry.register(
        name="skeleton_key",
        factory=_build_novel(SkeletonKeyAttack),
        category=AttackCategory.NOVEL,
        attack_class=SkeletonKeyAttack,
        description="Skeleton Key 攻击",
    )
    registry.register(
        name="deceptive_alignment",
        factory=_build_novel(DeceptiveAlignmentAttack),
        category=AttackCategory.NOVEL,
        attack_class=DeceptiveAlignmentAttack,
        description="欺骗性对齐攻击",
    )
    registry.register(
        name="cognitive_overload",
        factory=_build_novel(CognitiveOverloadAttack),
        category=AttackCategory.NOVEL,
        attack_class=CognitiveOverloadAttack,
        description="认知过载攻击",
    )
    registry.register(
        name="context_overflow",
        factory=_build_novel(ContextOverflowAttack),
        category=AttackCategory.NOVEL,
        attack_class=ContextOverflowAttack,
        description="上下文溢出攻击",
    )
    registry.register(
        name="role_confusion",
        factory=_build_novel(RoleConfusionAttack),
        category=AttackCategory.NOVEL,
        attack_class=RoleConfusionAttack,
        description="角色混淆攻击",
    )


def _register_meta_attacks(registry: AttackRegistry):
    """注册改进 GCG、自适应策略、攻击链等元攻击"""
    from .improved_gcg import ImprovedGCGAttack
    from .adaptive_strategy import AdaptiveAttackStrategy, AdaptiveConfig
    from .chain import RegistryAttackChainAttack

    registry.register(
        name="improved_gcg",
        factory=lambda llm, iter, **kw: ImprovedGCGAttack(
            target_llm=llm, config=AttackConfig(max_iterations=iter)
        ),
        category=AttackCategory.GRADIENT,
        attack_class=ImprovedGCGAttack,
        description="改进版 GCG（热启动、迁移、并行评估）",
        requires_grad=True,
        aliases=["gcg_improved", "gcg_v2"],
    )

    registry.register(
        name="adaptive",
        factory=lambda llm, iter, **kw: AdaptiveAttackStrategy(
            target_llm=llm,
            config=AttackConfig(max_iterations=iter),
            adaptive_config=AdaptiveConfig(),
        ),
        category=AttackCategory.ADVANCED,
        attack_class=AdaptiveAttackStrategy,
        description="自适应攻击策略（动态选策略 + 反馈学习）",
        aliases=["adaptive_strategy", "meta_attack"],
    )

    registry.register(
        name="attack_chain",
        factory=lambda llm, iter, **kw: RegistryAttackChainAttack(
            target_llm=llm, config=AttackConfig(max_iterations=iter)
        ),
        category=AttackCategory.ADVANCED,
        attack_class=RegistryAttackChainAttack,
        description="组合攻击链（encoding → jailbreak → tap）",
        aliases=["chain", "combo_attack"],
    )


# 便捷函数
def create_attack_instance(
    attack_type: str,
    llm: BaseLLM,
    max_iterations: int = 100,
    **kwargs,
) -> BaseAttack:
    """创建攻击实例

    Args:
        attack_type: 攻击类型
        llm: 目标LLM
        max_iterations: 最大迭代次数
        **kwargs: 额外配置参数

    Returns:
        BaseAttack: 攻击实例
    """
    registry = get_registry()
    return registry.create(attack_type, llm, max_iterations, **kwargs)


def get_attack_type(name: str) -> Optional[AttackTypeInfo]:
    """获取攻击类型信息"""
    registry = get_registry()
    return registry.get_attack_type(name)


def get_all_attack_types() -> Dict[str, AttackTypeInfo]:
    """获取所有攻击类型"""
    registry = get_registry()
    return registry.get_all_types()


def get_attack_types_by_category(category: AttackCategory) -> Set[str]:
    """获取类别下的所有攻击类型"""
    registry = get_registry()
    return registry.get_category(category)


def list_attack_types() -> List[str]:
    """列出所有攻击类型"""
    registry = get_registry()
    return registry.get_all_names()


def has_attack_type(name: str) -> bool:
    """检查是否存在指定攻击类型"""
    registry = get_registry()
    return registry.has_type(name)


def get_registry_statistics() -> Dict[str, Any]:
    """获取注册表统计信息"""
    registry = get_registry()
    return registry.get_statistics()


# 向后兼容的导出
__all__ = [
    "AttackCategory",
    "AttackTypeInfo",
    "AttackRegistry",
    "AttackFactory",
    "get_registry",
    "create_attack_instance",
    "get_attack_type",
    "get_all_attack_types",
    "get_attack_types_by_category",
    "list_attack_types",
    "has_attack_type",
    "get_registry_statistics",
]
