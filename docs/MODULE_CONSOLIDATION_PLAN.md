# P2 模块合并方案（defense / evaluation）

基于对 `mox/defense/`（13 文件，~5700 行）和 `mox/evaluation/`（17 文件，~9900 行）
的完整依赖图分析。本方案分 **5 个阶段**，每阶段独立可提交、可验证、可回滚。

## 调查结论速览

### 死代码（零生产引用，可安全删除）

| 文件 | 行数 | 唯一引用 | 处置 |
|------|------|----------|------|
| `defense/enhanced_filter.py` | 773 | 仅 `tests/test_enhanced_defense.py`，未导出 | 删除 + 删测试 |
| `evaluation/extended_benchmarks.py` | 138 | **零引用**（连测试都没有） | 删除 |
| `evaluation/multi_dim_evaluator.py` | 541 | **零引用** | 删除 |

合计 **1452 行**死代码。

### 命名冲突（`__init__.py` 用 `as` 别名掩盖）

| 符号 | 定义位置 | `__init__.py` 实际导出 |
|------|----------|------------------------|
| `EvaluationResult` | attack_evaluator / benchmarks / framework | framework 的（最后导入覆盖） |
| `EvaluationConfig` | attack_evaluator / framework | framework 的 |
| `AttackEvaluator` | evaluator / attack_evaluator | attack_evaluator 的（`as EnhancedAttackEvaluator` 后别名） |
| `BenchmarkCase` | benchmarks / benchmarks_v2 / datasets | benchmarks 的（V2/Dataset 加后缀） |
| `LLMJudge` | defense/llm_judge + evaluation/judge | 两个都导出（不同模块） |
| `MaliciousPattern` | input_filter / enhanced_filter | input_filter 的 |

### 重叠模块组（功能分析后的合并策略）

经阅读源码，这些"重叠"组实际上是**层级递进**而非纯重复：

- **输出检测**：`output_filter`（正则+关键词，快速）vs `output_validator`（12 类 PII 精细检测）→ **互补，保留两者**，仅统一结果类型
- **判官**：`judge`（LLM 判官）vs `perplexity_judge`（困惑度+稳定判官）→ **互补**，perplexity 是独立能力
- **评估器**：`evaluator`（基础指标）→ `attack_evaluator`（增强）→ `framework`（统一编排）→ **递进**，解决 EvaluationConfig/Result 冲突即可
- **输入检测**：`input_filter` + `injection_detector` + `semantic_firewall` → 三者角度不同（模式/注入语义/意图），**保留分工**

**重要结论**：真正需要"合并"的不多，大部分是**命名冲突治理 + 死代码清理**。
强行合并互补模块反而会损失功能。

---

## 阶段 1：删除死代码（零风险）

**目标**：移除 3 个零引用文件，减 1452 行。

**操作**：
1. 删除 `mox/defense/enhanced_filter.py`（773 行）
2. 删除 `mox/evaluation/extended_benchmarks.py`（138 行）
3. 删除 `mox/evaluation/multi_dim_evaluator.py`（541 行）
4. 删除 `tests/test_enhanced_defense.py`（仅测被删的 enhanced_filter）
5. 确认 `__init__.py` 未引用这三个文件（已确认）
6. 运行 `pytest tests/` 确认无回归

**风险**：极低。三个文件均未在 `__init__.py` 导出，无生产代码引用。

**验证**：`pytest tests/` 全绿 + `python -c "import mox"` 无报错。

---

## 阶段 2：治理 evaluation 命名冲突（中风险）

**问题**：`EvaluationResult` / `EvaluationConfig` 在多个文件重复定义，
`__init__.py` 的导入顺序决定了"谁覆盖谁"，这是脆弱的。

**策略**：确立 `framework.py` 为规范定义，其他文件改为 re-export。

**操作**：
1. `framework.py` 保留 `EvaluationConfig` / `EvaluationResult` 的规范定义
2. `attack_evaluator.py` 删除自己的 `EvaluationConfig`/`EvaluationResult`，
   改为 `from mox.evaluation.framework import EvaluationConfig, EvaluationResult`
   （若字段不同则先合并字段）
3. `benchmarks.py:443` 的 `EvaluationResult` 删除，改为从 framework 导入
4. `evaluation/__init__.py`：清理重复导入，确保每个符号只从规范位置导出一次
5. 更新外部引用（`attack_evaluator` 的 `EvaluationConfig` 被
   `mox/attacks/improved_gcg.py` 引用，需确认导入路径不变）

