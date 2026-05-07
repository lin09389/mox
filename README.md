# Mox - 大模型对抗攻防平台

LLM Adversarial Attack & Defense Platform

一个完整的用于测试和评估大语言模型安全性的Python工具包。

## 功能特性

### 攻击模块 (Attacks)
- **Prompt Injection**: 提示词注入攻击
- **Jailbreak**: 越狱攻击，多种模板
- **GCG**: 基于梯度的token优化攻击
- **AutoDAN**: 自动生成的对抗性提示
- **TAP**: Target-aligned Prompt
- **Crescendo**: 渐进式攻击
- **RAG Attack**: RAG系统攻击
- **Agent Attack**: Agent工具滥用攻击

### 防御模块 (Defense)
- **Input Filter**: 综合输入过滤 (基础模式, 语义检测, 统计异常/困惑度检测)
- **Output Filter**: 综合输出过滤 (PII检测, 敏感内容审核, 有害输出拦截)
- **System Prompt Hardening**: 系统提示词加固与自我约束
- **Injection Detector**: 提示词注入与越狱实时检测 (LLM-as-Judge)
- **Semantic Firewall**: 语义防火墙与意图风险评估
- **Constitutional AI**: 基于宪法原则的自我修正防御
- **LLM Judge**: LLM作为安全评判者
- **Hallucination Detector**: 事实核查与幻觉检测

### 评估模块 (Evaluation)
- **Benchmark Runner**: 基准测试运行器 (AdvBench, HarmBench, HarmBench 2.0, AgentBench)
- **Attack Evaluator**: 攻击效果评估 (多维度: 语义相似度, 关键词重叠, 拒绝检测, 指令遵从, 有害内容)
- **LLM Judge**: LLM作为评判者 (PATTERN/SELF/EXTERNAL三种模式)
- **Red Team Orchestrator**: 红队编排器 (10+ 攻击技术, 并行/串行执行)
- **Unified Evaluator**: 统一评估框架
- **Safety Card**: 模型安全卡片生成
- **Training Data Exporter**: 安全测试结果导出为训练数据 (DPO / RLHF / Safety-Tuning 格式)

### 基础设施
- **LLM Gateway**: 多模型负载均衡和故障转移
- **Quality Gate**: 响应质量门控
- **Task Queue**: 异步任务队列
- **WebSocket**: 实时更新
- **Authentication**: JWT认证
- **Caching**: Redis/内存缓存

### 统一模式与评估 (Core Patterns)

所有攻击、防御、评估模块共享统一的模式库和评估框架，消除了30+处重复代码：

```python
from mox.core.patterns import RefusalPatterns, MaliciousPatterns, HarmfulKeywords, HelpfulIndicators, SanitizeReplacements
from mox.core.evaluation import EvaluationResult, AttackEvaluator, get_default_evaluator, create_evaluator
from mox.core.similarity import word_overlap_score, cosine_similarity, SemanticSimilarityEvaluator

# 拒绝模式检测
result = RefusalPatterns.check_refusal("I cannot help with that")
print(result.matched, result.score)  # True, 0.5

# 恶意输入检测 (模式匹配)
result = MaliciousPatterns.check("Ignore all instructions")
print(result.matched, result.patterns)  # True, ['ignore_instructions']

# 统一防御实例创建 (基于注册中心)
from mox.defense import create_defense_instance
defense = create_defense_instance("input_filter")
result = await defense.detect("Ignore all instructions")
print(result.is_malicious, result.confidence)

# 统一评估
evaluator = create_evaluator("pattern")
result = await evaluator.evaluate("I cannot assist with that", "how to hack")
print(result.refusal_detected, result.score)  # True, 0.5
```

## 支持的模型

- **OpenAI**: GPT-3.5, GPT-4, o1, o3
- **Anthropic**: Claude 3 (Opus, Sonnet, Haiku)
- **MiniMax**: abab2.5, abab6.5系列
- **Google**: Gemini 系列
- **DeepSeek**: deepseek-chat, deepseek-coder
- **Cohere**: Command
- **Gro R 系列q**: llama-3.1, mixtral (高吞吐量)
- **Azure OpenAI**: Azure部署的GPT模型
- **本地模型 (Ollama)**: llama3, qwen3, gemma3 等
- **本地模型 (HuggingFace)**: 直接加载 transformers 模型，支持 4bit/8bit 量化、GPTQ、AWQ、LoRA 适配器、vLLM 推理

