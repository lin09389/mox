"""LangGraph 防御工作流

使用 LangGraph 实现多层防御工作流，支持：
- 多阶段检测
- 自适应防御策略
- 实时响应
- 审计日志
"""

from typing import Annotated, TypedDict, Literal, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from mox.core import BaseLLM, Message
from mox.defense import (
    InputFilter,
    OutputFilter,
    LLMJudge,
    PerplexityFilter,
)


class DefensePhase(str, Enum):
    """防御阶段"""

    INPUT_ANALYSIS = "input_analysis"
    THREAT_DETECTION = "threat_detection"
    RESPONSE_GENERATION = "response_generation"
    OUTPUT_FILTERING = "output_filtering"
    AUDIT_LOGGING = "audit_logging"


class ThreatLevel(str, Enum):
    """威胁等级"""

    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WorkflowDefenseResult:
    """防御工作流结果"""

    is_safe: bool
    threat_level: ThreatLevel
    detected_threats: list[str]
    filtered_input: str | None
    filtered_output: str | None
    response: str | None
    confidence: float
    metadata: dict = field(default_factory=dict)


class DefenseState(TypedDict):
    """防御工作流状态"""

    # 输入
    user_input: str
    system_prompt: str | None

    # 当前状态
    current_phase: DefensePhase
    threat_level: ThreatLevel
    detected_threats: list[str]
    confidence: float

    # 处理结果
    filtered_input: str | None
    raw_response: str | None
    filtered_output: str | None

    # 最终结果
    result: WorkflowDefenseResult | None

    # 上下文
    messages: list[dict]
    audit_log: list[dict]


