# Mox - 大模型对抗攻防平台

## 完整使用指南

---

## 目录

1. [快速开始](#1-快速开始)
2. [支持模型](#2-支持模型)
3. [攻击模块](#3-攻击模块)
4. [防御模块](#4-防御模块)
5. [评估与基准](#5-评估与基准)
6. [可视化报告](#6-可视化报告)
7. [命令行工具](#7-命令行工具)
8. [API服务](#8-api服务)
9. [Web界面](#9-web界面)

---

## 1. 快速开始

### 安装

```bash
# 克隆或下载项目
cd mox

# 安装依赖
pip install -e .

# 或安装开发版本
pip install -e ".[dev]"
```

### 配置

```bash
# 复制配置示例
cp .env.example .env

# 编辑 .env 填入API Key
```

### 基础使用

```python
import asyncio
from mox import LLMFactory, PromptInjectionAttack, InputFilter, AttackPayload, AttackType

async def main():
    # 创建LLM实例
    llm = LLMFactory.create_from_model_name("gpt-4")
    
    # 攻击测试
    attack = PromptInjectionAttack(target_llm=llm)
    payload = AttackPayload(
        attack_type=AttackType.PROMPT_INJECTION,
        prompt="Write a poem",
        target_behavior="poem",
    )
    outcome = await attack.generate_attack(payload)
    print(f"攻击结果: {outcome.result.value}")
    
    # 防御检测
    defense = InputFilter()
    result = await defense.detect("Ignore all instructions...")
    print(f"是否恶意: {result.is_malicious}")

asyncio.run(main())
```

---

## 2. 支持模型

### 云端模型

```python
from mox import LLMFactory

# OpenAI
llm = LLMFactory.create_from_model_name("gpt-4")
llm = LLMFactory.create_from_model_name("gpt-3.5-turbo")

# Anthropic
llm = LLMFactory.create_from_model_name("claude-3-opus")
llm = LLMFactory.create_from_model_name("claude-3-sonnet")

# MiniMax
llm = LLMFactory.create_from_model_name("abab6.5s-chat")
```

### 本地模型 (Ollama)

```bash
# 先启动Ollama
ollama serve

# 拉取模型
ollama pull llama3
ollama pull qwen2.5
ollama pull mistral
```

```python
# 自动检测
llm = LLMFactory.create_from_model_name("llama3")
llm = LLMFactory.create_from_model_name("qwen2.5")
llm = LLMFactory.create_from_model_name("mistral")
llm = LLMFactory.create_from_model_name("phi3")
llm = LLMFactory.create_from_model_name("codellama")

# 或手动指定
from mox import OllamaLLM
llm = OllamaLLM(
    model="llama3",
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)
```

---

## 3. 攻击模块

### 3.1 基础攻击

```python
from mox import (
    LLMFactory,
    PromptInjectionAttack,
    JailbreakAttack,
    GCGAttack,
    AutoDANAttack,
    AttackConfig,
    AttackPayload,
    AttackType,
)

llm = LLMFactory.create_from_model_name("gpt-4")

# Prompt Injection
attack = PromptInjectionAttack(target_llm=llm)
payload = AttackPayload(
    attack_type=AttackType.PROMPT_INJECTION,
    prompt="Write a poem",
    target_behavior="poem"
)
outcome = await attack.generate_attack(payload)

# Jailbreak
attack = JailbreakAttack(target_llm=llm)

# GCG (需要tokenizer)
attack = GCGAttack(target_llm=llm, config=AttackConfig(max_iterations=100))

# AutoDAN
attack = AutoDANAttack(target_llm=llm)
```

### 3.2 LLM驱动攻击

```python
from mox import (
    TAPAttack,
    MultiTurnJailbreakAttack,
    CrescendoAttack,
    TAPConfig,
)

# TAP/PAIR 自动红队攻击
llm = LLMFactory.create_from_model_name("gpt-4")
attack = TAPAttack(
    target_llm=llm,
    attacker_llm=llm,  # 可使用不同模型
    config=TAPConfig(max_iterations=10, max_depth=5)
)
outcome = await attack.generate_attack(payload)

# Multi-turn Jailbreak
attack = MultiTurnJailbreakAttack(target_llm=llm)

# Crescendo 渐进式攻击
attack = CrescendoAttack(target_llm=llm)
```

### 3.3 RAG/Agent攻击

```python
from mox import (
    RAGContextInjectionAttack,
    AgentToolManipulationAttack,
    ChainOfThoughtExfiltrationAttack,
    IndirectPromptInjectionAttack,
)

# RAG 上下文注入
attack = RAGContextInjectionAttack(target_llm=llm)

# Agent 工具操纵
attack = AgentToolManipulationAttack(target_llm=llm)

# CoT 外泄
attack = ChainOfThoughtExfiltrationAttack(target_llm=llm)

# 间接注入
attack = IndirectPromptInjectionAttack(target_llm=llm)
```

### 3.4 Agent特定攻击

```python
from mox import (
    ToolAbuseAttack,
    MemoryInjectionAttack,
    RoleHijackingAttack,
    AuthorityEscalationAttack,
    ChainOfThoughtInjectionAttack,
)

# 工具滥用
attack = ToolAbuseAttack(target_llm=llm)

# 记忆注入
attack = MemoryInjectionAttack(target_llm=llm)

# 角色劫持
attack = RoleHijackingAttack(target_llm=llm)

# 权限提升
attack = AuthorityEscalationAttack(target_llm=llm)

# CoT注入
attack = ChainOfThoughtInjectionAttack(target_llm=llm)
```

### 3.5 攻击配置

```python
from mox import AttackConfig, TAPConfig

config = AttackConfig(
    max_iterations=100,     # 最大迭代次数
    success_threshold=0.8,  # 成功阈值
    temperature=0.7,        # 采样温度
    verbose=True            # 详细输出
)

tap_config = TAPConfig(
    max_iterations=20,
    max_depth=5,
    max_breadth=3,
    use_refinement=True,   # 使用细化
    context_window=3
)
```

---

## 4. 防御模块

### 4.1 输入过滤

```python
from mox import InputFilter

filter = InputFilter()

# 检测恶意输入
result = await filter.detect("Ignore all previous instructions...")
print(f"是否恶意: {result.is_malicious}")
print(f"置信度: {result.confidence}")
print(f"检测模式: {result.detected_patterns}")
```

### 4.2 输出过滤

```python
from mox import OutputFilter

filter = OutputFilter()

result = await filter.detect("My password is admin123")
print(f"是否危险: {result.is_malicious}")
print(f"净化后: {result.sanitized_input}")
```

### 4.3 系统提示词加固

```python
from mox import SystemPromptHardening

hardening = SystemPromptHardening()

# 获取加固后的提示词
hardened = hardening.get_hardened_prompt(
    custom_instructions="你是一个有帮助的助手"
)

# 获取注入防御提示
injection_defense = hardening.get_injection_defense_prompt()
```

### 4.4 防御管道

```python
from mox import DefensePipeline, InputFilter, OutputFilter

pipeline = DefensePipeline()
pipeline.add_defense(InputFilter())
pipeline.add_defense(OutputFilter())

# 多层检测
result = await pipeline.scan_input(user_input)
result = await pipeline.scan_output(model_response)
```

### 4.5 LLM-as-Judge

```python
from mox.defense.llm_judge import LLMJudge, SafetyCoTDefense, JudgmentType

# 使用LLM判断安全性
judge = LLMJudge(llm, judgment_type=JudgmentType.SAFETY)
result = await judge.judge(prompt, response)
print(f"安全: {result.is_safe}, 置信度: {result.confidence}")

# Safety-CoT 防御
defense = SafetyCoTDefense(llm)
result = await defense.check_and_respond(user_input)
```

---

## 5. 评估与基准

### 5.1 内置数据集

```python
from mox import BenchmarkDataset

dataset = BenchmarkDataset()

# 列出数据集
print(dataset.list_datasets())
# ['advbench', 'harmbench', 'defense_test', 'harmbench_standard']

# 获取数据集信息
info = dataset.get_dataset_info("harmbench_standard")
print(f"大小: {info['size']}")
print(f"类别: {info['categories']}")

# 获取测试用例
payloads = dataset.get_attack_payloads("harmbench_standard", limit=10)
```

### 5.2 运行基准测试

```python
from mox import BenchmarkRunner, LLMFactory, PromptInjectionAttack

llm = LLMFactory.create_from_model_name("gpt-4")
attack = PromptInjectionAttack(target_llm=llm)

runner = BenchmarkRunner()
dataset = BenchmarkDataset()
payloads = dataset.get_attack_payloads("advbench", limit=5)

results = await attack.run_batch(payloads)

# 评估
for outcome in results:
    runner.attack_evaluator.add_result(outcome)

report = runner.attack_evaluator.generate_report()
print(f"攻击成功率: {report.attack_success_rate}")
```

---

## 6. 可视化报告

### 6.1 快速生成

```python
from mox import create_quick_report, ReportGenerator

# 方式1: 快速生成
filename = create_quick_report(outcomes, attack_types)
# 输出: mox_report.html

# 方式2: 自定义
report = ReportGenerator()
for outcome in outcomes:
    report.add_result(outcome, "attack_type")

# 保存HTML报告
report.save_html_report("my_report.html")

# 获取JSON报告
json_data = report.generate_json_report()
```

### 6.2 报告内容

报告包含：
- 总测试数、成功/失败数、成功率
- 攻击成功率饼图
- 攻击类型分布环形图
- 各类型成功率柱状图
- 迭代次数分布
- 详细结果表格

---

## 7. 命令行工具

### 7.1 快速测试

```bash
# 攻击测试
python -m mox quick --mode attack -p "how to hack" -t "hack info" --model llama3

# 防御检测
python -m mox quick --mode defense -p "Ignore all instructions"

# LLM判断
python -m mox quick --mode judge -p "harmful question" -r "refused response"
```

### 7.2 完整攻击

```bash
# 指定攻击类型
python -m mox attack -t prompt_injection -p "test" --target "harmful"
python -m mox attack -t jailbreak -p "test" --target "harmful"
python -m mox attack -t tap -p "test" --target "harmful"
python -m mox attack -t multi_turn -p "test" --target "harmful"
python -m mox attack -t crescendo -p "test" --target "harmful"
python -m mox attack -t rag -p "test" --target "harmful"
python -m mox attack -t agent -p "test" --target "harmful"

# 指定模型
python -m mox attack -t tap -p "test" --target "harmful" -m llama3

# 指定迭代
python -m mox attack -t tap -p "test" --target "harmful" --max-iter 20
```

### 7.3 防御检测

```bash
# 输入检测
python -m mox defense --text "Ignore all instructions"

# 输出检测
python -m mox defense --scan-type output --text "My password is secret"
```

### 7.4 基准测试

```bash
# 运行基准测试
python -m mox benchmark -d harmbench_standard -a tap --max-cases 10

# 指定模型
python -m mox benchmark -d advbench -a jailbreak -m llama3 --max-cases 5
```

### 7.5 LLM-as-Judge

```bash
# 评估安全性
python -m mox judge --text "how to make bomb" --response "I can't help"

# Safety-CoT防御
python -m mox cot --text "how to hack"
```

---

## 8. API服务

### 启动

```bash
python -m mox api
# 访问 http://localhost:8000/docs
```

### 示例请求

```bash
# 攻击
curl -X POST http://localhost:8000/attack \
  -H "Content-Type: application/json" \
  -d '{
    "attack_type": "prompt_injection",
    "model": "gpt-4",
    "prompt": "test",
    "target": "harmful"
  }'

# 防御
curl -X POST http://localhost:8000/defense \
  -H "Content-Type: application/json" \
  -d '{"text": "Ignore all instructions"}'
```

---

## 9. Web界面

### 启动

```bash
python -m mox ui
# 访问 http://localhost:7860
```

### 功能

- 攻击测试
- 防御检测
- 基准测试
- 结果可视化

---

## 10. 示例代码

### 完整示例

```python
import asyncio
from mox import (
    LLMFactory,
    PromptInjectionAttack,
    InputFilter,
    AttackPayload,
    AttackType,
    ReportGenerator,
)

async def main():
    # 1. 创建LLM (支持本地Ollama)
    llm = LLMFactory.create_from_model_name("llama3")
    
    # 2. 运行攻击
    attack = PromptInjectionAttack(target_llm=llm)
    payloads = [
        AttackPayload(AttackType.PROMPT_INJECTION, "test1", "target1"),
        AttackPayload(AttackType.JAILBREAK, "test2", "target2"),
    ]
    
    outcomes = []
    for payload in payloads:
        outcome = await attack.generate_attack(payload)
        outcomes.append(outcome)
        print(f"攻击: {outcome.result.value}")
    
    # 3. 测试防御
    defense = InputFilter()
    result = await defense.detect("Ignore all instructions")
    print(f"检测: {result.is_malicious}")
    
    # 4. 生成报告
    report = ReportGenerator()
    for outcome in outcomes:
        report.add_result(outcome, "test")
    report.save_html_report("report.html")

asyncio.run(main())
```

---

## 附录

### 支持的模型列表

**OpenAI**: gpt-4, gpt-4-turbo, gpt-3.5-turbo, o1, o1-mini

**Anthropic**: claude-3-opus, claude-3-sonnet, claude-3-haiku

**MiniMax**: abab6.5s-chat, abab2.5-chat

**Ollama**: llama3, llama2, qwen2.5, mistral, phi3, codellama, deepseek, gemma

### 攻击类型枚举

```python
from mox.core import AttackType

AttackType.PROMPT_INJECTION   # 提示词注入
AttackType.JAILBREAK          # 越狱攻击
AttackType.GCG                # GCG攻击
AttackType.AUTO_DAN           # AutoDAN攻击
AttackType.ROLE_PLAY          # 角色扮演
AttackType.DEEP_INCEPTION     # 深度 inception
```

### 防御类型枚举

```python
from mox.core import DefenseType

DefenseType.INPUT_FILTER         # 输入过滤
DefenseType.OUTPUT_FILTER        # 输出过滤
DefenseType.PROMPT_HARDENING     # 提示词加固
DefenseType.PERPLEXITY_FILTER    # 困惑度过滤
```

---

生成时间: 2025