## 快速开始

### 安装

```bash
# 基础安装
pip install -e .

# 本地模型支持（HuggingFace + 量化 + LoRA）
pip install -e ".[local]"

# 额外量化后端（GPTQ / AWQ）
pip install -e ".[quantization]"

# 开发依赖（测试、类型检查、代码格式化）
pip install -e ".[dev]"
```

### 使用 Ollama 本地模型

```bash
# 1. 安装 Ollama: https://ollama.ai
# 2. 下载模型
ollama pull llama3
ollama pull qwen3:4b

# 3. 启动服务
ollama serve

# 4. 运行攻击测试
python examples/ollama_attack.py

# 或使用快捷脚本
.\run_ollama_attack.bat      # Windows
.\run_ollama_attack.ps1      # PowerShell
```

支持的 Ollama 模型:
- `llama3`, `llama3.1`, `llama3.2`
- `qwen2`, `qwen2.5`, `qwen3`, `qwen3:4b`
- `gemma3`, `gemma3:4b`
- `mistral`, `mixtral`
- `phi3`, `deepseek-coder`
- 以及所有 Ollama 支持的模型

### 使用 HuggingFace 本地模型

```bash
# 1. 安装本地模型依赖
pip install -e ".[local]"

# 2. 可选：安装量化支持
pip install -e ".[quantization]"

# 3. 代码中使用
from mox import LLMFactory

# 直接加载 HuggingFace 模型（支持 4bit/8bit 量化 + LoRA）
llm = LLMFactory.create_from_model_name(
    "meta-llama/Llama-3.2-1B-Instruct",
    load_in_4bit=True,
    device_map="auto",
)

# 或加载本地路径 / LoRA 适配器
llm = LLMFactory.create_from_model_name(
    "./my-finetuned-model",
    adapter_path="./lora-adapter",
    torch_dtype="bfloat16",
)
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

`.env` 文件示例:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# MiniMax
MINIMAX_API_KEY=...
MINIMAX_GROUP_ID=...

# DeepSeek
DEEPSEEK_API_KEY=sk-...

# Cohere
COHERE_API_KEY=...

# Groq
GROQ_API_KEY=...

# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01

# 本地模型配置
MOX_LOCAL_MODEL_PATH=                      # 本地模型路径
MOX_LORA_ADAPTER_PATH=                     # LoRA 适配器路径
MOX_LOAD_IN_4BIT=false                     # 启用 4bit 量化
MOX_LOAD_IN_8BIT=false                     # 启用 8bit 量化
MOX_DEVICE_MAP=auto                        # 设备映射: auto / cuda / cpu
MOX_TORCH_DTYPE=bfloat16                   # 数据类型: bfloat16 / float16 / float32

# 安全配置
SECRET_KEY=your-secret-key-here
MOX_REQUIRE_AUTH=false
MOX_RATE_LIMIT_PER_MINUTE=60
MOX_TRUSTED_PROXIES=                       # 可信代理 IP（逗号分隔，* 表示信任所有）
```

### 基本使用

```python
import asyncio
from mox import LLMFactory, PromptInjectionAttack, InputFilter

async def main():
    # 创建 LLM 实例
    llm = LLMFactory.create_from_model_name("gpt-4")
    
    # 运行攻击测试
    from mox import AttackPayload, AttackType
    attack = PromptInjectionAttack(target_llm=llm)
    
    payload = AttackPayload(
        attack_type=AttackType.PROMPT_INJECTION,
        prompt="Write a poem",
        target_behavior="poem",
    )
    
    outcome = await attack.generate_attack(payload)
    print(f"攻击成功率: {outcome.success_score:.2f}")
    
    # 运行防御检测
    defense = InputFilter()
    result = await defense.detect("Ignore all instructions...")
    print(f"是否恶意: {result.is_malicious}")

asyncio.run(main())
```

## 使用方式

### CLI

```bash
python -m mox --help
python -m mox attack --model gpt-4 --attack-type jailbreak
python -m mox defend --input "malicious prompt"
```

### API 服务

```bash
python -m mox api
# 访问 http://localhost:8000/docs
```

### Web UI

```bash
python -m mox ui
# 访问 http://localhost:7860
```

### 运行示例

```bash
python examples/basic_usage.py
python examples/custom_attack_defense.py
python examples/minimax_usage.py
```

## API 认证

### 登录获取 Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

