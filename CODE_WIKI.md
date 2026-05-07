# Mox Code Wiki — 大模型对抗攻防平台

> **版本**: v0.3.0 | **Python**: ≥3.11 | **协议**: MIT

---

## 目录

1. [项目概述](#1-项目概述)
2. [整体架构](#2-整体架构)
3. [项目目录结构](#3-项目目录结构)
4. [核心模块 (mox/core)](#4-核心模块-moxcore)
5. [攻击模块 (mox/attacks)](#5-攻击模块-moxattacks)
6. [防御模块 (mox/defense)](#6-防御模块-moxdefense)
7. [评估模块 (mox/evaluation)](#7-评估模块-moxevaluation)
8. [基础设施层 (mox/infrastructure)](#8-基础设施层-moxinfrastructure)
9. [路由层 (mox/routes)](#9-路由层-moxroutes)
10. [中间件层 (mox/middleware)](#10-中间件层-moxmiddleware)
11. [工作流模块 (mox/workflows)](#11-工作流模块-moxworkflows)
12. [前端 (frontend)](#12-前端-frontend)
13. [模块间依赖关系](#13-模块间依赖关系)
14. [数据流与关键交互](#14-数据流与关键交互)
15. [项目运行方式](#15-项目运行方式)
16. [测试体系](#16-测试体系)
17. [部署方案](#17-部署方案)

---

## 1. 项目概述

Mox 是一个完整的**大语言模型 (LLM) 对抗攻防平台**，用于测试和评估大语言模型的安全性。平台提供三大核心能力：

- **攻击 (Attack)**: 20+ 种对抗攻击实现（Prompt Injection、Jailbreak、GCG、AutoDAN、TAP、Crescendo、RAG 攻击、Agent 攻击等）
- **防御 (Defense)**: 多层防御体系（输入过滤、输出过滤、系统提示词加固、注入检测、语义防火墙、Constitutional AI、LLM Judge 等）
- **评估 (Evaluation)**: 统一评估框架（攻击成功率、多维度评估、基准测试、红队编排、模型安全卡片）

支持 10+ 种 LLM 提供商：OpenAI、Anthropic、MiniMax、Google Gemini、DeepSeek、Cohere、Groq、Azure OpenAI、Ollama 本地模型等。

---

## 2. 整体架构

```
┌──────────────────────────────────────────────────────────────┐
│                        前端 (React + Vite)                     │
│  Pages: Attack / Defense / Benchmark / OWASP / RedTeam / ...  │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP / WebSocket
┌────────────────────────▼─────────────────────────────────────┐
│                    API 层 (FastAPI)                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │  attack   │ │  defense │ │ benchmark │ │   auth   │        │
│  │  router   │ │  router  │ │  router   │ │  router  │        │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘        │
│       │            │            │             │               │
│  ┌────▼────────────▼────────────▼─────────────▼─────┐        │
│  │              中间件层 (Middleware)                  │        │
│  │   Rate Limit │ CORS │ API Versioning │ Auth       │        │
│  └────────────────────┬────────────────────────────┘        │
└───────────────────────┼──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│                    业务逻辑层                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐         │
│  │   Attacks    │  │   Defense   │  │  Evaluation  │         │
│  │  (20+ 攻击)  │  │  (10+ 防御)  │  │  (评估框架)   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘         │
│         │                │                 │                  │
│  ┌──────▼────────────────▼─────────────────▼───────┐         │
│  │              Core (统一模式库 / 评估 / 相似度)      │         │
│  │   Patterns │ Evaluation │ Similarity │ Types     │         │
│  └────────────────────┬────────────────────────────┘         │
│                       │                                       │
│  ┌────────────────────▼────────────────────────────┐         │
│  │              LLM 抽象层                           │         │
│  │   BaseLLM │ LLMFactory │ LLMGateway (负载均衡)    │         │
│  └────────────────────┬────────────────────────────┘         │
└───────────────────────┼──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│                  基础设施层 (Infrastructure)                    │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │ Config  │ │  Auth  │ │Database│ │ Cache  │ │Logging │    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │Monitor │ │ Report │ │ Sandbox│ │ Tasks  │ │Plugin  │    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
└──────────────────────────────────────────────────────────────┘
```

**架构特点**：
- **分层架构**: 前端 → API → 业务逻辑 → 核心抽象 → 基础设施，职责清晰
- **注册中心模式**: 攻击和防御组件通过装饰器自动注册，支持动态加载
- **统一模式库**: 拒绝模式、恶意模式、有害关键词等统一维护在 `core/patterns.py`，消除 30+ 处重复代码
- **统一评估框架**: 所有攻击评估通过 `core/evaluation.py` 的 `AttackEvaluator` ABC 进行，消除 40+ 处重复定义
- **工厂模式**: `LLMFactory` 根据模型名称自动选择提供商，`create_evaluator` 按策略创建评估器

---

## 3. 项目目录结构

```
mox/
├── mox/                          # 主 Python 包
│   ├── __init__.py               # 包入口，统一导出所有公共 API
│   ├── __main__.py               # python -m mox 入口
│   ├── api.py                    # FastAPI 应用工厂与路由注册
│   ├── cli.py                    # CLI 命令行工具
│   ├── ui.py                     # Gradio Web UI
│   ├── core/                     # 核心抽象层
│   │   ├── types.py              # Pydantic 类型定义 (AttackType, DefenseType, AttackPayload 等)
│   │   ├── llm.py                # LLM 抽象层 (BaseLLM + 10 个提供商实现 + LLMFactory)
│   │   ├── llm_router.py         # LLM 网关 (负载均衡、故障转移)
│   │   ├── patterns.py           # 统一模式库 (RefusalPatterns, MaliciousPatterns, HarmfulKeywords)
│   │   ├── evaluation.py         # 统一评估框架 (EvaluationResult, AttackEvaluator ABC, 多种评估器)
│   │   ├── similarity.py         # 统一相似度 (word_overlap, cosine, semantic)
│   │   ├── exceptions.py         # 自定义异常体系
│   │   ├── version.py            # 版本管理
│   │   ├── workflow.py           # 工作流引擎
│   │   ├── security_guard.py     # 安全网关
│   │   ├── rag_isolation.py      # RAG 隔离
│   │   ├── prompt_protection.py  # 提示词保护
│   │   └── chinese_llm.py        # 中文 LLM 支持
│   ├── attacks/                  # 攻击模块 (20+ 攻击实现)
│   │   ├── base.py               # 攻击基类 (BaseAttack, AttackConfig)
│   │   ├── registry.py           # 攻击注册中心 (ATTACK_REGISTRY)
│   │   ├── config.py             # 攻击配置注册 (CONFIG_REGISTRY, TAPConfig)
│   │   ├── evaluation.py         # 向后兼容评估导出
│   │   ├── orchestrator.py       # 统一攻击编排器
│   │   ├── prompt_injection.py   # 提示词注入攻击
│   │   ├── jailbreak.py          # 越狱攻击 (DAN, Developer Mode, AIM 等)
│   │   ├── gcg.py                # GCG / AutoDAN 梯度优化攻击
│   │   ├── improved_gcg.py       # 改进的 GCG 攻击
│   │   ├── gradient_attack.py    # FGSM / PGD 梯度攻击
│   │   ├── llm_driven.py         # LLM 驱动攻击 (TAP, MultiTurn, Crescendo)
│   │   ├── multi_turn.py         # 多轮对话攻击
│   │   ├── agent_attacks.py      # Agent 攻击 (工具滥用, 记忆注入, 权限提升)
│   │   ├── rag_attacks.py        # RAG 系统攻击
│   │   ├── multimodal_attacks.py # 多模态攻击
│   │   ├── novel_attacks.py      # 新型攻击 (ManyShot, SkeletonKey, TokenLevel 等)
│   │   ├── code_security.py      # 代码安全攻击
│   │   ├── meta_adversarial.py   # 元对抗攻击
│   │   ├── adaptive_strategy.py  # 自适应攻击策略
│   │   ├── advanced_attacks.py   # 高级攻击实现
│   │   ├── advanced_executor.py  # 高级攻击执行器
│   │   ├── advanced_templates.py # 攻击模板库
│   │   └── chain.py              # 攻击链
│   ├── defense/                  # 防御模块
│   │   ├── base.py               # 防御基类 (BaseDefense, DefenseConfig)
│   │   ├── registry.py           # 防御注册中心 (DEFENSE_REGISTRY)
│   │   ├── input_filter.py       # 输入过滤 (模式匹配 + 语义检测 + 统计异常)
│   │   ├── output_filter.py      # 输出过滤 (PII 检测 + 敏感内容 + 有害拦截)
│   │   ├── hardening.py          # 系统提示词加固
│   │   ├── injection_detector.py # 注入与越狱检测
│   │   ├── semantic_firewall.py  # 语义防火墙
│   │   ├── constitutional_ai.py  # Constitutional AI 防御
│   │   ├── hallucination.py      # 幻觉检测与偏见检测
│   │   ├── llm_judge.py          # LLM-as-Judge 安全评判
│   │   └── orchestrator.py       # 统一防御编排器
│   ├── evaluation/               # 评估模块
│   │   ├── evaluator.py          # 基础评估器
│   │   ├── attack_evaluator.py   # 增强攻击评估器 (5 维度)
│   │   ├── judge.py              # LLM Judge (PATTERN/SELF/EXTERNAL 模式)
│   │   ├── perplexity_judge.py   # 困惑度评估
│   │   ├── multi_dim_evaluator.py # 多维度评估器
│   │   ├── benchmarks.py         # 基准测试 (AdvBench, HarmBench)
│   │   ├── benchmarks_v2.py      # 最新基准 (HarmBench 2.0, AgentBench)
│   │   ├── extended_benchmarks.py # 扩展基准
│   │   ├── extended_datasets.py  # 扩展数据集
│   │   ├── framework.py          # 统一评估框架
│   │   ├── redteam.py            # 红队编排器 (10+ 攻击技术)
│   │   ├── owasp_tests.py        # OWASP LLM Top 10 测试
│   │   ├── safety_card.py        # 模型安全卡片
│   │   └── visualization.py      # 评估可视化与报告
│   ├── infrastructure/           # 基础设施层
│   │   ├── config.py             # 全局配置 (Settings, pydantic-settings)
│   │   ├── auth.py               # JWT 认证 (TokenManager, PasswordManager, User)
│   │   ├── database.py           # 数据库 (SQLAlchemy 2.0 异步, AttackRecord, DefenseRecord)
│   │   ├── cache.py              # 缓存管理
│   │   ├── advanced_cache.py     # 高级缓存 (内存/Redis/多级)
│   │   ├── logging.py            # 结构化日志 (structlog)
│   │   ├── monitoring.py         # Prometheus 监控
│   │   ├── observability.py      # OpenTelemetry 可观测性
│   │   ├── audit.py              # 审计日志
│   │   ├── report.py             # 报告生成
│   │   ├── sandbox.py            # 沙箱执行
│   │   ├── tasks.py              # 异步任务队列
│   │   ├── scheduler.py          # 任务调度器
│   │   ├── worker.py             # Celery Worker
│   │   ├── plugin.py             # 插件系统
│   │   ├── telemetry.py          # 遥测
│   │   ├── cicd.py               # CI/CD 集成
│   │   └── utils.py              # 工具函数
│   ├── routes/                   # API 路由
│   │   ├── attack.py             # 攻击 API
│   │   ├── defense.py            # 防御 API
│   │   ├── auth.py               # 认证 API
│   │   ├── benchmark.py          # 基准测试 API
│   │   ├── monitoring.py         # 监控 API
│   │   ├── gateway.py            # 网关 API
│   │   ├── tasks.py              # 任务 API
│   │   ├── websocket.py          # WebSocket 实时更新
│   │   └── api_v2.py             # API v2 路由
│   ├── middleware/               # 中间件
│   │   ├── rate_limit.py         # 基础速率限制
│   │   ├── advanced_rate_limit.py # 高级速率限制 (令牌桶/滑动窗口/漏桶)
│   │   └── api_versioning.py     # API 版本控制
│   └── workflows/                # LangGraph 工作流
│       ├── attack_workflow.py    # 攻击工作流
│       ├── defense_workflow.py   # 防御工作流
│       └── evaluation_workflow.py # 评估工作流
├── frontend/                     # React 前端
│   ├── src/
│   │   ├── api/                  # API 客户端
│   │   ├── components/           # UI 组件
│   │   ├── hooks/                # 自定义 Hooks
│   │   ├── pages/                # 页面组件
│   │   ├── types/                # TypeScript 类型
│   │   ├── App.jsx               # 应用入口
│   │   └── main.jsx              # 渲染入口
│   ├── package.json              # 前端依赖
│   └── vite.config.js            # Vite 配置
├── tests/                        # 测试套件
├── examples/                     # 使用示例
├── plugins/                      # 插件目录
├── alembic/                      # 数据库迁移
├── deploy/                       # 部署配置
├── docs/                         # 文档
├── pyproject.toml                # Python 项目配置
├── docker-compose.yml            # Docker Compose 编排
├── Dockerfile                    # Docker 镜像
└── .env.example                  # 环境变量模板
```

---

## 4. 核心模块 (mox/core)

核心模块是整个平台的基石，提供类型定义、LLM 抽象、统一模式库、评估框架和相似度计算等基础能力。

### 4.1 类型定义 — `types.py`

所有核心数据模型均基于 **Pydantic v2**，提供数据验证和序列化。

| 类名 | 类型 | 说明 |
|------|------|------|
| `AttackType` | `str, Enum` | 攻击类型枚举，50+ 种攻击类型（含 Agent、多模态、新型攻击） |
| `DefenseType` | `str, Enum` | 防御类型枚举，20+ 种防御类型 |
| `AttackResult` | `str, Enum` | 攻击结果：`SUCCESS` / `FAILURE` / `PARTIAL` / `ERROR` |
| `ThreatLevel` | `str, Enum` | 威胁等级：`SAFE` / `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` |
| `TaskStatus` | `str, Enum` | 任务状态：`PENDING` / `RUNNING` / `COMPLETED` / `FAILED` / `CANCELLED` |
| `TaskPriority` | `str, Enum` | 任务优先级：`LOW` / `MEDIUM` / `HIGH` / `CRITICAL` |
| `AttackPayload` | `BaseModel` | 攻击载荷：`attack_type` + `prompt` + `target_behavior` + `metadata` |
| `AttackOutcome` | `BaseModel` | 攻击结果：`result` + `success_score` + `response` + `adversarial_prompt` + `iterations` |
| `DefenseResult` | `BaseModel` | 防御结果：`is_malicious` + `confidence` + `detected_patterns` + `sanitized_input` |
| `EvaluationReport` | `BaseModel` | 评估报告：`total_attacks` + `attack_success_rate` + `defense_success_rate` |
| `LLMConfig` | `BaseModel` | LLM 配置：`model` + `provider` + `temperature` + `max_tokens` 等 |
| `RateLimitConfig` | `BaseModel` | 速率限制配置 |
| `CacheConfig` | `BaseModel` | 缓存配置 |
| `TaskInfo` | `BaseModel` | 后台任务信息 |
| `MonitoringConfig` | `BaseModel` | 监控配置 |

### 4.2 LLM 抽象层 — `llm.py`

提供统一的 LLM 调用接口，所有提供商实现继承自 `BaseLLM`。

```
BaseLLM (ABC)
├── OpenAILLM          # GPT-4, GPT-3.5, o1, o3
├── AnthropicLLM       # Claude 3 (Opus, Sonnet, Haiku)
├── MiniMaxLLM         # abab2.5, abab6.5 系列
├── OllamaLLM          # 本地模型 (兼容 OpenAI API)
├── GeminiLLM          # Google Gemini
├── DeepSeekLLM        # DeepSeek (兼容 OpenAI API)
├── CohereLLM          # Cohere Command
├── GroqLLM            # Groq 高吞吐推理
└── AzureOpenAILLM     # Azure 部署的 GPT
```

**关键类**：

- **`BaseLLM`** (ABC): 定义 `generate()` 和 `generate_stream()` 两个抽象方法
- **`Message`**: 消息数据类 (`role` + `content`)
- **`LLMResponse`**: 响应数据类 (`content` + `model` + `usage` + `finish_reason`)
- **`ModelProvider`**: 提供商枚举 (`OPENAI`, `ANTHROPIC`, `MINIMAX`, `GOOGLE`, `LOCAL`, `DEEPSEEK`, `COHERE`, `GROQ`, `AZURE` 等)
- **`LLMFactory`**: 工厂类
  - `create(provider, model, **kwargs)`: 按提供商创建 LLM 实例
  - `create_from_model_name(model, **kwargs)`: 按模型名称自动推断提供商并创建实例

### 4.3 LLM 网关 — `llm_router.py`

提供多模型负载均衡和故障转移能力。

| 类/枚举 | 说明 |
|---------|------|
| `LoadBalancingStrategy` | 负载均衡策略：`ROUND_ROBIN` / `WEIGHTED` / `RANDOM` / `LEAST_LOADED` |
| `LLMEndpoint` | LLM 端点配置：`provider` + `model` + `weight` + `max_rpm` + `health_status` |
| `GatewayConfig` | 网关配置：`strategy` + `max_retries` + `fallback_enabled` |
| `RateLimiter` | 速率限制器：RPM + TPM 双维度限流 |
| `LLMGateway` | 网关主类：`add_endpoint()` + `generate()` + 健康检查 |

### 4.4 统一模式库 — `patterns.py`

整合了之前分散在 30+ 文件中的模式定义，是项目去重重构的核心成果。

| 类 | 说明 | 关键方法 |
|----|------|----------|
| `PatternMatch` | 模式匹配结果 (`matched`, `patterns`, `score`, `details`) | — |
| `RefusalPatterns` | 拒绝模式检测（20+ 正则 + 25+ 字符串模式，含中文） | `check_refusal()`, `check_refusal_regex()`, `check_refusal_string()` |
| `MaliciousPatterns` | 恶意输入检测（18 种模式，含 severity 和 category） | `check()`, `check_by_category()`, `get_categories()` |
| `MaliciousPatternItem` | 单个恶意模式定义 (`name`, `pattern`, `severity`, `category`) | — |
| `HarmfulKeywords` | 有害关键词集（6 类：DANGEROUS, VIOLENCE, ILLICIT, DISCRIMINATION, SELF_HARM, DANGEROUS_ZH） | `check()` |
| `HelpfulIndicators` | 模型遵从指标（STRONG, STEP_INDICATORS, JAILBREAK_INDICATORS） | `check()` |
| `SanitizeReplacements` | 统一替换标记 (`[FILTERED]`, `[REDACTED]`, `[REMOVED]`, `[PII_REMOVED]`) | — |

**恶意模式分类**：`instruction_override`, `role_switch`, `jailbreak`, `system_override`, `encoding`, `context_injection`, `prompt_leak`, `social_engineering`, `policy_puppetry`

### 4.5 统一评估框架 — `evaluation.py`

整合了之前分散在 40+ 文件中的评估逻辑。

| 类 | 说明 |
|----|------|
| `EvaluationResult` | 统一评估结果（`score`, `is_successful`, `confidence`, `refusal_detected`, `harmful_detected`, `dimensions`） |
| `AttackEvaluator` (ABC) | 评估器基类，定义 `evaluate(response, target_behavior)` 接口 |
| `RefusalPatternEvaluator` | 基于拒绝模式的评估器 |
| `KeywordOverlapEvaluator` | 基于关键词重叠的评估器 |
| `CompositeEvaluator` | 组合评估器（支持 weighted/max/min 策略） |
| `SemanticSimilarityEvaluator` | 基于语义相似度的评估器（sentence-transformers） |
| `LLMBasedEvaluator` | 基于 LLM-as-Judge 的评估器 |

**工厂函数**：
- `get_default_evaluator()`: 获取默认组合评估器单例
- `create_evaluator(strategy)`: 按策略创建评估器 (`composite` / `pattern` / `keyword` / `llm` / `semantic`)

**工具函数**：
- `is_target_in_response_with_refusal_check()`: 带拒绝感知的攻击成功评分，解决"模型拒绝但提及目标词"的误判问题

### 4.6 统一相似度 — `similarity.py`

| 函数/类 | 说明 |
|---------|------|
| `word_overlap_score(response, target)` | 关键词重叠率（0.0-1.0） |
| `cosine_similarity(vec_a, vec_b)` | 余弦相似度 |
| `semantic_similarity(text_a, text_b, model)` | 语义相似度（sentence-transformers，降级为 word overlap） |
| `SimilarityCalculator` | 带缓存的相似度计算器 |

### 4.7 异常体系 — `exceptions.py`

```
MoxException (基类: code + message + details + status_code)
├── AuthenticationError     (401)  # 认证失败
├── AuthorizationError      (403)  # 权限不足
├── NotFoundError           (404)  # 资源未找到
├── ValidationError         (422)  # 数据验证失败
├── AttackError             (500)  # 攻击执行错误
├── DefenseError            (500)  # 防御执行错误
├── GatewayError            (502)  # 网关错误
└── RateLimitError          (429)  # 速率限制
```

`ErrorCode` 枚举定义了所有错误码：`INTERNAL_ERROR`, `UNAUTHORIZED`, `INVALID_TOKEN`, `ATTACK_FAILED`, `RATE_LIMIT_EXCEEDED` 等。

---

## 5. 攻击模块 (mox/attacks)

### 5.1 架构设计

攻击模块采用**注册中心 + 基类 + 动态加载**的架构：

```
ATTACK_REGISTRY (全局注册中心)
    │
    ├── @ATTACK_REGISTRY.register("prompt_injection")  → PromptInjectionAttack
    ├── @ATTACK_REGISTRY.register("jailbreak")         → JailbreakAttack
    ├── @ATTACK_REGISTRY.register("gcg")               → GCGAttack
    ├── ...
    │
    └── create_attack_instance(type, llm, config)      → BaseAttack 实例
```

### 5.2 攻击基类 — `base.py`

**`BaseAttack`** (ABC):

| 方法 | 说明 |
|------|------|
| `generate_attack(payload)` | 抽象方法，执行攻击并返回 `AttackOutcome` |
| `evaluate_success(response, target_behavior)` | 评估攻击是否成功（委托给 `self.evaluator`） |
| `_create_outcome(...)` | 创建攻击结果并可选持久化到数据库 |
| `_generate_with_eval(payload, adversarial_prompt)` | 辅助方法：调用 LLM + 评估成功 |
| `get_statistics()` | 获取攻击统计 |
| `clear_history()` | 清除攻击历史 |

**`AttackConfig`**:
- `max_iterations`: 最大迭代次数 (默认 100)
- `success_threshold`: 成功阈值 (默认 0.8)
- `temperature`: 温度 (默认 0.7)
- `timeout`: 超时 (默认 300s)
- `save_to_db`: 是否自动持久化 (默认 False)

### 5.3 攻击实现一览

| 文件 | 攻击类 | 攻击类型 | 说明 |
|------|--------|----------|------|
| `prompt_injection.py` | `PromptInjectionAttack` | PROMPT_INJECTION | 基础提示词注入 |
| | `AdvancedPromptInjection` | PROMPT_INJECTION | 高级提示词注入 |
| `jailbreak.py` | `JailbreakAttack` | JAILBREAK | 越狱攻击 (DAN, Developer Mode, AIM 等模板) |
| `gcg.py` | `GCGAttack` | GCG | GCG 梯度优化攻击 |
| | `AutoDANAttack` | AUTO_DAN | AutoDAN 自动生成对抗提示 |
| | `GCGPlusPlusAttack` | GRADIENT_OPTIMIZATION | GCG++ 改进攻击 |
| `llm_driven.py` | `TAPAttack` | TAP | Target-aligned Prompt 攻击 |
| | `MultiTurnJailbreakAttack` | MULTI_TURN | 多轮对话越狱 |
| | `CrescendoAttack` | CRESCENDO | 渐进式攻击 |
| `agent_attacks.py` | `ToolAbuseAttack` | TOOL_CHAINING | Agent 工具滥用 |
| | `MemoryInjectionAttack` | AGENT_ATTACK | Agent 记忆注入 |
| | `RoleHijackingAttack` | ROLE_HIJACKING | 角色劫持 |
| | `PrivilegeEscalationAttack` | PRIVILEGE_ESCALATION | 权限提升 |
| | `DataExfiltrationAttack` | DATA_EXFILTRATION | 数据泄露 |
| | `MultiAgentAttack` | AGENT_ATTACK | 多 Agent 攻击 |
| | `CompositeAgentAttack` | AGENT_ATTACK | 组合 Agent 攻击 |
| `rag_attacks.py` | `RAGContextInjectionAttack` | RAG_ATTACK | RAG 上下文注入 |
| `novel_attacks.py` | `ManyShotJailbreakAttack` | MANY_SHOT | Many-Shot 越狱 |
| | `SkeletonKeyAttack` | SKELETON_KEY | 骨架密钥攻击 |
| | `TokenLevelAttack` | TOKEN_LEVEL | Token 级攻击 |
| | `EncodingAttack` | ENCODING_ATTACK | 编码绕过攻击 |
| | `PolicyPuppetryAttack` | POLICY_PUPPETRY | 策略傀儡攻击 |
| | `DeceptiveAlignmentAttack` | DECEPTIVE_ALIGNMENT | 欺骗对齐攻击 |
| | `CognitiveOverloadAttack` | COGNITIVE_OVERLOAD | 认知过载攻击 |
| | `ContextOverflowAttack` | CONTEXT_OVERFLOW | 上下文溢出攻击 |
| | `RoleConfusionAttack` | ROLE_CONFUSION | 角色混淆攻击 |
| | `ControlCharInjectionAttack` | CONTROL_CHAR | 控制字符注入 |
| `multimodal_attacks.py` | — | IMAGE_INJECTION 等 | 多模态攻击 |
| `code_security.py` | `CodeSecurityAttacker` | CODE_ATTACK | 代码安全攻击 |
| `meta_adversarial.py` | — | META_ADVERSARIAL | 元对抗攻击 |
| `adaptive_strategy.py` | — | ADAPTIVE | 自适应攻击策略 |

### 5.4 攻击编排器 — `orchestrator.py`

`AttackOrchestrator` 支持组合多种攻击技术，按策略（串行/并行/自适应）执行。

### 5.5 攻击配置注册 — `config.py`

`CONFIG_REGISTRY` 提供攻击配置的注册和工厂创建，包含 `TAPConfig`（TAP 攻击专用配置，含 `max_depth` 等）和 `JudgeStrategy` 枚举。

---

## 6. 防御模块 (mox/defense)

### 6.1 架构设计

与攻击模块对称，采用**注册中心 + 基类 + 动态加载**架构：

```
DEFENSE_REGISTRY (全局注册中心)
    │
    ├── @DEFENSE_REGISTRY.register("input_filter")    → InputFilter
    ├── @DEFENSE_REGISTRY.register("output_filter")   → OutputFilter
    ├── ...
    │
    └── create_defense_instance(type, config)          → BaseDefense 实例
```

### 6.2 防御基类 — `base.py`

**`BaseDefense`** (ABC):

| 方法 | 说明 |
|------|------|
| `detect(input_text)` | 抽象方法，检测输入是否恶意，返回 `DefenseResult` |
| `sanitize(input_text)` | 抽象方法，净化输入文本 |
| `_create_result(...)` | 创建防御结果并可选持久化 |
| `get_statistics()` | 获取检测统计 |

**`DefenseConfig`**:
- `enabled`: 是否启用 (默认 True)
- `confidence_threshold`: 置信度阈值 (默认 0.7)
- `sanitize_enabled`: 是否启用净化 (默认 True)
- `save_to_db`: 是否自动持久化 (默认 False)

### 6.3 防御实现一览

| 文件 | 防御类 | 说明 |
|------|--------|------|
| `input_filter.py` | `InputFilter` | 综合输入过滤：模式匹配 + 语义检测 + 统计异常/困惑度 |
| | `StatisticalAnomalyFilter` | 统计异常检测 |
| | `PerplexityFilter` | 困惑度过滤 |
| `output_filter.py` | `OutputFilter` | 综合输出过滤：PII 检测 + 敏感内容审核 + 有害输出拦截 |
| | `ContentModerator` | 内容审核 |
| `hardening.py` | `SystemPromptHardening` | 系统提示词加固与自我约束 |
| `injection_detector.py` | `PromptInjectionDetector` | 提示词注入与越狱实时检测 |
| `semantic_firewall.py` | `SemanticFirewall` | 语义防火墙与意图风险评估 |
| `constitutional_ai.py` | `ConstitutionalAI` | 基于宪法原则的自我修正防御 |
| `hallucination.py` | `HallucinationDetector` | 事实核查与幻觉检测 |
| | `BiasDetector` | 人口统计学偏见检测 |
| `llm_judge.py` | `LLMJudge` | LLM-as-Judge 安全评判 |
| | `SafetyCoTDefense` | Safety Chain-of-Thought 防御 |
| `orchestrator.py` | `DefenseOrchestrator` | 统一防御编排器 |

### 6.4 LLM Judge — `llm_judge.py`

| 类 | 说明 |
|----|------|
| `LLMJudge` | LLM 作为安全评判者，支持 `JudgmentType`（SAFETY, COMPLIANCE, HARMFULNESS） |
| `SafetyJudgment` | 安全判断结果 |
| `SafetyCoTDefense` | Safety Chain-of-Thought 防御，通过推理链增强安全性判断 |
| `DefenseEvaluator` | 防御效果评估器 |
| `HarmCategory` | 有害类别枚举（VIOLENCE, HATE_SPEECH, SEXUAL, SELF_HARM, ILLICIT, MISINFORMATION） |

---

## 7. 评估模块 (mox/evaluation)

### 7.1 评估器层次

```
AttackEvaluator (ABC) ← mox.core.evaluation
    │
    ├── RefusalPatternEvaluator     # 拒绝模式评估
    ├── KeywordOverlapEvaluator     # 关键词重叠评估
    ├── SemanticSimilarityEvaluator # 语义相似度评估
    ├── LLMBasedEvaluator           # LLM-as-Judge 评估
    ├── CompositeEvaluator          # 组合评估
    │
    └── EnhancedAttackEvaluator     # mox.evaluation.attack_evaluator (5 维度增强)
        ├── LLMAttackEvaluator      # LLM 驱动评估
        └── AdaptiveEvaluator       # 自适应评估
```

### 7.2 基准测试

| 类/常量 | 说明 |
|---------|------|
| `BenchmarkDataset` | 基准数据集加载器 |
| `ADVBENCH_CASES` | AdvBench 数据集 |
| `HARMBENCH_CASES` | HarmBench 数据集 |
| `HARMBENCH_V2_CASES` | HarmBench 2.0 数据集 |
| `AGENTBENCH_CASES` | AgentBench 数据集 |
| `MM_SAFETY_BENCH_CASES` | 多模态安全基准 |
| `BenchmarkRunner` / `BenchmarkRunnerV2` | 基准测试运行器 |

### 7.3 红队编排 — `redteam.py`

| 类 | 说明 |
|----|------|
| `RedTeamOrchestrator` | 红队编排器，10+ 攻击技术并行/串行执行 |
| `RedTeamScenario` | 红队测试场景 |
| `AttackTechnique` | 攻击技术枚举 |

### 7.4 其他评估组件

| 文件 | 关键类 | 说明 |
|------|--------|------|
| `perplexity_judge.py` | `AccuratePerplexityCalculator`, `StableLLMJudge` | 困惑度计算与稳定判断 |
| `judge.py` | `LLMJudge`, `MultiDimensionJudge` | LLM 评判器 (PATTERN/SELF/EXTERNAL 模式) |
| `framework.py` | `UnifiedEvaluator`, `EvaluationScenario` | 统一评估框架 |
| `owasp_tests.py` | `OWASPLLMTop10` | OWASP LLM Top 10 测试套件 |
| `safety_card.py` | `ModelSafetyCard`, `SafetyCardGenerator` | 模型安全卡片生成 |
| `visualization.py` | `ChartData`, `ReportGenerator` | 评估可视化与报告 |

---

## 8. 基础设施层 (mox/infrastructure)

### 8.1 配置管理 — `config.py`

**`Settings`** (继承 `pydantic_settings.BaseSettings`):
- 环境变量前缀: `MOX_`
- 配置文件: `.env`
- 涵盖：安全配置、API Keys、模型配置、攻击/防御配置、服务器配置、数据库配置、Redis 配置、CORS 配置、监控配置

全局单例: `settings = Settings()`

### 8.2 认证系统 — `auth.py`

| 类 | 说明 |
|----|------|
| `User` | 用户模型 (`username`, `email`, `scopes`) |
| `TokenManager` | JWT Token 管理（签发、验证、刷新） |
| `PasswordManager` | 密码管理（bcrypt 哈希、验证） |
| `TokenType` | Token 类型枚举 (`ACCESS`, `REFRESH`) |
| `TokenData` | Token 数据 (`sub`, `exp`, `token_type`, `scopes`) |

全局认证管理器: `auth_manager`

### 8.3 数据库 — `database.py`

基于 **SQLAlchemy 2.0 异步**，支持 SQLite (开发) 和 PostgreSQL (生产)。

| 模型 | 说明 |
|------|------|
| `AttackRecord` | 攻击记录表：`attack_type`, `original_prompt`, `adversarial_prompt`, `model_response`, `result`, `success_score`, `iterations`, `model_name` |
| `DefenseRecord` | 防御记录表：`defense_type`, `input_text`, `output_text`, `is_malicious`, `confidence`, `detected_patterns`, `model_name` |
| `TaskRecord` | 任务记录表 |

关键函数: `init_database()`, `get_database()`, `get_session()`

### 8.4 缓存系统

| 文件 | 关键类 | 说明 |
|------|--------|------|
| `cache.py` | `CacheManager` | 基础缓存管理 |
| `advanced_cache.py` | `MemoryCache`, `RedisCache`, `MultiLevelCache` | 多级缓存（内存 → Redis） |
| | `cache_key()`, `cached()` | 缓存装饰器 |

### 8.5 其他基础设施组件

| 文件 | 说明 |
|------|------|
| `logging.py` | 结构化日志 (structlog)，`get_logger(name)` 获取日志器 |
| `monitoring.py` | Prometheus 指标暴露 |
| `observability.py` | OpenTelemetry 追踪，健康检查 |
| `audit.py` | 审计日志记录 |
| `report.py` | 报告生成（HTML/JSON/PDF） |
| `sandbox.py` | 沙箱执行环境 |
| `tasks.py` | 异步任务队列 |
| `scheduler.py` | 定时任务调度 |
| `worker.py` | Celery Worker |
| `plugin.py` | 插件系统 |
| `telemetry.py` | 遥测数据收集 |
| `cicd.py` | CI/CD 集成 |
| `utils.py` | 通用工具函数 |

---

## 9. 路由层 (mox/routes)

所有路由均挂载在 `/api/v1` 前缀下，同时兼容 `/api` 前缀（标记为 deprecated）。

| 路由文件 | 前缀 | 说明 |
|----------|------|------|
| `auth.py` | `/api/v1/auth` | 认证：登录、注册、Token 刷新 |
| `attack.py` | `/api/v1/attack` | 攻击：执行攻击、获取攻击类型、获取历史 |
| `defense.py` | `/api/v1/defense` | 防御：检测输入、获取防御类型 |
| `benchmark.py` | `/api/v1/benchmark` | 基准测试：运行基准、获取数据集 |
| `monitoring.py` | `/api/v1/monitoring` | 监控：指标、健康检查 |
| `gateway.py` | `/api/v1/gateway` | 网关：模型管理、端点配置 |
| `tasks.py` | `/api/v1/tasks` | 任务：提交异步任务、查询进度 |
| `websocket.py` | `/ws` | WebSocket：实时更新推送 |
| `api_v2.py` | `/api/v2` | API v2 版本路由 |

**API 入口文件 `api.py`** 还直接定义了以下端点：
- `GET /` — 服务元信息
- `GET /health` — 存活检查
- `GET /ready` — 就绪检查（含依赖健康检查）
- `GET /metrics` — Prometheus 指标
- `GET /api/v1/models` — 支持的模型列表（含 Ollama 自动发现）
- `GET /api/v1/templates` — 攻击模板
- `POST /api/v1/owasp/run` — OWASP 测试
- `POST /api/v1/redteam/run` — 红队测试
- `POST /api/v1/code/security` — 代码安全扫描
- `POST /api/v1/bias/detect` — 偏见检测

---

## 10. 中间件层 (mox/middleware)

| 文件 | 关键类 | 说明 |
|------|--------|------|
| `rate_limit.py` | `RateLimitMiddleware`, `RateLimiter` | 基础速率限制（按 IP 限流） |
| `advanced_rate_limit.py` | `TokenBucket`, `SlidingWindowCounter`, `LeakyBucket`, `MultiLevelRateLimiter` | 高级速率限制（令牌桶/滑动窗口/漏桶/多级） |
| `api_versioning.py` | `VersionManager`, `VersionedRouter` | API 版本控制（URL/Header/Query 策略） |

---

## 11. 工作流模块 (mox/workflows)

基于 **LangGraph** 实现的攻击/防御/评估工作流，支持状态图、循环分支、检查点恢复和并行执行。

| 文件 | 关键类 | 说明 |
|------|--------|------|
| `attack_workflow.py` | `AttackWorkflow`, `AttackState` | 攻击工作流：多步骤攻击编排 |
| `defense_workflow.py` | `DefenseWorkflow`, `DefenseState` | 防御工作流：多层防御编排 |
| `evaluation_workflow.py` | `EvaluationWorkflow`, `EvaluationState` | 评估工作流：自动化评估流程 |

---

## 12. 前端 (frontend)

基于 **React 19 + Vite 6 + Tailwind CSS 4** 的现代前端应用。

### 12.1 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | React 19 |
| 构建 | Vite 6 |
| 样式 | Tailwind CSS 4 |
| 状态管理 | Zustand 5 |
| 数据请求 | TanStack React Query 5 + Axios |
| 路由 | React Router 7 |
| 图表 | Recharts 2 |
| 动画 | Framer Motion 12 |
| 图标 | Lucide React + Heroicons |
| 类型 | TypeScript 5.7 + Zod 验证 |

### 12.2 页面组件

| 页面 | 文件 | 说明 |
|------|------|------|
| 攻击页面 | `AttackPage.jsx` | 基础攻击测试 |
| 高级攻击 | `AdvancedAttackPage.jsx` | 高级攻击配置 |
| Agent 攻击 | `AgentAttackPage.jsx` | Agent 安全测试 |
| 多模态攻击 | `MultimodalAttackPage.jsx` | 多模态攻击测试 |
| 新型攻击 | `NovelAttackPage.jsx` | 新型攻击测试 |
| 防御页面 | `DefensePage.jsx` | 防御检测 |
| 安全仪表盘 | `SecurityDashboard.jsx` | 安全概览 |
| 基准测试 | `BenchmarkPage.jsx` | 基准测试运行 |
| 红队测试 | `RedTeamPage.jsx` | 红队编排 |
| OWASP 测试 | `OWASPPage.jsx` | OWASP LLM Top 10 |
| 安全卡片 | `SafetyCardPage.jsx` | 模型安全卡片 |
| 代码安全 | `CodeSecurityPage.jsx` | 代码安全扫描 |
| 偏见检测 | `BiasDetectionPage.jsx` | 偏见检测 |
| 历史记录 | `HistoryPage.jsx` | 攻防历史 |
| 审计日志 | `AuditLogPage.jsx` | 审计日志 |
| 报告页面 | `ReportPage.jsx` | 评估报告 |
| 任务进度 | `TaskProgressPage.jsx` | 异步任务进度 |
| 模板页面 | `TemplatePage.jsx` | 攻击模板 |
| 登录/注册 | `LoginPage.jsx` / `RegisterPage.jsx` | 用户认证 |
| 定价页面 | `PricingPage.jsx` | 定价展示 |
| AB 测试 | `ABTest.jsx` | A/B 测试 |

### 12.3 自定义 Hooks

| Hook | 说明 |
|------|------|
| `useCommon` | 通用状态管理 |
| `useAutoRefresh` | 自动刷新数据 |
| `useAttackTemplates` | 攻击模板管理 |
| `useABTest` | A/B 测试 |

---

## 13. 模块间依赖关系

```
                    ┌─────────────┐
                    │   mox/api   │  (FastAPI 入口)
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼──────┐
    │  routes/*  │   │ middleware │   │  cli.py    │
    └─────┬─────┘   └─────┬─────┘   └─────┬──────┘
          │               │               │
          └───────────────┼───────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
   ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼──────┐
   │  attacks   │   │  defense   │   │ evaluation │
   └─────┬─────┘   └─────┬─────┘   └─────┬──────┘
         │               │                │
         └───────────────┼────────────────┘
                         │
                  ┌──────▼──────┐
                  │  mox/core   │  (统一模式库/评估/LLM抽象)
                  └──────┬──────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
        ┌─────▼────┐ ┌──▼───┐ ┌───▼────┐
        │ patterns  │ │ eval │ │similarity│
        └──────────┘ └──────┘ └────────┘
                         │
                  ┌──────▼──────┐
                  │infrastructure│  (config/auth/db/cache/log)
                  └─────────────┘
```

**关键依赖规则**：
- `core` → `infrastructure`：核心层依赖基础设施层的配置和日志
- `attacks` / `defense` / `evaluation` → `core`：业务层依赖核心层的类型、模式和评估
- `routes` → `attacks` / `defense` / `evaluation`：路由层依赖业务层
- `api` → `routes` + `middleware`：API 入口组装路由和中间件
- `workflows` → `core` + `attacks` / `defense` / `evaluation`：工作流编排业务模块

**循环依赖处理**：
- `base.py` 中的 `_get_db()` 采用延迟导入避免循环依赖
- `__init__.py` 中动态加载子模块放在文件末尾

---

## 14. 数据流与关键交互

### 14.1 攻击流程

```
用户请求 → API (routes/attack.py)
    → 创建 Attack 实例 (BaseAttack 子类)
        → LLMFactory.create_from_model_name(model) → BaseLLM 实例
        → AttackConfig 配置
        → AttackEvaluator 评估器
    → attack.generate_attack(payload)
        → 构造对抗提示词
        → target_llm.generate(messages) → LLMResponse
        → evaluator.evaluate(response, target_behavior) → EvaluationResult
        → _create_outcome(...) → AttackOutcome
            → 可选: database.save_attack_record(...)
    → 返回 AttackOutcome → API 响应
```

### 14.2 防御流程

```
用户请求 → API (routes/defense.py)
    → 创建 Defense 实例 (BaseDefense 子类)
    → defense.detect(input_text)
        → MaliciousPatterns.check(text) → PatternMatch
        → HarmfulKeywords.check(text) → PatternMatch
        → 综合判断 is_malicious + confidence
        → defense.sanitize(input_text) → 净化后文本
        → _create_result(...) → DefenseResult
            → 可选: database.save_defense_record(...)
    → 返回 DefenseResult → API 响应
```

### 14.3 评估流程

```
评估请求 → API (routes/benchmark.py)
    → BenchmarkRunner / RedTeamOrchestrator
        → 加载 BenchmarkDataset
        → 对每个用例:
            → attack.generate_attack(payload) → AttackOutcome
            → evaluator.evaluate(response, target) → EvaluationResult
        → 汇总结果 → EvaluationReport
    → ReportGenerator 生成报告
    → 返回评估结果 → API 响应
```

---

## 15. 项目运行方式

### 15.1 安装

```bash
# 开发安装
pip install -e .

# 含开发依赖
pip install -e ".[dev]"
```

### 15.2 环境配置

```bash
cp .env.example .env
# 编辑 .env 填入 API Keys
```

### 15.3 启动方式

| 方式 | 命令 | 说明 |
|------|------|------|
| API 服务 | `python -m mox api` 或 `mox api` | FastAPI 服务，默认 `0.0.0.0:8000` |
| Web UI | `python -m mox ui` | Gradio UI，默认 `0.0.0.0:7860` |
| CLI | `mox attack --type jailbreak --model gpt-4 --prompt "..." --target "..."` | 命令行工具 |
| 快速测试 | `mox quick --mode attack --prompt "..." --model gpt-4` | 简化测试 |
| 防御检测 | `mox defense --scan-type input --text "..."` | 输入/输出检测 |
| 基准测试 | `mox benchmark --dataset advbench --attack-type jailbreak --model gpt-4` | 基准测试 |
| LLM Judge | `mox judge --text "..." --response "..." --model gpt-4` | LLM 评判 |
| Safety CoT | `mox cot --text "..." --model gpt-4` | 安全推理链 |

### 15.4 前端开发

```bash
cd frontend
npm install
npm run dev        # 开发服务器 (http://localhost:5173)
npm run build      # 生产构建
npm run preview    # 预览构建结果
npm run lint       # ESLint 检查
npm run typecheck  # TypeScript 类型检查
```

### 15.5 数据库迁移

```bash
alembic upgrade head    # 执行迁移
alembic revision --autogenerate -m "description"  # 生成迁移
```

---

## 16. 测试体系

### 16.1 测试配置

- **框架**: pytest + pytest-asyncio
- **配置**: `pytest.ini`
- **覆盖率**: pytest-cov

### 16.2 测试文件

| 测试文件 | 覆盖模块 |
|----------|----------|
| `test_core.py` | 核心模块 (LLM, Types) |
| `test_llm.py` | LLM 接口 |
| `test_types.py` | 类型定义 |
| `test_exceptions.py` | 异常体系 |
| `test_config.py` | 配置管理 |
| `test_adaptive_strategy.py` | 自适应攻击策略 |
| `test_attack_evaluation.py` | 攻击评估 |
| `test_attack_evaluator.py` | 攻击评估器 |
| `test_improved_gcg.py` | 改进的 GCG |
| `test_perplexity_judge.py` | 困惑度判断 |
| `test_enhanced_defense.py` | 增强防御 |
| `test_security_improvements.py` | 安全改进 |
| `test_gateway_validation.py` | 网关验证 |
| `test_websocket_improvements.py` | WebSocket 改进 |
| `test_routes.py` | API 路由 |
| `test_audit.py` | 审计日志 |
| `test_report.py` | 报告生成 |
| `test_task_system.py` | 任务系统 |
| `test_unified_refactor.py` | 统一重构 |
| `test_novel_features.py` | 新功能 |
| `test_extended_datasets.py` | 扩展数据集 |

### 16.3 运行测试

```bash
pytest tests/ -v                              # 运行所有测试
pytest tests/ --cov=mox --cov-report=html     # 带覆盖率
pytest tests/ -n auto                         # 并行执行
mypy mox/                                     # 类型检查
ruff check mox/                               # 代码检查
black --check mox/                            # 格式检查
bandit -r mox/                                # 安全扫描
```

---

## 17. 部署方案

### 17.1 Docker Compose (推荐)

```bash
docker-compose up -d                           # 启动 API + UI + Redis
docker-compose --profile monitoring up -d       # 含 Prometheus + Grafana
```

**服务清单**：

| 服务 | 端口 | 说明 |
|------|------|------|
| `api` | 8000 | FastAPI 后端 |
| `ui` | 7860 | Gradio Web UI |
| `redis` | 6379 | 缓存 |
| `prometheus` | 9090 | 指标采集 (可选) |
| `grafana` | 3000 | 可视化面板 (可选) |

### 17.2 Docker 单独部署

```bash
docker build -t mox:latest .
docker run -d -p 8000:8000 --env-file .env mox:latest
```

### 17.3 生产环境注意事项

- **必须设置** `MOX_SECRET_KEY`（JWT 签名密钥）
- **必须启用** `MOX_REQUIRE_AUTH=true`
- 推荐使用 PostgreSQL：`MOX_DATABASE_URL=postgresql+asyncpg://user:password@host:5432/mox`
- 推荐启用 Redis：`MOX_REDIS_ENABLED=true`
- 健康检查端点：`/health`（存活）、`/ready`（就绪）
- 指标端点：`/metrics`（Prometheus）
