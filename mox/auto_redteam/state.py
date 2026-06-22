"""自动红蓝对抗 - 状态与数据结构"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AgentState(str, Enum):
    """智能体运行状态"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    FINISHED = "finished"
    ERROR = "error"


class VulnerabilityType(str, Enum):
    """漏洞类型分类"""
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    OTHER = "other"


class DiscoveredVulnerability(BaseModel):
    """发现的漏洞记录"""
    id: str
    vuln_type: VulnerabilityType
    attack_name: str
    prompt_used: str
    model_response: str
    severity: float = Field(ge=0.0, le=1.0)
    discovered_at: datetime = Field(default_factory=datetime.now)


class StepLog(BaseModel):
    """推理步骤日志"""
    step_num: int
    timestamp: datetime = Field(default_factory=datetime.now)
    state: AgentState
    thought: Optional[str] = None
    action_name: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None


class RedTeamTask(BaseModel):
    """红队任务整体状态"""
    task_id: str
    target_model: str
    status: str = "running" # running, completed, failed
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    max_steps: int = 20
    current_step: int = 0
    logs: List[StepLog] = []
    vulnerabilities: List[DiscoveredVulnerability] = []
    error_message: Optional[str] = None
    report_id: Optional[int] = None
