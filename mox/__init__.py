"""
Mox - 大模型对抗攻防平台
LLM Adversarial Attack & Defense Platform

一个完整的用于测试和评估大语言模型安全性的平台。

主要功能:
- 攻击模块: Prompt Injection, Jailbreak, GCG, AutoDAN 等
- 防御模块: 输入过滤, 输出过滤, 系统提示词加固
- 评估模块: 攻击成功率, 防御效果, 鲁棒性评估
- Web界面: Gradio UI 和 FastAPI 接口

支持模型:
- OpenAI (GPT-3.5, GPT-4, o1, o3)
- Anthropic (Claude)
- MiniMax (abab系列)
- Google (Gemini)
- DeepSeek
- Cohere
- Groq
- Azure OpenAI
- 本地模型 (Ollama)

使用示例:
    from mox import LLMFactory, PromptInjectionAttack, InputFilter

    # 创建 LLM 实例
    llm = LLMFactory.create_from_model_name("gpt-4")

    # 运行攻击测试
    attack = PromptInjectionAttack(target_llm=llm)
    outcome = await attack.generate_attack(payload)

    # 运行防御检测
    defense = InputFilter()
    result = await defense.detect(user_input)
"""

__version__ = "0.2.0"

from mox.core import (
    settings,
    Settings,
    BaseLLM,
    OpenAILLM,
    AnthropicLLM,
    MiniMaxLLM,
    OllamaLLM,
    GeminiLLM,
    DeepSeekLLM,
    CohereLLM,
    GroqLLM,
    AzureOpenAILLM,
    LLMFactory,
    ModelProvider,
    Message,
    LLMResponse,
    AttackType,
    DefenseType,
    AttackResult,
    AttackPayload,
    AttackOutcome,
    DefenseResult,
    EvaluationReport,
    User,
    TokenManager,
    PasswordManager,
    auth_manager,
)

from mox.attacks import (
    BaseAttack,
    AttackConfig,
    PromptInjectionAttack,
    AdvancedPromptInjection,
    JailbreakAttack,
    GCGAttack,
    AutoDANAttack,
    TAPAttack,
    MultiTurnJailbreakAttack,
    CrescendoAttack,
    TAPConfig,
    RAGAttackType,
    RAGAttackConfig,
    RAGContextInjectionAttack,
    AgentToolManipulationAttack,
    ChainOfThoughtExfiltrationAttack,
    IndirectPromptInjectionAttack,
    AgentAttackType,
    AgentAttackConfig,
    ToolAbuseAttack,
    MemoryInjectionAttack,
    RoleHijackingAttack,
    AuthorityEscalationAttack,
    ChainOfThoughtInjectionAttack,
)

from mox.defense import (
    BaseDefense,
    DefenseConfig,
    InputFilter,
    OutputFilter,
    PerplexityFilter,
    KeywordDetector,
    ContentModerator,
    SystemPromptHardening,
    DefensePipeline,
)
from mox.defense.llm_judge import (
    LLMJudge,
    SafetyJudgment,
    JudgmentType,
    HarmCategory,
    DefenseEvaluator,
    SafetyCoTDefense,
)

from mox.evaluation import (
    AttackEvaluator,
    DefenseEvaluator,
    RobustnessEvaluator,
    BenchmarkRunner,
    BenchmarkDataset,
    ChartData,
    ReportGenerator,
    create_quick_report,
)

__all__ = [
    "__version__",
    "settings",
    "Settings",
    "BaseLLM",
    "OpenAILLM",
    "AnthropicLLM",
    "MiniMaxLLM",
    "OllamaLLM",
    "GeminiLLM",
    "DeepSeekLLM",
    "CohereLLM",
    "GroqLLM",
    "AzureOpenAILLM",
    "LLMFactory",
    "ModelProvider",
    "Message",
    "LLMResponse",
    "AttackType",
    "DefenseType",
    "AttackResult",
    "AttackPayload",
    "AttackOutcome",
    "DefenseResult",
    "EvaluationReport",
    "BaseAttack",
    "AttackConfig",
    "PromptInjectionAttack",
    "AdvancedPromptInjection",
    "JailbreakAttack",
    "GCGAttack",
    "AutoDANAttack",
    "TAPAttack",
    "MultiTurnJailbreakAttack",
    "CrescendoAttack",
    "TAPConfig",
    "RAGAttackType",
    "RAGAttackConfig",
    "RAGContextInjectionAttack",
    "AgentToolManipulationAttack",
    "ChainOfThoughtExfiltrationAttack",
    "IndirectPromptInjectionAttack",
    "AgentAttackType",
    "AgentAttackConfig",
    "ToolAbuseAttack",
    "MemoryInjectionAttack",
    "RoleHijackingAttack",
    "AuthorityEscalationAttack",
    "ChainOfThoughtInjectionAttack",
    "BaseDefense",
    "DefenseConfig",
    "InputFilter",
    "OutputFilter",
    "PerplexityFilter",
    "KeywordDetector",
    "ContentModerator",
    "SystemPromptHardening",
    "DefensePipeline",
    "LLMJudge",
    "SafetyJudgment",
    "JudgmentType",
    "HarmCategory",
    "DefenseEvaluator",
    "SafetyCoTDefense",
    "AttackEvaluator",
    "DefenseEvaluator",
    "RobustnessEvaluator",
    "BenchmarkRunner",
    "BenchmarkDataset",
    "ChartData",
    "ReportGenerator",
    "create_quick_report",
    "User",
    "TokenManager",
    "PasswordManager",
    "auth_manager",
]
