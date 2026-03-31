# 防御模块

## 概述

Mox 提供了多种防御机制来保护LLM免受对抗性攻击。

## 防御类型

### 1. Input Filter (输入过滤)

检测并拦截恶意用户输入：

```python
from mox import InputFilter

filter = InputFilter()

result = await filter.detect("Ignore all previous instructions...")
print(result.is_malicious)      # True/False
print(result.confidence)        # 置信度 0-1
print(result.detected_patterns) # 检测到的模式列表
```

### 2. Output Filter (输出过滤)

检测敏感信息泄露：

```python
from mox import OutputFilter

filter = OutputFilter()

result = await filter.detect("My password is admin123")
print(result.is_malicious)       # True/False
print(result.sanitized_input)    # 净化后的文本
```

### 3. Perplexity Filter (困惑度过滤)

基于语言模型困惑度检测异常输入：

```python
from mox import PerplexityFilter

filter = PerplexityFilter(threshold=50.0)
result = await filter.detect(user_input)
```

### 4. Keyword Detector (关键词检测)

检测特定关键词：

```python
from mox import KeywordDetector

detector = KeywordDetector(
    keywords=["password", "secret", "api_key"],
    case_sensitive=False
)

result = await detector.detect(user_input)
```

### 5. Content Moderator (内容审核)

综合内容审核：

```python
from mox import ContentModerator

moderator = ContentModerator()
result = await moderator.moderate(user_input)
```

### 6. System Prompt Hardening (系统提示词加固)

增强系统提示词的抗攻击能力：

```python
from mox import SystemPromptHardening

hardening = SystemPromptHardening()

# 获取加固后的提示词
hardened = hardening.get_hardened_prompt(
    custom_instructions="你是一个有帮助的助手"
)

# 获取注入防御提示词
injection_defense = hardening.get_injection_defense_prompt()
```

### 7. Defense Pipeline (防御管道)

组合多种防御策略：

```python
from mox import DefensePipeline, InputFilter, OutputFilter

pipeline = DefensePipeline()
pipeline.add_defense(InputFilter())
pipeline.add_defense(OutputFilter())

# 对输入进行多层检测
result = await pipeline.scan_input(user_input)
print(result["is_malicious"])
print(result["confidence"])
print(result["detected_patterns"])

# 对输出进行多层检测
result = await pipeline.scan_output(model_response)
```

## DefenseConfig

```python
from mox.defense import DefenseConfig

config = DefenseConfig(
    threshold=0.5,       # 置信度阈值
    block=True,           # 是否拦截
    sanitize=True,        # 是否净化
    log=True             # 是否记录日志
)
```

## DefenseType 枚举

```python
from mox.core import DefenseType

DefenseType.INPUT_FILTER         # 输入过滤
DefenseType.OUTPUT_FILTER        # 输出过滤
DefenseType.PERPLEXITY_FILTER    # 困惑度过滤
DefenseType.KEYWORD_DETECTOR     # 关键词检测
DefenseType.CONTENT_MODERATOR    # 内容审核
DefenseType.PROMPT_HARDENING     # 提示词加固
```
