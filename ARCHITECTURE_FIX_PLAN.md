# Mox 架构优化修复计划

> 基于代码深度审查，按风险/收益排序的 5 个修复阶段

---

## 当前架构问题总览

| # | 问题 | 影响范围 | 风险 |
|---|------|---------|------|
| 1 | 攻击/防御注册中心完全重复 | `attacks/registry.py`, `defense/registry.py` | 高 |
| 2 | `EvaluationResult`/`AttackEvaluator` 多处冲突定义 | `core/evaluation.py`, `evaluation/attack_evaluator.py`, `evaluation/evaluator.py`, `attacks/evaluation.py` | 高 |
| 3 | `BaseAttack`/`BaseDefense` 直接耦合数据库 | `attacks/base.py`, `defense/base.py` | 中 |
| 4 | `DefenseOrchestrator.run_scenario()` 大型 if-elif 分支 | `defense/orchestrator.py` L313-340 | 中 |
| 5 | `_load_all_attacks()` 静默吞异常 | `attacks/__init__.py` L104-120 | 中 |
| 6 | 模块级全局单例过多 | `attacks/orchestrator.py`, `defense/registry.py` | 低 |

---

## Phase 1: 泛型注册中心 (影响最大，风险最低)

**目标：** 用一个泛型 `Registry[T]` 消除 `attacks/registry.py` 和 `defense/registry.py` 的完全重复。

**新建文件：** `mox/core/registry.py`

```python
"""Generic registry pattern for attack/defense plugins."""
from __future__ import annotations

import threading
from typing import Dict, Type, Optional, TypeVar, Generic, Callable, Any

T = TypeVar("T")


class Registry(Generic[T]):
    """Thread-safe generic registry with decorator-based registration."""

    def __init__(self, name: str):
        self._name = name
        self._entries: Dict[str, Type[T]] = {}
        self._lock = threading.Lock()

    def register(self, key: str) -> Callable[[Type[T]], Type[T]]:
        """Decorator: @registry.register("my_attack")"""
        def decorator(cls: Type[T]) -> Type[T]:
            with self._lock:
                if key in self._entries:
                    import logging
                    logging.getLogger(__name__).warning(
                        "%s '%s' already registered, overwriting with %s",
                        self._name, key, cls.__name__,
                    )
                self._entries[key] = cls
            return cls
        return decorator

    def get(self, key: str) -> Optional[Type[T]]:
        with self._lock:
            return self._entries.get(key)

    def create(self, key: str, **kwargs) -> T:
        cls = self.get(key)
        if cls is None:
            raise ValueError(
                f"{self._name} '{key}' not in registry. "
                f"Available: {self.registered_names}"
            )
        return cls(**kwargs)

    @property
    def registered_names(self) -> list[str]:
        with self._lock:
            return list(self._entries.keys())

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._entries

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)
```

**修改文件：**

`mox/attacks/registry.py` → 简化为：
```python
from mox.core.registry import Registry
from .base import BaseAttack

ATTACK_REGISTRY: Registry[BaseAttack] = Registry("attack")

# 保留向后兼容的工厂函数
def create_attack_instance(attack_type: str, llm, config=None, **kwargs):
    # ... 不变
```

`mox/defense/registry.py` → 简化为：
```python
from mox.core.registry import Registry
from .base import BaseDefense

DEFENSE_REGISTRY: Registry[BaseDefense] = Registry("defense")

def create_defense_instance(defense_type: str, config=None, **kwargs):
    # ... 不变
```

**验证：**
- `pytest tests/ -v` 全量通过
- `ATTACK_REGISTRY.registered_names` 输出与改动前一致
- `DEFENSE_REGISTRY.registered_names` 输出与改动前一致

---

## Phase 2: 评估器命名空间整理 (消除危险的别名覆盖)

**目标：** 让每个类名在整个项目中只有一处定义，消除 `evaluation/__init__.py` 里的别名赋值。

**现状问题：**
```
core/evaluation.py          → AttackEvaluator (ABC)      ← 正确，是基类
attacks/evaluation.py       → AttackEvaluator (concrete)  ← 名字冲突，靠别名掩盖
evaluation/attack_evaluator.py → AttackEvaluator (另一个)  ← 又一个
evaluation/evaluator.py     → AttackEvaluator (又一个)     ← 又又一个
evaluation/__init__.py      → AttackEvaluator = EnhancedAttackEvaluator  ← 别名覆盖
```

**改动：**

