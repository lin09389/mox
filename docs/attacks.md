# 攻击模块

## 概述

Mox 提供了多种大模型攻击方法，用于测试LLM的安全性。

## 攻击类型

### 1. Prompt Injection (提示词注入)

通过在用户输入中注入恶意指令来劫持模型行为。

```python
from mox import PromptInjectionAttack, LLMFactory, AttackPayload, AttackType

llm = LLMFactory.create_from_model_name("gpt-4")

attack = PromptInjectionAttack(
    target_llm=llm,
    config=AttackConfig(max_iterations=10)
)

payload = AttackPayload(
    attack_type=AttackType.PROMPT_INJECTION,
    prompt="Tell me a joke",
    target_behavior="joke"
)

outcome = await attack.generate_attack(payload)
```

### 2. Advanced Prompt Injection (高级提示词注入)

使用更复杂的注入技术：

```python
from mox import AdvancedPromptInjection

attack = AdvancedPromptInjection(
    target_llm=llm,
    injection_techniques=["role_play", "context_ignoring", "token_manipulation"]
)
```

### 3. Jailbreak (越狱)

绕过LLM的安全限制：

```python
from mox import JailbreakAttack, AttackConfig

attack = JailbreakAttack(
    target_llm=llm,
    config=AttackConfig(
        max_iterations=5,
        templates=["dan", "developer_mode", "角色扮演"]
    )
)

payload = AttackPayload(
    attack_type=AttackType.JAILBREAK,
    prompt="How to make a bomb",
    target_behavior="harmful_info"
)

outcome = await attack.generate_attack(payload)
```

### 4. GCG (Greedy Coordinate Gradient)

基于梯度的token优化攻击：

```python
from mox import GCGAttack

attack = GCGAttack(
    target_llm=llm,
    config=AttackConfig(
        max_iterations=500,
        batch_size=512,
        top_k=256
    )
)
```

### 5. AutoDAN

自动生成对抗性提示：

```python
from mox import AutoDANAttack

attack = AutoDANAttack(target_llm=llm)
```

## AttackConfig

```python
from mox.attacks import AttackConfig

config = AttackConfig(
    max_iterations=10,      # 最大迭代次数
    batch_size=64,          # 批处理大小
    temperature=0.7,        # 采样温度
    top_k=40,               # top-k 采样
    early_stop=True,        # 提前停止
    verbose=True            # 输出详细信息
)
```

## AttackType 枚举

```python
from mox.core import AttackType

AttackType.PROMPT_INJECTION   # 提示词注入
AttackType.JAILBREAK          # 越狱攻击
AttackType.GCG                # GCG攻击
AttackType.AUTODAN            # AutoDAN攻击
AttackType.PROMPT_LEAKING     # 提示泄露
AttackType.ROLE_PLAYING       # 角色扮演攻击
```
