# 评估模块

## 概述

Mox 提供了完整的评估框架，用于测试攻击效果和防御能力。

## 组件

### 1. BenchmarkRunner (基准测试运行器)

运行标准基准测试：

```python
from mox import BenchmarkRunner, BenchmarkDataset

runner = BenchmarkRunner()

# 加载数据集
dataset = BenchmarkDataset()
payloads = dataset.get_attack_payloads("advbench")

# 运行测试
for payload in payloads:
    outcome = await attack.generate_attack(payload)
    runner.attack_evaluator.add_result(outcome)

# 生成报告
report = runner.attack_evaluator.generate_report()
print(report.attack_success_rate)
```

### 2. AttackEvaluator (攻击评估器)

```python
from mox import AttackEvaluator

evaluator = AttackEvaluator()

# 添加结果
evaluator.add_result(attack_outcome)

# 获取指标
metrics = evaluator.get_metrics()
# - attack_success_rate
# - avg_iterations
# - avg_success_score

# 生成报告
report = evaluator.generate_report()
```

### 3. DefenseEvaluator (防御评估器)

```python
from mox import DefenseEvaluator

evaluator = DefenseEvaluator()

# 测试防御效果
for test_input in malicious_inputs:
    result = await defense.detect(test_input)
    evaluator.add_result(result, expected_is_malicious=True)

# 评估指标
metrics = evaluator.get_metrics()
# - detection_rate
# - false_positive_rate
# - precision
# - recall
```

### 4. RobustnessEvaluator (鲁棒性评估器)

```python
from mox.evaluation.evaluator import RobustnessEvaluator

evaluator = RobustnessEvaluator()

# 测试模型在各种攻击下的鲁棒性
evaluator.evaluate_model(llm, attack_payloads)

# 获取鲁棒性评分
score = evaluator.get_robustness_score()
```

## 内置数据集

```python
from mox import BenchmarkDataset

dataset = BenchmarkDataset()

# 列出可用数据集
print(dataset.list_datasets())
# ['advbench', 'harmbench', 'jailbreakbench']

# 获取数据集信息
info = dataset.get_dataset_info("advbench")
print(info['size'])       # 测试用例数量
print(info['categories']) # 类别

# 加载测试用例
payloads = dataset.get_attack_payloads("advbench", limit=100)
```

## EvaluationReport

```python
from mox import EvaluationReport

report = EvaluationReport(
    total_attacks=100,
    successful_attacks=30,
    failed_attacks=70,
    attack_success_rate=0.3,
    avg_iterations=5.2,
    metadata={}
)

# 转换为字典
data = report.to_dict()

# 导出为JSON
json_str = report.to_json()
```
