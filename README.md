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
- **Input Filter**: 输入过滤，检测恶意提示
- **Output Filter**: 输出过滤，检测敏感信息泄露
- **System Prompt Hardening**: 系统提示词加固
- **Defense Pipeline**: 防御管道，组合多种防御策略
- **LLM Judge**: LLM作为评判者
- **Perplexity Filter**: 基于困惑度的检测
- **Semantic Similarity**: 语义相似度检测

### 评估模块 (Evaluation)
- **Benchmark Runner**: 基准测试运行器 (AdvBench, HarmBench)
- **Attack Evaluator**: 攻击效果评估
- **Defense Evaluator**: 防御效果评估
- **Robustness Evaluator**: 鲁棒性评估
- **OWASP LLM Top 10**: OWASP安全测试

### 基础设施
- **LLM Gateway**: 多模型负载均衡和故障转移
- **Task Queue**: 异步任务队列
- **WebSocket**: 实时更新
- **Authentication**: JWT认证
- **Caching**: Redis/内存缓存

## 支持的模型

- **OpenAI**: GPT-3.5, GPT-4, o1, o3
- **Anthropic**: Claude 3 (Opus, Sonnet, Haiku)
- **MiniMax**: abab2.5, abab6.5系列
- **Google**: Gemini 系列
- **DeepSeek**: deepseek-chat, deepseek-coder
- **Cohere**: Command
- **Gro R 系列q**: llama-3.1, mixtral (高吞吐量)
- **Azure OpenAI**: Azure部署的GPT模型
- **本地模型**: Ollama 支持的所有模型

## 快速开始

### 安装

```bash
pip install -e .
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

# 5. 运行自动化攻击循环测试
python examples/attack_loop.py
python examples/advanced_attack_loop.py
```

支持的 Ollama 模型:
- `llama3`, `llama3.1`, `llama3.2`
- `qwen2`, `qwen2.5`, `qwen3`, `qwen3:4b`
- `gemma3`, `gemma3:4b`
- `mistral`, `mixtral`
- `phi3`, `deepseek-coder`
- 以及所有 Ollama 支持的模型

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

# 安全配置
SECRET_KEY=your-secret-key-here
MOX_REQUIRE_AUTH=false
MOX_RATE_LIMIT_PER_MINUTE=60
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

### 自动化攻击测试循环

```bash
# 基础版本 - 顺序执行攻击测试
python examples/attack_loop.py

# 高级版本 - 并行执行攻击测试，支持实时监控
python examples/advanced_attack_loop.py

# 指定模型和攻击类型
python examples/advanced_attack_loop.py llama3,qwen3:4b tool_chaining,privilege_escalation 2 3
```

详细的攻击循环使用说明请参考 [攻击测试循环文档](examples/ATTACK_LOOP_README.md)。

## API 认证

用户通过 `MOX_DEFAULT_USERS` 环境变量配置（格式 `username:password:email:scopes`，多个用户用 `|` 分隔）。**生产环境务必使用强密码**，切勿使用示例值。

### 登录获取 Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "YOUR_USERNAME", "password": "YOUR_PASSWORD"}'
```

返回:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "username": "YOUR_USERNAME",
    "email": "user@mox.ai",
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
from mox.core.llm_gateway import LLMGateway, LoadBalancingStrategy

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
│   ├── auth.py              # JWT认证
│   ├── tasks.py             # 异步任务队列
│   ├── cache.py             # 缓存管理
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库
│   └── types.py             # 类型定义
├── attacks/                 # 攻击模块
│   ├── prompt_injection.py
│   ├── jailbreak.py
│   ├── gcg.py
│   ├── rag_attacks.py
│   └── agent_attacks.py
├── defense/                 # 防御模块
│   ├── input_filter.py
│   ├── output_filter.py
│   ├── hardening.py
│   └── llm_judge.py
├── evaluation/              # 评估模块
│   ├── benchmarks.py
│   ├── evaluator.py
│   └── owasp_tests.py
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
# - Grafana: http://localhost:3000 (set GRAFANA_ADMIN_USER / GRAFANA_ADMIN_PASSWORD in .env)
```

### 环境变量

复制 `.env.example` 为 `.env` 并配置以下关键变量:

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `MOX_SECRET_KEY` | JWT签名密钥 (必填!) | - |
| `MOX_REQUIRE_AUTH` | 是否需要认证 | `false` |
| `MOX_REDIS_URL` | Redis连接地址 | `redis://localhost:6379` |
| `MOX_DATABASE_URL` | 数据库连接地址 | SQLite本地文件 |

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

- **v0.2.0** - 统一攻击/防御框架、多模型支持、CI/CD完善
- **v0.1.0** - 初始版本

## License

MIT License
