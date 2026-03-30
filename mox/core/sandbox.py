"""Tool/MCP 沙箱 - 工具调用安全隔离

提供:
1. 工具权限控制
2. 调用参数验证
3. 执行结果过滤
4. 审计日志
"""

from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time
import secrets


class Permission(Enum):
    """权限级别"""

    NONE = "none"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class RiskLevel(Enum):
    """风险级别"""

    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ToolDefinition:
    """工具定义"""

    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_permissions: Set[Permission] = field(default_factory=set)
    allowed_roles: List[str] = field(default_factory=list)
    rate_limit_per_minute: int = 60
    timeout_seconds: float = 30.0
    dangerous: bool = False
    dangerous_reason: str = ""


@dataclass
class ToolCall:
    """工具调用记录"""

    call_id: str
    tool_name: str
    parameters: Dict[str, Any]
    caller: str
    timestamp: float
    risk_level: RiskLevel = RiskLevel.SAFE
    approved: bool = False
    result: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class ToolResult:
    """工具执行结果"""

    success: bool
    result: Any
    risk_level: RiskLevel
    filtered_fields: List[str] = field(default_factory=list)
    audit_info: Dict[str, Any] = field(default_factory=dict)


class ToolSandbox:
    """工具沙箱

    使用示例:
        sandbox = ToolSandbox()

        # 注册工具
        sandbox.register_tool(
            name="search",
            func=search_api,
            required_permissions={Permission.READ}
        )

        # 带权限检查的调用
        result = await sandbox.execute("search", {"query": "test"}, user_role="user")
    """

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.tool_implementations: Dict[str, Callable] = {}
        self.call_history: List[ToolCall] = []
        self.role_permissions: Dict[str, Set[Permission]] = {}

    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        required_permissions: Optional[Set[Permission]] = None,
        allowed_roles: Optional[List[str]] = None,
        rate_limit: int = 60,
        timeout: float = 30.0,
        dangerous: bool = False,
    ):
        """注册工具"""
        self.tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters or {},
            required_permissions=required_permissions or {Permission.READ},
            allowed_roles=allowed_roles or [],
            rate_limit_per_minute=rate_limit,
            timeout_seconds=timeout,
            dangerous=dangerous,
        )
        self.tool_implementations[name] = func

    def set_role_permissions(self, role: str, permissions: Set[Permission]):
        """设置角色权限"""
        self.role_permissions[role] = permissions

    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        caller: str = "anonymous",
        role: str = "user",
    ) -> ToolResult:
        """执行工具调用"""

        call_id = secrets.token_hex(6)

        call = ToolCall(
            call_id=call_id,
            tool_name=tool_name,
            parameters=parameters,
            caller=caller,
            timestamp=time.time(),
        )

        if tool_name not in self.tools:
            call.error = f"Tool not found: {tool_name}"
            self.call_history.append(call)
            return ToolResult(
                success=False,
                result=None,
                risk_level=RiskLevel.CRITICAL,
                audit_info={"error": call.error},
            )

        tool_def = self.tools[tool_name]

        can_execute, reason = self._check_permissions(tool_def, role)
        if not can_execute:
            call.error = f"Permission denied: {reason}"
            call.risk_level = RiskLevel.HIGH
            self.call_history.append(call)
            return ToolResult(
                success=False,
                result=None,
                risk_level=RiskLevel.HIGH,
                audit_info={"error": call.error, "reason": reason},
            )

        risk_level = self._assess_risk(tool_def, parameters)
        call.risk_level = risk_level

        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            call.error = f"High risk tool call blocked: {risk_level.value}"
            self.call_history.append(call)
            return ToolResult(
                success=False,
                result=None,
                risk_level=risk_level,
                audit_info={"error": call.error, "risk_level": risk_level.value},
            )

        try:
            start_time = time.time()

            func = self.tool_implementations[tool_name]

            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(**parameters), timeout=tool_def.timeout_seconds
                )
            else:
                result = func(**parameters)

            call.duration_ms = (time.time() - start_time) * 1000
            call.result = result
            call.approved = True

            filtered_result, filtered_fields = self._filter_result(result, tool_def)

            self.call_history.append(call)

            return ToolResult(
                success=True,
                result=filtered_result,
                risk_level=risk_level,
                filtered_fields=filtered_fields,
                audit_info={
                    "call_id": call_id,
                    "duration_ms": call.duration_ms,
                    "caller": caller,
                },
            )

        except asyncio.TimeoutError:
            call.error = f"Tool timeout after {tool_def.timeout_seconds}s"
            self.call_history.append(call)
            return ToolResult(
                success=False,
                result=None,
                risk_level=RiskLevel.MEDIUM,
                audit_info={"error": call.error},
            )
        except Exception as e:
            call.error = str(e)
            self.call_history.append(call)
            return ToolResult(
                success=False,
                result=None,
                risk_level=RiskLevel.MEDIUM,
                audit_info={"error": call.error},
            )

    def _check_permissions(
        self,
        tool_def: ToolDefinition,
        role: str,
    ) -> tuple[bool, str]:
        """检查权限"""

        if tool_def.allowed_roles and role not in tool_def.allowed_roles:
            return False, f"Role {role} not in allowed roles"

        role_perms = self.role_permissions.get(role, set())

        for required in tool_def.required_permissions:
            if required not in role_perms and Permission.ADMIN not in role_perms:
                return False, f"Missing permission: {required.value}"

        return True, ""

    def _assess_risk(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
    ) -> RiskLevel:
        """评估风险"""

        if tool_def.dangerous:
            return RiskLevel.CRITICAL

        dangerous_params = ["password", "secret", "token", "key", "admin"]
        if any(k.lower() in dangerous_params for k in parameters.keys()):
            return RiskLevel.MEDIUM

        if "exec" in str(parameters) or "eval" in str(parameters):
            return RiskLevel.HIGH

        return RiskLevel.SAFE

    def _filter_result(
        self,
        result: Any,
        tool_def: ToolDefinition,
    ) -> tuple[Any, List[str]]:
        """过滤结果中的敏感信息"""

        sensitive_fields = ["password", "token", "secret", "key", "api_key"]
        filtered = []

        if isinstance(result, dict):
            filtered_result = {}
            for key, value in result.items():
                if any(s in key.lower() for s in sensitive_fields):
                    filtered.append(key)
                    filtered_result[key] = "***REDACTED***"
                else:
                    filtered_result[key] = value
            return filtered_result, filtered

        return result, filtered

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取审计日志"""
        return [
            {
                "call_id": c.call_id,
                "tool_name": c.tool_name,
                "caller": c.caller,
                "timestamp": c.timestamp,
                "risk_level": c.risk_level.value,
                "approved": c.approved,
                "error": c.error,
            }
            for c in self.call_history[-limit:]
        ]


class MCPSandbox:
    """MCP (Model Context Protocol) 沙箱"""

    def __init__(self):
        self.sandbox = ToolSandbox()
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(
        self,
        session_id: str,
        role: str = "user",
        permissions: Optional[Set[Permission]] = None,
    ) -> str:
        """创建会话"""
        self.sessions[session_id] = {
            "role": role,
            "permissions": permissions or {Permission.READ},
            "created_at": time.time(),
            "tool_calls": 0,
        }

        if permissions:
            self.sandbox.set_role_permissions(role, permissions)

        return session_id

    async def call_tool(
        self,
        session_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> ToolResult:
        """会话中调用工具"""

        session = self.sessions.get(session_id)
        if not session:
            return ToolResult(
                success=False,
                result=None,
                risk_level=RiskLevel.CRITICAL,
                audit_info={"error": "Invalid session"},
            )

        session["tool_calls"] += 1

        return await self.sandbox.execute(
            tool_name=tool_name,
            parameters=parameters,
            caller=session_id,
            role=session["role"],
        )

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return self.sessions.get(session_id)


__all__ = [
    "ToolSandbox",
    "MCPSandbox",
    "ToolDefinition",
    "ToolCall",
    "ToolResult",
    "Permission",
    "RiskLevel",
]
