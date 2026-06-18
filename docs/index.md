# Mox 文档

欢迎使用 Mox - 大模型对抗攻防平台文档。

## 目录

- [README](../README.md) - 项目概览
- [API 参考](api.md) - 核心 API
- [攻击模块](attacks.md) - 攻击方法详解
- [防御模块](defense.md) - 防御策略详解
- [评估模块](evaluation.md) - 评估框架

## 快速链接

### 安装
```bash
pip install -e .
```

### 快速开始
```python
from mox import LLMFactory, PromptInjectionAttack, InputFilter

llm = LLMFactory.create_from_model_name("gpt-4")
attack = PromptInjectionAttack(target_llm=llm)
```

### 运行示例
```bash
python examples/basic_usage.py
python examples/attack_loop.py  # 攻击循环测试
```

### 启动服务
```bash
python -m mox api   # API 服务
python -m mox ui   # Web UI
```