**风险**：中等。需确认三个 `EvaluationResult` 的字段差异，合并时不能丢字段。

**验证**：`pytest tests/test_attack_evaluator.py tests/test_attack_evaluation.py tests/test_evaluation_improvements.py`

---

## 阶段 3：收敛 evaluator 三件套（中风险）

**目标**：明确 `evaluator.py` / `attack_evaluator.py` / `framework.py` 的职责边界。

**策略**（保留分工，消除歧义）：
1. `evaluator.py`：保留为**基础指标层**（`EvaluationMetrics`、`AttackTypeMetrics`、
   简单 `AttackEvaluator`/`DefenseEvaluator`/`RobustnessEvaluator`）
   - 但其 `AttackEvaluator` 与 attack_evaluator 的同名 → 重命名为
     `BasicAttackEvaluator`，加 deprecation 别名
2. `attack_evaluator.py`：保留为**增强评估层**（`AttackEvaluator` 为主名称）
3. `framework.py`：保留为**统一编排层**（`UnifiedEvaluator`）
4. `__init__.py`：导出注释明确三层关系，消除"哪个 AttackEvaluator"的困惑

**风险**：`evaluator.py` 的 `AttackEvaluator` 被 `mox/__init__.py` 间接导出，
重命名需更新 `__init__.py` 链。有 deprecation 期保护。

**验证**：全量 `pytest tests/` + `python -c "from mox.evaluation import AttackEvaluator"`。

---

## 阶段 4：defense 输入检测去歧义（低风险）

**目标**：明确 `input_filter` / `injection_detector` / `semantic_firewall` 的分工。

**分析**：三者实际职责不同，不需合并，但需文档化边界：
- `input_filter`：通用恶意模式检测（正则+关键词+困惑度），入口级
- `injection_detector`：专注 Prompt Injection 语义检测（多语言/编码/多层）
- `semantic_firewall`：意图分类 + 风险评分（语义级）

**操作**：
1. 在 `defense/__init__.py` 加分组注释，说明三者分工
2. 检查 `MaliciousPattern` 是否在 enhanced_filter 删除后仍冲突
   （阶段 1 删了 enhanced_filter 后只剩 input_filter 一处，冲突自动消失）
3. 更新 `defense/README.md`（若存在）或 docstring 说明选择指引

**风险**：低。主要是文档/注释工作，不改逻辑。

**验证**：`pytest tests/` + `python -c "import mox.defense"`。

---

## 阶段 5：输出检测统一结果类型（低风险）

**目标**：`output_filter` 与 `output_validator` 结果类型统一。

**分析**：两者互补（快速正则 vs 精细 PII），保留两者，但
`OutputValidationResult`（output_validator）与 `DefenseResult`（base）
是两套结果类型，使用方需分别处理。

**操作**：
1. 让 `OutputValidator` 返回的 `OutputValidationResult` 继承或兼容 `DefenseResult`
   （增加 `is_malicious`/`confidence`/`detected_patterns` 适配属性）
2. 或提供 `to_defense_result()` 转换方法
3. 更新 `routes/api_v2.py`（同时引用了两者）的调用方式

**风险**：低。新增适配，不破坏现有接口。

**验证**：`pytest tests/` + 手动验证 `/api/v2/defense` 端点。

---

## 执行顺序与提交策略

| 阶段 | 风险 | 独立提交 | 建议顺序 |
|------|------|----------|----------|
| 1 删死代码 | 极低 | ✅ 单独提交 | 第 1 步 |
| 2 评估命名冲突 | 中 | ✅ 单独提交 | 第 2 步 |
| 3 evaluator 收敛 | 中 | ✅ 单独提交 | 第 3 步 |
| 4 输入检测去歧义 | 低 | ✅ 单独提交 | 第 4 步 |
| 5 输出结果统一 | 低 | ✅ 单独提交 | 第 5 步 |

**每阶段提交前必须**：
- [ ] `pytest tests/` 全绿
- [ ] `python -c "import mox; import mox.defense; import mox.evaluation"` 无报错
- [ ] `ruff check mox/` 无新增告警
- [ ] CHANGELOG 记录

## 修订说明

原报告认为需要"合并 defense 下 8+ 重叠过滤器"，但源码分析显示这些模块
多为**互补/递进**关系而非纯重复。本方案聚焦于：
1. 真正的死代码清理（阶段 1，立竿见影）
2. 命名冲突治理（阶段 2-3，消除歧义）
3. 文档化分工（阶段 4-5，降低认知负担）

避免了"为合并而合并"导致功能损失的风险。
