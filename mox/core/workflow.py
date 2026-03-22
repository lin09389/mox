"""Plan-then-Execute 工作流引擎

安全的 Agent 工作流模式:
1. 计划阶段 - LLM 生成行动计划
2. 验证阶段 - 验证计划安全性 (使用 AST 解析)
3. 执行阶段 - 执行经批准的计划
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
import ast
import re

from mox.core import BaseLLM, Message


class PlanStatus(Enum):
    """计划状态"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(Enum):
    """步骤状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionStep:
    """执行步骤"""

    step_id: str
    action: str
    tool: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_result: Optional[str] = None
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class ExecutionPlan:
    """执行计划"""

    plan_id: str
    goal: str
    steps: List[ExecutionStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    reasoning: str = ""
    approved: bool = False
    approver: Optional[str] = None
    created_at: float = 0.0
    completed_at: Optional[float] = None


@dataclass
class WorkflowResult:
    """工作流结果"""

    success: bool
    plan: ExecutionPlan
    final_result: Optional[Any] = None
    executed_steps: int = 0
    total_duration_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


ToolExecutor = Callable[[str, Dict[str, Any]], Any]


class PlanThenExecuteEngine:
    """Plan-then-Execute 引擎

    使用示例:
        engine = PlanThenExecuteEngine(llm)

        # 定义可用工具
        engine.register_tool("search", search_function)
        engine.register_tool("calculate", calculate_function)

        # 执行工作流
        result = await engine.execute("帮我查一下北京的天气并计算华氏温度")
    """

    def __init__(
        self,
        llm: BaseLLM,
        system_prompt: Optional[str] = None,
        require_approval: bool = True,
        max_steps: int = 10,
    ):
        self.llm = llm
        self.require_approval = require_approval
        self.max_steps = max_steps
        self.tools: Dict[str, ToolExecutor] = {}
        self.tool_schemas: Dict[str, Dict[str, Any]] = {}

        self.system_prompt = system_prompt or self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        return """你是一个安全的任务规划器。
        
你必须:
1. 将复杂任务分解为简单的步骤
2. 只使用提供的工具
3. 每个步骤必须是具体可执行的
4. 验证每个步骤的安全性

工具调用格式:
```json
{
    "step_id": "step_1",
    "action": "tool_name",
    "parameters": {"key": "value"}
}
```"""

    def register_tool(
        self,
        name: str,
        func: ToolExecutor,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """注册工具"""
        self.tools[name] = func
        self.tool_schemas[name] = {
            "name": name,
            "description": description or func.__doc__ or "",
            "parameters": parameters or {},
        }

    def _build_planning_prompt(self, user_request: str) -> str:
        tools_desc = "\n".join(
            [f"- {name}: {schema['description']}" for name, schema in self.tool_schemas.items()]
        )

        return f"""用户请求: {user_request}

可用工具:
{tools_desc}

