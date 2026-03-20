# API 文档

## 核心模块 (mox.core)

### LLM 接口

#### LLMFactory

```python
from mox.core import LLMFactory

# 从模型名称创建
llm = LLMFactory.create_from_model_name("gpt-4")
llm = LLMFactory.create_from_model_name("claude-3-opus")
llm = LLMFactory.create_from_model_name("abab6.5s-chat")

# 从配置创建
from mox.core import ModelProvider, Settings
llm = LLMFactory.create(
    provider=ModelProvider.OPENAI,
    model="gpt-4",
    settings=Settings(temperature=0.7)
)
```

#### BaseLLM

```python
from mox import BaseLLM

# 同步调用
response = llm.chat([{"role": "user", "content": "Hello"}])

# 异步调用
response = await llm.achat([{"role": "user", "content": "Hello"}])

# 流式调用
for chunk in llm.stream_chat([{"role": "user", "content": "Hello"}]):
    print(chunk)
```

### 数据类型

#### Message

```python
from mox.core import Message

msg = Message(role="user", content="Hello")
msg = Message(role="assistant", content="Hi there")
msg = Message(role="system", content="You are helpful")
```

#### AttackPayload

```python
from mox.core import AttackPayload, AttackType

payload = AttackPayload(
    attack_type=AttackType.PROMPT_INJECTION,
    prompt="原始提示词",
    target_behavior="目标行为",
    context={"key": "value"}  # 可选上下文
)
```

#### AttackOutcome

```python
outcome = await attack.generate_attack(payload)

# 属性
outcome.success_score      # 成功分数 (0-1)
outcome.adversarial_prompt # 对抗性提示词
outcome.model_response     # 模型响应
outcome.iterations         # 迭代次数
outcome.metadata           # 元数据
outcome.result             # 攻击结果枚举
```