### 2a. `core/evaluation.py` — 重命名为 `BaseAttackEvaluator`

```python
# 改名：AttackEvaluator → BaseAttackEvaluator
class BaseAttackEvaluator(ABC):
    ...
```

同时保留一个向后兼容别名：
```python
AttackEvaluator = BaseAttackEvaluator  # deprecated alias，计划在 v0.4 移除
```

### 2b. `attacks/evaluation.py` — 改用 `BaseAttackEvaluator`

```python
from mox.core.evaluation import BaseAttackEvaluator

class AttackEvaluator(BaseAttackEvaluator):
    """Backward-compatible concrete evaluator, delegates to RefusalPatternEvaluator."""
    ...
```

### 2c. `evaluation/attack_evaluator.py` — 重命名为 `EnhancedAttackEvaluator`

这个文件里的类改名为 `EnhancedAttackEvaluator`（它本来就被 `__init__.py` 以这个名字导入，只是文件里叫 `AttackEvaluator`）。

### 2d. `evaluation/evaluator.py` — 重命名类

```python
# 改名：AttackEvaluator → AttackMetricsCollector (它是收集 metrics 的，不是评估攻击的)
class AttackMetricsCollector:
    ...

# DefenseEvaluator → DefenseMetricsCollector
class DefenseMetricsCollector:
    ...
```

### 2e. `evaluation/__init__.py` — 删除别名赋值

删除这行：
```python
AttackEvaluator = EnhancedAttackEvaluator  # 删除
```

改为直接导出 `EnhancedAttackEvaluator`，同时保留 `AttackEvaluator` 从 `attacks/evaluation` 的导入以保持向后兼容。

**验证：**
- 全量 pytest 通过
- `from mox import AttackEvaluator` 仍然可用
- `from mox.core.evaluation import BaseAttackEvaluator` 新路径可用
- grep 搜索确认 `AttackEvaluator` 在整个项目中只有 3 处定义（ABC + 2个concrete），无别名覆盖

---

## Phase 3: 解耦基类与数据库 (单一职责)

**目标：** `BaseAttack` 和 `BaseDefense` 不再直接写数据库。

**方案：** 引入事件回调机制。

### 3a. `mox/core/events.py` (新建)

```python
"""Simple event bus for decoupling persistence from core logic."""
from typing import Callable, Dict, List, Any
import asyncio

class EventBus:
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def on(self, event: str, handler: Callable):
        self._handlers.setdefault(event, []).append(handler)

    async def emit(self, event: str, **data):
        for handler in self._handlers.get(event, []):
            try:
                result = handler(**data)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                pass  # 事件处理器不应影响主流程

# 全局事件总线
event_bus = EventBus()
```

### 3b. 修改 `attacks/base.py`

删除 `_get_db()` 函数和 `_create_outcome` 中的数据库写入逻辑，改为：

```python
from mox.core.events import event_bus

async def _create_outcome(self, ...):
    outcome = AttackOutcome(...)
    self.history.append(outcome)
    # 发出事件，由外层监听并持久化
    await event_bus.emit("attack_completed", outcome=outcome, attack=self)
    return outcome
```

### 3c. 修改 `defense/base.py`

同理，删除 `_get_db()` 和 `_create_result` 中的数据库写入，改为发出 `defense_detected` 事件。

### 3d. 在 API/Orchestrator 层注册事件处理器

在 `mox/api.py` 或 `mox/infrastructure/` 的启动代码中：

```python
from mox.core.events import event_bus

async def persist_attack(outcome, attack, **kw):
    db = get_database()
    if db:
        await db.save_attack_record(...)

event_bus.on("attack_completed", persist_attack)
```

**验证：**
- pytest 全量通过
- `save_to_db=True` 的行为与改动前完全一致（通过事件处理器实现）
- `BaseAttack` 和 `BaseDefense` 不再有任何 `from mox.infrastructure.database` 的导入

---

## Phase 4: DefenseOrchestrator 条件分支消除

**目标：** 利用已有的注册中心替代 `run_scenario()` 中的 if-elif 链。

**方案：** 给 `BaseDefense` 增加一个可选的 `test_scenario()` 方法，让编排器统一分发。

### 4a. 在 `defense/base.py` 中添加默认实现

