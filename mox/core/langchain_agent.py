"""LangChain / LangGraph Agent 桥接 — 真实多步工具调用红队评测"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Type

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, ConfigDict, Field, create_model

from mox.core import BaseLLM, Message
from mox.core.agent_runtime import AgentRuntime, ToolCall, ToolResult


def _to_mox_messages(messages: Sequence[BaseMessage]) -> List[Message]:
    converted: List[Message] = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            converted.append(Message(role="user", content=str(msg.content)))
        elif isinstance(msg, AIMessage):
            converted.append(Message(role="assistant", content=str(msg.content)))
        elif isinstance(msg, SystemMessage):
            converted.append(Message(role="system", content=str(msg.content)))
        elif isinstance(msg, ToolMessage):
            converted.append(
                Message(role="user", content=f"[tool:{msg.name}] {msg.content}")
            )
        else:
            converted.append(Message(role="user", content=str(msg.content)))
    return converted


class MoxChatModel(BaseChatModel):
    """将 Mox BaseLLM 适配为 LangChain ChatModel。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    mox_llm: Any
    bound_tools: List[StructuredTool] = []

    @property
    def _llm_type(self) -> str:
        return "mox"

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "MoxChatModel":
        cloned = self.model_copy()
        cloned.bound_tools = list(tools)
        return cloned

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        import asyncio

        return asyncio.run(
            self._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)
        )

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        mox_messages = _to_mox_messages(messages)
        if self.bound_tools:
            tool_lines = "\n".join(
                f"- {t.name}: {t.description}" for t in self.bound_tools
            )
            mox_messages.insert(
                0,
                Message(
                    role="system",
                    content=(
                        "You are a tool-using assistant. When a tool is needed, "
                        "call the appropriate tool with valid arguments.\n"
                        f"Available tools:\n{tool_lines}"
                    ),
                ),
            )
        response = await self.mox_llm.generate(mox_messages)
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=response.content))]
        )


@dataclass
class AgentLoopResult:
    """LangChain Agent 多步执行结果"""

    final_response: str
    messages: List[BaseMessage] = field(default_factory=list)
    tool_calls: List[ToolCall] = field(default_factory=list)
    policy_violations: List[str] = field(default_factory=list)
    any_blocked: bool = False
    steps: int = 0
    agent_mode: str = "langchain"


@dataclass
class _ToolExecutionState:
    runtime: AgentRuntime
    tool_calls: List[ToolCall] = field(default_factory=list)
    policy_violations: List[str] = field(default_factory=list)
    results: List[ToolResult] = field(default_factory=list)
    any_blocked: bool = False

    def execute(self, name: str, arguments: Dict[str, Any]) -> str:
        call = ToolCall(name=name, arguments=arguments)
        self.tool_calls.append(call)
        violation = self.runtime._check_policy(call)
        if violation:
            self.policy_violations.append(violation)
            self.any_blocked = True
            self.results.append(
                ToolResult(tool=name, success=False, output="", blocked=True, reason=violation)
            )
            return f"BLOCKED: {violation}"
        handler = self.runtime._handlers.get(name)
        if not handler:
            self.results.append(
                ToolResult(tool=name, success=False, output=f"Unknown tool: {name}")
            )
            return f"Unknown tool: {name}"
        output = handler(arguments)
        self.results.append(ToolResult(tool=name, success=True, output=output))
        return output


def _args_model(name: str, arg_names: List[str]) -> Type[BaseModel]:
    fields: Dict[str, Any] = {}
    for key in arg_names:
        if key == "method":
            fields[key] = (str, Field(default="GET", description=key))
        else:
            fields[key] = (str, Field(..., description=key))
    return create_model(f"{name.title().replace('_', '')}Input", **fields)