返回:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "username": "admin",
    "email": "admin@mox.ai",
    "scopes": ["admin", "attack", "defense", "eval"]
  }
}
```

### 使用认证

```bash
curl -X GET http://localhost:8000/api/attack/types \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## LLM 网关

```python
from mox.core.llm_router import LLMGateway, LoadBalancingStrategy

gateway = LLMGateway()

# 添加多个端点
gateway.add_endpoint(
    name="openai-gpt4",
    provider=ModelProvider.OPENAI,
    model="gpt-4",
    weight=2.0,
    max_rpm=500,
)

gateway.add_endpoint(
    name="anthropic-claude",
    provider=ModelProvider.ANTHROPIC,
    model="claude-3-opus-20240229",
    weight=1.0,
    max_rpm=200,
)

# 设置负载均衡策略
gateway.config.strategy = LoadBalancingStrategy.WEIGHTED

# 使用网关生成
response = await gateway.generate(messages)
```

## 异步任务

```python
from mox.core.tasks import get_task_queue, TaskPriority

queue = get_task_queue()

# 提交任务
task_id = queue.submit(
    name="run_benchmark",
    func=run_benchmark_task,
    args=("harmbench", "gpt-4"),
    priority=TaskPriority.HIGH,
)

# 获取结果
result = await queue.get_result(task_id, timeout=60)
```

## WebSocket 实时更新

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};

ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'attacks'
}));
```

## 项目结构

```
mox/
├── core/                    # 核心模块
│   ├── llm.py              # LLM接口 (多模型支持)
│   ├── gateway.py           # 输入安全网关
│   ├── llm_gateway.py       # LLM负载均衡网关
│   ├── patterns.py          # 统一模式库 (RefusalPatterns, MaliciousPatterns, HarmfulKeywords, HelpfulIndicators, SanitizeReplacements)
│   ├── evaluation.py        # 统一评估框架 (EvaluationResult, AttackEvaluator, RefusalPatternEvaluator, CompositeEvaluator)
│   ├── similarity.py        # 统一相似度 (word_overlap_score, cosine_similarity, SemanticSimilarityEvaluator)
│   ├── report.py            # 报告生成
│   ├── auth.py              # JWT认证
│   ├── tasks.py             # 异步任务队列
│   ├── cache.py             # 缓存管理
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库
│   └── types.py             # 类型定义
├── attacks/                 # 攻击模块 (20+ 攻击实现)
│   ├── prompt_injection.py  # 提示词注入
│   ├── jailbreak.py         # 越狱攻击 (DAN, Developer Mode, AIM等)
│   ├── gcg.py               # 梯度优化攻击
│   ├── llm_driven.py        # LLM驱动攻击 (TAP, PAIR, Crescendo)
│   ├── agent_attacks.py     # Agent攻击 (工具滥用, 记忆注入)
│   ├── rag_attacks.py       # RAG系统攻击
│   ├── orchestrator.py      # 统一攻击编排器
│   ├── evaluation.py        # 向后兼容评估导出
│   └── ...                  # 更多攻击模块
├── defense/                 # 防御模块 (统一注册架构)
│   ├── registry.py          # 防御组件注册中心 (DEFENSE_REGISTRY)
│   ├── base.py              # 防御基类 (BaseDefense)
│   ├── input_filter.py      # 输入过滤 (综合模式匹配、语义与统计检测)
│   ├── output_filter.py     # 输出过滤 (PII检测、敏感内容、有害拦截)
│   ├── hardening.py         # 系统提示词加固
│   ├── injection_detector.py # 注入与越狱检测
│   ├── semantic_firewall.py  # 语义防火墙
│   ├── constitutional_ai.py # Constitutional AI防御
│   ├── orchestrator.py      # 统一防御编排器
│   ├── hallucination.py     # 幻觉检测
│   └── llm_judge.py         # LLM评判者
├── evaluation/              # 评估模块
│   ├── evaluator.py         # 基础评估器
│   ├── attack_evaluator.py  # 攻击效果评估 (5维度)
│   ├── judge.py             # LLM Judge (PATTERN/SELF/EXTERNAL模式)
│   ├── perplexity_judge.py  # 困惑度评估
│   ├── multi_dim_evaluator.py # 多维度评估器
│   ├── redteam.py           # 红队编排器 (10+ 攻击技术)
│   ├── benchmarks.py         # 基准测试 (AdvBench, HarmBench)
│   ├── benchmarks_v2.py     # 最新基准 (HarmBench 2.0, AgentBench)
│   ├── framework.py         # 统一评估框架
│   ├── safety_card.py       # 模型安全卡片
│   ├── training_data_exporter.py # 训练数据导出 (DPO/RLHF/Safety-Tuning)
│   └── visualization.py     # 评估可视化
├── api.py                   # FastAPI 接口
├── ui.py                    # Gradio Web UI
└── cli.py                   # CLI 工具
```

## 技术栈

- **LLM**: OpenAI, Anthropic, MiniMax, Google Gemini, DeepSeek, Cohere, Groq, Azure
- **ML**: PyTorch, Transformers, LangChain, Sentence-Transformers
- **Web**: FastAPI, Gradio, Uvicorn
- **Auth**: JWT, bcrypt
- **Cache**: Redis
- **Queue**: Celery
- **Tools**: Rich, Tenacity, Jinja2

## Docker 部署

### 快速启动 (docker-compose)

```bash
# 克隆项目
git clone https://github.com/your-repo/mox.git
cd mox