```python
class BaseDefense(ABC):
    ...

    async def run_scenario_test(self, test_input: str) -> tuple[bool, bool, float, str, dict, str | None]:
        """统一的场景测试接口，返回 (detected, blocked, confidence, sanitized, details, error)"""
        try:
            result = await self.detect(test_input)
            return (
                result.is_malicious,
                result.is_malicious,
                result.confidence,
                result.sanitized_input or test_input,
                {"patterns": result.detected_patterns},
                None,
            )
        except Exception as e:
            return False, False, 0.0, test_input, {}, f"{type(self).__name__} error: {e}"
```

### 4b. 特殊防御覆盖

`HallucinationDetector` 和 `LLMJudge` 有不同接口，需要覆盖：

```python
class HallucinationDetector(BaseDefense):
    async def run_scenario_test(self, test_input: str) -> tuple:
        result = self.check(test_input, "test context")
        return (result.is_hallucination, False, result.confidence, test_input, {...}, None)
```

### 4c. 简化 `DefenseOrchestrator.run_scenario()`

```python
async def run_scenario(self, scenario):
    defense = self.defenses.get(scenario.defense_type)
    if defense is None:
        reg_name = self.defense_mapping.get(scenario.defense_type)
        if reg_name:
            defense = create_defense_instance(reg_name, target_llm=self.target_llm)
        else:
            defense = create_defense_instance("input_filter")

    detected, blocked, confidence, sanitized, details, error = await defense.run_scenario_test(scenario.test_input)
    ...
```

整段 30 行 if-elif 变成 10 行。

**验证：**
- 所有 9 个防御场景测试结果与改动前一致
- 新增防御类型无需修改 orchestrator

---

## Phase 5: 攻击注册表静默失败改为显式

**目标：** `_load_all_attacks()` 中的 `except Exception` 改为在启动时报告失败的模块。

**方案：** 收集所有失败，在启动摘要中输出，同时提供一个 `verify_registry()` 工具函数。

### 5a. 修改 `attacks/__init__.py`

```python
_load_failures: list[tuple[str, Exception]] = []

def _load_all_attacks():
    ...
    for _, module_name, is_pkg in pkgutil.iter_modules([package_dir]):
        if not is_pkg and module_name not in EXCLUDED:
            try:
                importlib.import_module(f".{module_name}", package=__name__)
            except Exception as e:
                _load_failures.append((module_name, e))
                _log.warning("Failed to load '%s': %s", module_name, e)

def verify_registry() -> list[str]:
    """返回加载失败的模块列表，用于健康检查和 CI。"""
    return [name for name, _ in _load_failures]
```

### 5b. 添加 CI 检查脚本

```python
# scripts/verify_attacks.py
from mox.attacks import verify_registry, ATTACK_REGISTRY
failures = verify_registry()
if failures:
    print(f"WARNING: {len(failures)} attack modules failed to load: {failures}")
    exit(1)
print(f"OK: {len(ATTACK_REGISTRY.registered_names)} attacks registered")
```

### 5c. 在 API 启动时调用

在 `mox/api.py` 的 startup 事件中调用 `verify_registry()` 并记录到日志。

**验证：**
- 正常启动：0 failures
- 故意破坏一个模块：启动日志有 WARNING，`verify_registry()` 返回非空列表
- CI 脚本 `python scripts/verify_attacks.py` 通过

---

## 执行顺序与依赖关系

```
Phase 1 (泛型注册中心)
    ↓
Phase 2 (评估器命名空间)     ← 依赖 Phase 1 的 core/registry.py 存在
    ↓
Phase 3 (基类数据库解耦)     ← 独立，但建议在 Phase 1 之后做
    ↓
Phase 4 (DefenseOrchestrator) ← 依赖 Phase 1 的 Registry 泛型
    ↓
Phase 5 (静默失败)           ← 独立，可在任意阶段并行
```

## 不做的事情 (明确排除)

- **不拆分 `evaluation/` 子包** — 当前模块数量可控（8个文件），拆包会增加导入路径复杂度，收益不大
- **不引入 DI 容器** — 项目规模不需要，`EventBus` + 构造函数注入已足够
- **不删除 `benchmarks.py` vs `benchmarks_v2.py`** — v1 仍在被引用，需要先做迁移评估，属于单独任务
- **不改动前端** — 架构问题全在 Python 后端

## 完成标准

每个 Phase 完成后必须满足：
1. `pytest tests/ -v` 全部通过
2. `ruff check mox/` 无新增 warning
3. `from mox import *` 所有公开 API 不变（向后兼容）
4. 每个 Phase 的变更可独立提交，不影响其他 Phase