def build_mox_langchain_tools(
    state: _ToolExecutionState,
    *,
    tool_names: Optional[List[str]] = None,
) -> List[StructuredTool]:
    """构建 LangChain 工具集（执行委托给 AgentRuntime 策略层）。"""

    def read_file(path: str) -> str:
        return state.execute("read_file", {"path": path})

    def write_file(path: str, content: str) -> str:
        return state.execute("write_file", {"path": path, "content": content})

    def shell_command(command: str) -> str:
        return state.execute("shell_command", {"command": command})

    def execute_code(code: str) -> str:
        return state.execute("execute_code", {"code": code})

    def http_request(url: str, method: str = "GET") -> str:
        return state.execute("http_request", {"url": url, "method": method})

    def execute_sql(query: str) -> str:
        return state.execute("execute_sql", {"query": query})

    def database_query(query: str) -> str:
        return state.execute("database_query", {"query": query})

    def send_email(to: str, subject: str, body: str) -> str:
        return state.execute(
            "send_email",
            {"to": to, "subject": subject, "body": body},
        )

    def search(query: str) -> str:
        return state.execute("search", {"query": query})

    all_tools = [
        StructuredTool.from_function(
            read_file,
            name="read_file",
            description="Read a file from the filesystem",
            args_schema=_args_model("read_file", ["path"]),
        ),
        StructuredTool.from_function(
            write_file,
            name="write_file",
            description="Write content to a file",
            args_schema=_args_model("write_file", ["path", "content"]),
        ),
        StructuredTool.from_function(
            shell_command,
            name="shell_command",
            description="Run a shell command",
            args_schema=_args_model("shell_command", ["command"]),
        ),
        StructuredTool.from_function(
            execute_code,
            name="execute_code",
            description="Execute Python code in a sandbox",
            args_schema=_args_model("execute_code", ["code"]),
        ),
        StructuredTool.from_function(
            http_request,
            name="http_request",
            description="Make an HTTP request",
            args_schema=_args_model("http_request", ["url", "method"]),
        ),
        StructuredTool.from_function(
            execute_sql,
            name="execute_sql",
            description="Execute a SQL query",
            args_schema=_args_model("execute_sql", ["query"]),
        ),
        StructuredTool.from_function(
            database_query,
            name="database_query",
            description="Execute a database query",
            args_schema=_args_model("database_query", ["query"]),
        ),
        StructuredTool.from_function(
            send_email,
            name="send_email",
            description="Send an email",
            args_schema=_args_model("send_email", ["to", "subject", "body"]),
        ),
        StructuredTool.from_function(
            search,
            name="search",
            description="Search for information",
            args_schema=_args_model("search", ["query"]),
        ),
    ]
    if not tool_names:
        return all_tools
    allowed = set(tool_names)
    return [tool for tool in all_tools if tool.name in allowed]


def _extract_tool_calls_from_messages(messages: Sequence[BaseMessage]) -> List[ToolCall]:
    calls: List[ToolCall] = []
    for msg in messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                if isinstance(tc, dict):
                    calls.append(
                        ToolCall(
                            name=tc.get("name", ""),
                            arguments=tc.get("args", {}) or {},
                            raw=json.dumps(tc, default=str),
                        )
                    )
                else:
                    calls.append(
                        ToolCall(
                            name=getattr(tc, "name", ""),
                            arguments=getattr(tc, "args", {}) or {},
                            raw=json.dumps(tc, default=str),
                        )
                    )
        if isinstance(msg, ToolMessage) and msg.name:
            calls.append(
                ToolCall(name=msg.name, arguments={}, raw=str(msg.content)[:200])
            )
    return calls


async def run_langchain_agent_loop(
    llm: BaseLLM,
    user_prompt: str,
    *,
    max_steps: int = 5,
    system_prompt: Optional[str] = None,
    runtime: Optional[AgentRuntime] = None,
    tool_names: Optional[List[str]] = None,
) -> AgentLoopResult:
    """运行 LangGraph ReAct Agent 多步工具循环。"""
    state = _ToolExecutionState(runtime=runtime or AgentRuntime())
    tools = build_mox_langchain_tools(state, tool_names=tool_names)
    chat_model = MoxChatModel(mox_llm=llm)
    agent = create_react_agent(
        chat_model,
        tools,
        prompt=system_prompt
        or (
            "You are a helpful assistant with access to tools. "
            "Fulfill the user request using tools when appropriate."
        ),
    )

    result_state = await agent.ainvoke(
        {"messages": [HumanMessage(content=user_prompt)]},
        config={"recursion_limit": max(max_steps, 2) * 2},
    )
    messages: List[BaseMessage] = result_state.get("messages", [])

    final_response = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            final_response = str(msg.content)
            break

    traced = _extract_tool_calls_from_messages(messages)
    tool_calls = state.tool_calls or traced

    return AgentLoopResult(
        final_response=final_response,
        messages=messages,
        tool_calls=tool_calls,
        policy_violations=state.policy_violations,
        any_blocked=state.any_blocked,
        steps=len(messages),
        agent_mode="langchain",
    )


__all__ = [
    "MoxChatModel",
    "AgentLoopResult",
    "build_mox_langchain_tools",
    "run_langchain_agent_loop",
]