class DefenseWorkflow:
    """LangGraph 防御工作流"""

    def __init__(
        self,
        llm: BaseLLM,
        enable_input_filter: bool = True,
        enable_output_filter: bool = True,
        enable_llm_judge: bool = True,
        enable_perplexity: bool = False,
        block_threshold: ThreatLevel = ThreatLevel.HIGH,
    ):
        self.llm = llm
        self.enable_input_filter = enable_input_filter
        self.enable_output_filter = enable_output_filter
        self.enable_llm_judge = enable_llm_judge
        self.enable_perplexity = enable_perplexity
        self.block_threshold = block_threshold

        # 初始化防御组件
        self.input_filter = InputFilter() if enable_input_filter else None
        self.output_filter = OutputFilter() if enable_output_filter else None
        self.llm_judge = LLMJudge(llm) if enable_llm_judge else None
        self.perplexity_filter = PerplexityFilter() if enable_perplexity else None

        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建防御工作流图"""
        workflow = StateGraph(DefenseState)

        # 添加节点
        workflow.add_node("input_analysis", self._input_analysis_node)
        workflow.add_node("threat_detection", self._threat_detection_node)
        workflow.add_node("response_generation", self._response_generation_node)
        workflow.add_node("output_filtering", self._output_filtering_node)
        workflow.add_node("audit_logging", self._audit_logging_node)

        # 设置入口点
        workflow.set_entry_point("input_analysis")

        # 添加边
        workflow.add_edge("input_analysis", "threat_detection")

        # 条件边：根据威胁等级决定下一步
        workflow.add_conditional_edges(
            "threat_detection",
            self._should_block,
            {
                "block": "audit_logging",
                "continue": "response_generation",
            },
        )

        workflow.add_edge("response_generation", "output_filtering")
        workflow.add_edge("output_filtering", "audit_logging")
        workflow.add_edge("audit_logging", END)

        return workflow.compile(checkpointer=self.checkpointer)

    async def _input_analysis_node(self, state: DefenseState) -> dict:
        """输入分析节点"""
        user_input = state["user_input"]

        # 基本输入分析
        analysis_result = {
            "length": len(user_input),
            "has_special_chars": any(c in user_input for c in ["<", ">", "{", "}", "[", "]"]),
            "has_encoding": any(kw in user_input.lower() for kw in ["base64", "encode", "decode"]),
        }

        # 使用输入过滤器
        if self.input_filter:
            filter_result = await self.input_filter.detect(user_input)

            if filter_result.is_malicious:
                return {
                    "current_phase": DefensePhase.INPUT_ANALYSIS,
                    "threat_level": ThreatLevel.HIGH,
                    "detected_threats": filter_result.detected_patterns,
                    "confidence": filter_result.confidence,
                    "filtered_input": filter_result.filtered_content,
                }

        return {
            "current_phase": DefensePhase.INPUT_ANALYSIS,
            "confidence": 0.5,
            "metadata": analysis_result,
        }

    async def _threat_detection_node(self, state: DefenseState) -> dict:
        """威胁检测节点"""
        detected_threats = list(state.get("detected_threats", []))
        confidence = state.get("confidence", 0.0)

        # 使用 LLM Judge 进行深度检测
        if self.llm_judge and state["threat_level"] != ThreatLevel.HIGH:
            judge_result = await self.llm_judge.judge(state["user_input"])

            if judge_result.get("is_malicious", False):
                detected_threats.extend(judge_result.get("reasons", []))
                confidence = max(confidence, judge_result.get("confidence", 0.8))

        # 使用困惑度检测
        if self.perplexity_filter:
            perplexity_result = await self.perplexity_filter.detect(state["user_input"])
            if perplexity_result.is_malicious:
                detected_threats.append("high_perplexity_input")
                confidence = max(confidence, 0.7)

        # 确定威胁等级
        threat_level = self._calculate_threat_level(detected_threats, confidence)

        return {
            "current_phase": DefensePhase.THREAT_DETECTION,
            "threat_level": threat_level,
            "detected_threats": detected_threats,
            "confidence": confidence,
        }

    async def _response_generation_node(self, state: DefenseState) -> dict:
        """响应生成节点"""
        # 如果输入被过滤，使用过滤后的版本
        prompt = state.get("filtered_input") or state["user_input"]

        messages = []
        if state.get("system_prompt"):
            messages.append(Message(role="system", content=state["system_prompt"]))
        messages.append(Message(role="user", content=prompt))

        response = await self.llm.generate(messages)

        return {
            "current_phase": DefensePhase.RESPONSE_GENERATION,
            "raw_response": response.content,
        }

    async def _output_filtering_node(self, state: DefenseState) -> dict:
        """输出过滤节点"""
        raw_response = state.get("raw_response", "")

        if self.output_filter and raw_response:
            filter_result = await self.output_filter.detect(raw_response)

            if filter_result.is_malicious:
                return {
                    "current_phase": DefensePhase.OUTPUT_FILTERING,
                    "filtered_output": filter_result.filtered_content,
                    "detected_threats": state["detected_threats"] + ["sensitive_output"],
                }

        return {
            "current_phase": DefensePhase.OUTPUT_FILTERING,
            "filtered_output": raw_response,
        }

    async def _audit_logging_node(self, state: DefenseState) -> dict:
        """审计日志节点"""
        result = WorkflowDefenseResult(
            is_safe=state["threat_level"] in [ThreatLevel.SAFE, ThreatLevel.LOW],
            threat_level=state["threat_level"],
            detected_threats=state.get("detected_threats", []),
            filtered_input=state.get("filtered_input"),
            filtered_output=state.get("filtered_output"),
            response=state.get("filtered_output"),
            confidence=state.get("confidence", 0.0),
            metadata={
                "phase": state["current_phase"].value,
            },
        )

        audit_entry = {
            "input": state["user_input"][:100],  # 截断敏感信息
            "threat_level": state["threat_level"].value,
            "threats": state.get("detected_threats", []),
            "blocked": not result.is_safe,
        }

        return {
            "current_phase": DefensePhase.AUDIT_LOGGING,
            "result": result,
            "audit_log": [audit_entry],
        }

    def _should_block(self, state: DefenseState) -> Literal["block", "continue"]:
        """决定是否阻止请求"""
        threat_order = [
            ThreatLevel.SAFE,
            ThreatLevel.LOW,
            ThreatLevel.MEDIUM,
            ThreatLevel.HIGH,
            ThreatLevel.CRITICAL,
        ]

        threat_idx = threat_order.index(state["threat_level"])
        block_idx = threat_order.index(self.block_threshold)

        if threat_idx >= block_idx:
            return "block"
        return "continue"

    def _calculate_threat_level(
        self,
        detected_threats: list[str],
        confidence: float,
    ) -> ThreatLevel:
        """计算威胁等级"""
        if not detected_threats:
            return ThreatLevel.SAFE

        critical_keywords = ["jailbreak", "dan", "system_override"]
        high_keywords = ["ignore", "role_switch", "injection"]

        for threat in detected_threats:
            if any(kw in threat.lower() for kw in critical_keywords):
                return ThreatLevel.CRITICAL
            if any(kw in threat.lower() for kw in high_keywords):
                return ThreatLevel.HIGH

        if confidence > 0.7:
            return ThreatLevel.MEDIUM
        if confidence > 0.4:
            return ThreatLevel.LOW

        return ThreatLevel.SAFE

    async def process(
        self,
        user_input: str,
        system_prompt: str | None = None,
        thread_id: str = "default",
    ) -> WorkflowDefenseResult:
        """处理用户输入"""
        initial_state: DefenseState = {
            "user_input": user_input,
            "system_prompt": system_prompt,
            "current_phase": DefensePhase.INPUT_ANALYSIS,
            "threat_level": ThreatLevel.SAFE,
            "detected_threats": [],
            "confidence": 0.0,
            "filtered_input": None,
            "raw_response": None,
            "filtered_output": None,
            "result": None,
            "messages": [],
            "audit_log": [],
        }

        config = {"configurable": {"thread_id": thread_id}}

        final_state = await self.graph.ainvoke(initial_state, config)

        return final_state.get("result") or WorkflowDefenseResult(
            is_safe=False,
            threat_level=ThreatLevel.HIGH,
            detected_threats=["processing_error"],
            filtered_input=None,
            filtered_output=None,
            response=None,
            confidence=0.0,
        )