请生成执行计划。返回JSON格式:
{{
    "goal": "任务目标",
    "reasoning": "你的思考过程",
    "steps": [
        {{
            "step_id": "step_1",
            "action": "tool_name",
            "parameters": {{}},
            "expected_result": "预期结果"
        }}
    ]
}}"""

    async def plan(self, user_request: str) -> ExecutionPlan:
        """生成执行计划"""

        prompt = self._build_planning_prompt(user_request)

        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=prompt),
        ]

        response = await self.llm.generate(messages)

        try:
            parsed = json.loads(response.content)
        except json.JSONDecodeError:
            import re

            match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
            else:
                parsed = {"goal": user_request, "reasoning": "Parse failed", "steps": []}

        steps = [
            ExecutionStep(
                step_id=s.get("step_id", f"step_{i}"),
                action=s.get("action", ""),
                parameters=s.get("parameters", {}),
                expected_result=s.get("expected_result"),
            )
            for i, s in enumerate(parsed.get("steps", [])[: self.max_steps])
        ]

        return ExecutionPlan(
            plan_id=f"plan_{hash(user_request) % 100000}",
            goal=parsed.get("goal", user_request),
            steps=steps,
            reasoning=parsed.get("reasoning", ""),
            created_at=asyncio.get_event_loop().time(),
        )

    async def validate_plan(self, plan: ExecutionPlan) -> tuple[bool, str]:
        """验证计划安全性 - 使用 AST 解析和模式匹配"""

        invalid_actions = []
        for step in plan.steps:
            if step.action not in self.tools:
                invalid_actions.append(step.action)

        if invalid_actions:
            return False, f"Unknown tools: {invalid_actions}"

        dangerous_patterns = [
            "exec(",
            "eval(",
            "os.system",
            "subprocess",
            "delete",
            "drop",
            "truncate",
            "rm -rf",
        ]

        for step in plan.steps:
            action_str = str(step.action) + str(step.parameters)
            if any(p in action_str.lower() for p in dangerous_patterns):
                return False, f"Dangerous action detected: {step.action}"

        for step in plan.steps:
            is_safe, reason = self._validate_parameters(step.action, step.parameters)
            if not is_safe:
                return False, f"Unsafe parameters in {step.action}: {reason}"

        return True, "Plan validated"

    def _validate_parameters(self, action: str, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """使用 AST 解析验证参数安全性"""

        dangerous_funcs = {
            "exec",
            "eval",
            "compile",
            "open",
            "write",
            "read",
            "__import__",
            "getattr",
            "setattr",
            "delattr",
        }

        dangerous_modules = {
            "os",
            "sys",
            "subprocess",
            "socket",
            "requests",
            "urllib",
            "http",
            "ftplib",
            "telnetlib",
        }

        for key, value in parameters.items():
            if isinstance(value, str):
                if self._contains_dangerous_code(value, dangerous_funcs, dangerous_modules):
                    return False, f"Dangerous code in parameter '{key}'"

                if len(value) > 10000:
                    return False, f"Parameter '{key}' exceeds length limit"

            elif isinstance(value, dict):
                for k, v in value.items():
                    if isinstance(v, str):
                        if self._contains_dangerous_code(v, dangerous_funcs, dangerous_modules):
                            return False, f"Dangerous code in nested parameter '{key}.{k}'"

        return True, ""

    def _contains_dangerous_code(
        self, code_str: str, dangerous_funcs: set, dangerous_modules: set
    ) -> bool:
        """检测代码字符串中是否包含危险模式"""

        if not code_str or len(code_str) < 5:
            return False

        dangerous_patterns = [
            r"__import__\s*\(",
            r"eval\s*\(",
            r"exec\s*\(",
            r"compile\s*\(",
            r'open\s*\([^)]*[\'"][wr][^\'"]*[\'"]',
            r"subprocess\.(call|run|Popen)",
            r"os\.system",
            r"os\.popen",
            r"socket\.",
            r"\.send\(",
            r"urllib\.",
            r"requests\.",
            r"<script",
            r"javascript:",
            r"on\w+\s*=",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, code_str, re.IGNORECASE):
                return True

        try:
            tree = ast.parse(code_str, mode="eval")
            return self._check_ast_dangerous(tree, dangerous_funcs, dangerous_modules)
        except SyntaxError:
            pass

        return False

    def _check_ast_dangerous(
        self, tree: ast.AST, dangerous_funcs: set, dangerous_modules: set
    ) -> bool:
        """使用 AST 检查危险模式"""

        class DangerousChecker(ast.NodeVisitor):
            def __init__(self):
                self.is_dangerous = False

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    if node.func.id in dangerous_funcs:
                        self.is_dangerous = True
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id in dangerous_modules:
                            self.is_dangerous = True
                self.generic_visit(node)

            def visit_Import(self, node):
                for alias in node.names:
                    if alias.name in dangerous_modules:
                        self.is_dangerous = True
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                if node.module and any(m in node.module for m in dangerous_modules):
                    self.is_dangerous = True
                self.generic_visit(node)

        checker = DangerousChecker()
        checker.visit(tree)
        return checker.is_dangerous

    async def execute_plan(
        self,
        plan: ExecutionPlan,
        approval_callback: Optional[Callable[[ExecutionPlan], bool]] = None,
    ) -> WorkflowResult:
        """执行计划"""

        import time

        start_time = time.time()

        valid, reason = await self.validate_plan(plan)
        if not valid:
            plan.status = PlanStatus.REJECTED
            return WorkflowResult(
                success=False,
                plan=plan,
                errors=[reason],
                metadata={"validation_failed": True},
            )

        if self.require_approval:
            approved = False
            if approval_callback:
                approved = approval_callback(plan)
            else:
                approved = True

            if not approved:
                plan.status = PlanStatus.REJECTED
                return WorkflowResult(
                    success=False,
                    plan=plan,
                    errors=["Plan not approved"],
                    metadata={"approval_required": True},
                )

        plan.status = PlanStatus.APPROVED
        plan.approved = True

        results = []
        errors = []
        executed = 0

        for step in plan.steps:
            step_start = time.time()
            step.status = StepStatus.RUNNING

            try:
                if step.action in self.tools:
                    tool_func = self.tools[step.action]
                    result = await tool_func(**step.parameters)
                    step.result = result
                    step.status = StepStatus.COMPLETED
                    results.append(result)
                    executed += 1
                else:
                    step.error = f"Tool not found: {step.action}"
                    step.status = StepStatus.FAILED
                    errors.append(step.error)

            except Exception as e:
                step.error = str(e)
                step.status = StepStatus.FAILED
                errors.append(str(e))

            step.duration_ms = (time.time() - step_start) * 1000

        duration = (time.time() - start_time) * 1000

        plan.status = PlanStatus.COMPLETED if not errors else PlanStatus.FAILED
        plan.completed_at = time.time()

        return WorkflowResult(
            success=len(errors) == 0,
            plan=plan,
            final_result=results[-1] if results else None,
            executed_steps=executed,
            total_duration_ms=duration,
            errors=errors,
        )

    async def execute(
        self,
        user_request: str,
        approval_callback: Optional[Callable[[ExecutionPlan], bool]] = None,
    ) -> WorkflowResult:
        """完整的计划-执行流程"""

        plan = await self.plan(user_request)
        return await self.execute_plan(plan, approval_callback)


class AgenticWorkflow:
    """Agent 工作流 - 带反思能力"""

    def __init__(
        self,
        llm: BaseLLM,
        max_iterations: int = 3,
    ):
        self.llm = llm
        self.max_iterations = max_iterations

    async def run_with_reflection(
        self,
        user_request: str,
        execute_func: Callable,
    ) -> Dict[str, Any]:
        """带反思的执行"""

        for iteration in range(self.max_iterations):
            response = await execute_func(user_request)

            reflection_prompt = f"""分析以下响应是否正确完成了任务:

任务: {user_request}
响应: {response}

如果有问题，说明需要重试的原因。如果没有问题，返回 "APPROVED"。"""

            messages = [Message(role="user", content=reflection_prompt)]
            reflection = await self.llm.generate(messages)

            if "APPROVED" in reflection.content.upper():
                return {
                    "response": response,
                    "iterations": iteration + 1,
                    "approved": True,
                }

        return {
            "response": response,
            "iterations": self.max_iterations,
            "approved": False,
        }


__all__ = [
    "PlanThenExecuteEngine",
    "AgenticWorkflow",
    "ExecutionPlan",
    "ExecutionStep",
    "WorkflowResult",
    "PlanStatus",
    "StepStatus",
]
