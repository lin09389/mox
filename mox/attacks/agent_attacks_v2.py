"""Compatibility shim — re-exports the agent attack classes that previously
lived in a separate ``agent_attacks_v2.py`` module.

The real implementations have been consolidated into
:mod:`mox.attacks.agent_attacks` (see the docstring there for details).
This module exists so that legacy imports of the form
``from mox.attacks.agent_attacks_v2 import ToolChainingAttack`` keep working.
"""

from mox.attacks.agent_attacks import (
    AgentAttackType,
    AgentAttackConfig,
    ToolAbuseAttack,
    MemoryInjectionAttack,
    RoleHijackingAttack,
    ToolChainingAttack,
    IndirectToolInjectionAttack as IndirectToolInjection,
    PrivilegeEscalationAttack,
    DataExfiltrationAttack,
    MultiAgentAttack,
    CompositeAgentAttack,
)

# `ToolConfusionAttack` was never implemented (it was referenced only by the
# v2 endpoint).  Map it to a real, related class so the endpoint still works
# even when callers ask for it.
ToolConfusionAttack = ToolAbuseAttack

# A minimal DEFAULT_TOOLS list — the original v2 module exposed this constant
# for the ``run_agent_attack`` endpoint.  We keep the name and shape stable.
DEFAULT_TOOLS: list = [
    "read_file",
    "write_file",
    "http_request",
    "execute_shell",
    "search_web",
]

__all__ = [
    "AgentAttackType",
    "AgentAttackConfig",
    "ToolAbuseAttack",
    "MemoryInjectionAttack",
    "RoleHijackingAttack",
    "ToolChainingAttack",
    "IndirectToolInjection",
    "PrivilegeEscalationAttack",
    "ToolConfusionAttack",
    "DataExfiltrationAttack",
    "MultiAgentAttack",
    "CompositeAgentAttack",
    "DEFAULT_TOOLS",
]
