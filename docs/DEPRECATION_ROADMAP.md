# Deprecation Roadmap: 重复版本文件清理

## 背景

`mox/` 包在迭代过程中形成了多组平行的"版本文件"（`xxx.py` / `xxx_v2.py` /
`xxx_v3.py`）。这导致：

- `mox/attacks/__init__.py` 导出 **150+ 个符号**，含大量"向后兼容别名"
  （例如 `GCGAttack` / `GCGAttackBasic` / `GCGAttackGradient`、
  `SkeletonKeyAttack` / `SkeletonKeyAttackV2`）。
- 新用户无法判断哪个类是"当前推荐实现"。
- 同一概念的多套实现长期并存，维护成本与 bug 面积翻倍。

由于这些文件已被 `__init__.py`、`routes/api_v2.py`、`ui.py`、
`core/scheduler.py` 及 25+ 测试深度引用，**不能一次性删除**。
本文件给出分阶段、可回滚的迁移计划。

## 原则

1. **保留功能最完整的版本作为"规范实现"**（canonical），通常是最新的 `_v3`
   或行数最多、被引用最多的版本。
2. **旧版本不立即删除**，而是：
   - 在模块顶部加 `warnings.warn(..., DeprecationWarning)`
   - 改为从规范实现 re-export（保持导入路径可用）
   - 在 `__init__.py` 的"兼容别名"旁标注 `# deprecated since vX.Y`
3. **至少经过一个 minor 版本**的 deprecation 期后才删除文件。
4. 每个阶段独立可交付、可测试、可回滚。

## 待清理文件清单与处置

| 文件 | 行数 | 规范实现 | 处置 | 阶段 |
|------|------|----------|------|------|
| `attacks/novel_attacks.py` | 519 | `novel_attacks_v3.py` | 标记 deprecated → re-export → 删除 | 1 |
| `attacks/novel_attacks_v2.py` | 505 | `novel_attacks_v3.py` | 标记 deprecated → re-export → 删除 | 1 |
| `attacks/novel_attacks_v3.py` | 994 | **(规范)** | 重命名为 `novel_attacks.py` | 1 |
| `attacks/advanced_attacks.py` | 1033 | **(规范)** | 保留，吸收 `_v2` 独有内容 | 2 |
| `attacks/advanced_attacks_v2.py` | 465 | `advanced_attacks.py` | 独有类(PAIR/DeepInception/Crescendo)迁入规范 → re-export → 删除 | 2 |
| `attacks/agent_attacks.py` | 354 | **(规范)** | 保留，吸收 `_v2` 独有内容 | 3 |
| `attacks/agent_attacks_v2.py` | 1066 | `agent_attacks.py` | 独有类迁入规范 → re-export → 删除 | 3 |
| `evaluation/benchmarks.py` | 536 | `benchmarks_v2.py` | 标记 deprecated → re-export → 删除 | 4 |
| `evaluation/benchmarks_v2.py` | 642 | **(规范)** | 重命名为 `benchmarks.py` | 4 |
| `core/database_ext.py` | 420 | `database.py` | 独有功能并入 `database.py` → re-export → 删除 | 5 |

## 执行阶段

### 阶段 1：合并 novel_attacks（示例模板，其他阶段照此执行）

**目标**：`novel_attacks_v3.py` 成为唯一的 `novel_attacks.py`。

**步骤**：

1. **差异分析**：对比 v2/v3 导出的类，确认 v3 完全覆盖 v2 的公开 API。
   - `ManyShotJailbreak`(v2) → `ManyShotJailbreakAttack`(v3)
   - `SkeletonKeyAttack`(v2) → `SkeletonKeyAttack`(v3)
   - 若有 v2 独有的公开方法，先迁入 v3。

2. **加 deprecation 到旧文件**（`novel_attacks.py`、`novel_attacks_v2.py`）：
   ```python
   import warnings
   warnings.warn(
       "mox.attacks.novel_attacks_v2 is deprecated; "
       "use mox.attacks.novel_attacks_v3 (will be renamed to novel_attacks).",
       DeprecationWarning,
       stacklevel=2,
   )
   ```
   并把旧实现替换为从 v3 的 re-export，保持导入路径不破。

3. **更新引用方**（一次性 PR）：
   - `mox/attacks/__init__.py:167-191` —— 移除 v2 导入，统一从 v3 导入；
     `SkeletonKeyAttackV2` / `ManyShotExampleV2` 等别名改为指向 v3 实现，
     标注 `# deprecated alias, remove in vX.Y+1`。
   - `tests/test_missing_modules.py:83,92,105-159` —— 更新导入路径。

4. **删除旧文件**（在下一个 minor 版本，即至少一个版本周期后）：
   删除 `novel_attacks.py`(旧)、`novel_attacks_v2.py`，
   将 `novel_attacks_v3.py` 重命名为 `novel_attacks.py`，
   全局更新导入。

5. **验证**：`pytest tests/` 全绿；`python -c "import mox.attacks"` 无警告外的报错。

### 阶段 2-5

每个阶段遵循"差异分析 → deprecation + re-export → 更新引用 → 跨版本删除"
的相同四步。建议**每阶段一个 PR**，便于 review 与回滚。

阶段间无强依赖，可并行规划，但建议按 1→2→3→4→5 顺序，因为阶段 1
验证过的模板可复用。

## 别名清理（`__init__.py`）

`attacks/__init__.py` 当前的兼容别名（`__all__` 中标记向后的）：

| 别名 | 实际指向 | 处置 |
|------|----------|------|
| `GCGAttack` | `GCGAttackGradient` | 保留为主名称，废弃 `GCGAttackBasic` |
| `GCGAttackBasic` | `gcg.GCGAttack` | deprecated，阶段外删除 |
| `KnowledgeDistillationAttack` | `KnowledgeExtractionAttack` | deprecated |
| `KnowledgeDistillationAttackV2` | `knowledge_extraction.KnowledgeDistillationAttack` | deprecated |
| `SkeletonKeyAttackV2` | v2 实现 | 阶段 1 后指向 v3，后续删除 |
| `ManyShotExampleV2` | v2 实现 | 阶段 1 后指向 v3，后续删除 |
| `MultimodalAdversarialAttack` | `TextBasedAdversarialAttack` | deprecated |
| `BenchmarkCaseV2` | `benchmarks_v2.BenchmarkCase` | 阶段 4 后改主名称 |

每个别名在 deprecation 期保留，在下个 minor 版本的"清理 PR"中统一移除。

## 验收标准

每个阶段合并前必须满足：

- [ ] `pytest tests/` 全部通过
- [ ] `python -c "import mox; import mox.attacks; import mox.evaluation"` 无报错
- [ ] `ruff check mox/` 无新增告警
- [ ] `mypy mox/` 无新增类型错误
- [ ] CHANGELOG 记录 deprecation 与计划移除版本号

## 时间线建议

- **v0.4.0**：完成阶段 1-2 的 deprecation + re-export（旧文件仍可导入但有警告）
- **v0.5.0**：完成阶段 3-4 的 deprecation + re-export
- **v0.6.0**：物理删除所有标记为 deprecated 的文件与别名
- **v1.0.0**：API 表面收敛完成，`attacks/__init__.py` 导出符号数减半

## 备注

- `core/database_ext.py` 的引用方（`audit.py`、`cicd.py`、`scheduler.py`）
  使用函数级延迟导入（`from mox.core.database_ext import ...`），合并时
  只需保证目标函数在 `database.py` 可用即可。
- `routes/api_v2.py` 与 `ui.py` 对 `_v2/_v3` 模块也是函数/方法内导入，
  重命名后用全局替换即可更新。
