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

```bash
# 构建镜像
docker build -t mox:latest .

# 运行容器
docker run -d -p 8000:8000 -p 7860:7860 \
  --env-file .env \
  mox:latest
```

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

## License

MIT License