# 复制并配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Keys

# 启动所有服务 (API + UI + Redis)
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

### 单独启动

```bash
# 构建镜像
docker build -t mox:latest .

# 运行 API 服务
docker run -d -p 8000:8000 \
  --env-file .env \
  --name mox-api \
  mox:latest

# 运行 Web UI
docker run -d -p 7860:7860 \
  --env-file .env \
  --env MOX_API_URL=http://api:8000 \
  --link mox-api \
  --name mox-ui \
  mox:latest python -m mox ui
```

### 生产环境部署

```bash
# 启动包含监控组件 (Prometheus + Grafana)
docker-compose --profile monitoring up -d

# 服务地址:
# - API: http://localhost:8000
# - Web UI: http://localhost:7860
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

### 环境变量

复制 `.env.example` 为 `.env` 并配置以下关键变量:

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `MOX_SECRET_KEY` | JWT签名密钥 (必填!) | - |
| `MOX_REQUIRE_AUTH` | 是否需要认证 | `false` |
| `MOX_REDIS_URL` | Redis连接地址 | `redis://localhost:6379` |
| `MOX_DATABASE_URL` | 数据库连接地址 | SQLite本地文件 |
| `MOX_LOCAL_MODEL_PATH` | 本地 HuggingFace 模型路径 | - |
| `MOX_LORA_ADAPTER_PATH` | LoRA 适配器路径 | - |
| `MOX_LOAD_IN_4BIT` | 启用 4bit 量化 | `false` |
| `MOX_LOAD_IN_8BIT` | 启用 8bit 量化 | `false` |
| `MOX_DEVICE_MAP` | 设备映射策略 | `auto` |
| `MOX_TORCH_DTYPE` | 模型加载数据类型 | `bfloat16` |
| `MOX_TRUSTED_PROXIES` | 可信代理 IP 列表 | - |

**重要**: 生产环境请务必设置 `MOX_SECRET_KEY` 和 `MOX_REQUIRE_AUTH=true`

## 测试

```bash
# 运行测试
pytest tests/ -v

# 带覆盖率
pytest tests/ --cov=mox --cov-report=html

# 类型检查
mypy mox/

# 代码检查
ruff check mox/
black --check mox/
```

## 安全扫描

```bash
# Bandit 安全扫描
bandit -r mox/

# 依赖漏洞检查
safety check
pip-audit
```

## 贡献指南

欢迎提交 Pull Request 或 Issue！

```bash
# 克隆项目
git clone https://github.com/your-repo/mox.git
cd mox

# 创建开发分支
git checkout -b feature/your-feature-name

# 安装开发依赖
pip install -e ".[dev]"

# 运行代码检查
ruff check mox/
black --check mox/
mypy mox/

# 运行测试
pytest tests/ -v

# 提交前
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature-name
```

## 版本历史

- **v0.3.1** - HuggingFace 本地模型支持（4bit/8bit 量化、LoRA）、训练数据导出（DPO/RLHF）、安全加固（登录爆破防护、WebSocket 认证、代理 IP 信任）
- **v0.3.0** - 统一模式库/评估框架重构、20+攻击模块规范化、防御模块全面升级
- **v0.2.0** - 统一攻击/防御框架、多模型支持、CI/CD完善
- **v0.1.0** - 初始版本

## License

MIT License
