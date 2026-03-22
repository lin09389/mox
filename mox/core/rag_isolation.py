"""RAG 层隔离 - 知识库访问控制 (RBAC)

提供:
1. 知识库域分离
2. 基于角色的访问控制 (RBAC)
3. 查询验证和过滤
4. 审计日志
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import time


class AccessLevel(Enum):
    """访问级别"""

    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3


@dataclass
class KnowledgeBase:
    """知识库定义"""

    kb_id: str
    name: str
    description: str
    domain: str
    sensitivity_level: int = 1
    allowed_roles: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """检索结果"""

    content: str
    source: str
    kb_id: str
    relevance_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessLog:
    """访问日志"""

    log_id: str
    user_id: str
    kb_id: str
    action: str
    timestamp: float
    granted: bool
    reason: str = ""


class RBACEngine:
    """RBAC 引擎"""

    def __init__(self):
        self.roles: Dict[str, Set[str]] = {}
        self.role_hierarchies: Dict[str, List[str]] = {}

    def add_role(self, role: str, permissions: Set[str]):
        """添加角色"""
        self.roles[role] = permissions

    def add_hierarchy(self, parent_role: str, child_roles: List[str]):
        """添加角色层级"""
        self.role_hierarchies[parent_role] = child_roles

    def get_permissions(self, role: str) -> Set[str]:
        """获取角色权限"""
        permissions = set()

        if role in self.roles:
            permissions.update(self.roles[role])

        for parent, children in self.role_hierarchies.items():
            if role in children:
                if parent in self.roles:
                    permissions.update(self.roles[parent])

        return permissions


class RAGIsolation:
    """RAG 隔离层

    使用示例:
        rag = RAGIsolation()

        # 注册知识库
        rag.register_knowledge_base(
            kb_id="medical_kb",
            name="医学知识库",
            domain="medical",
            allowed_roles=["doctor", "medical_staff"]
        )

        # 检索 (带权限检查)
        results = await rag.retrieve("symptoms", user_role="patient", user_id="user123")
    """

    def __init__(self):
        self.knowledge_bases: Dict[str, KnowledgeBase] = {}
        self.rbac = RBACEngine()
        self.access_logs: List[AccessLog] = []
        self.vector_stores: Dict[str, Any] = {}
        self._setup_default_roles()

    def _setup_default_roles(self):
        """设置默认角色"""
        self.rbac.add_role("admin", {"read", "write", "delete", "manage"})
        self.rbac.add_role("doctor", {"read", "write"})
        self.rbac.add_role("nurse", {"read"})
        self.rbac.add_role("patient", {"read"})
        self.rbac.add_role("staff", {"read"})
        self.rbac.add_role("guest", set())

        self.rbac.add_hierarchy("admin", ["doctor", "nurse", "staff"])

    def register_knowledge_base(
        self,
        kb_id: str,
        name: str,
        domain: str,
        description: str = "",
        allowed_roles: Optional[Set[str]] = None,
        sensitivity_level: int = 1,
    ):
        """注册知识库"""
        self.knowledge_bases[kb_id] = KnowledgeBase(
            kb_id=kb_id,
            name=name,
            description=description,
            domain=domain,
            sensitivity_level=sensitivity_level,
            allowed_roles=allowed_roles or set(),
        )

    def register_vector_store(
        self,
        kb_id: str,
        vector_store: Any,
    ):
        """注册向量存储"""
        self.vector_stores[kb_id] = vector_store

    async def retrieve(
        self,
        query: str,
        user_role: str,
        user_id: str,
        kb_ids: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> List[RetrievalResult]:
        """检索知识库"""

        if kb_ids is None:
            kb_ids = list(self.knowledge_bases.keys())

        authorized_kbs = []
        for kb_id in kb_ids:
            if kb_id not in self.knowledge_bases:
                self._log_access(user_id, kb_id, "retrieve", False, "KB not found")
                continue

            kb = self.knowledge_bases[kb_id]

            if self._check_access(user_role, kb):
                authorized_kbs.append(kb_id)
                self._log_access(user_id, kb_id, "retrieve", True)
            else:
                self._log_access(user_id, kb_id, "retrieve", False, "Access denied")

        results = []
        for kb_id in authorized_kbs:
            kb_results = await self._search_kb(kb_id, query, top_k)
            results.extend(kb_results)

        results.sort(key=lambda x: x.relevance_score, reverse=True)

        return results[:top_k]

    def _check_access(self, role: str, kb: KnowledgeBase) -> bool:
        """检查访问权限"""

        if not kb.allowed_roles:
            return True

        user_perms = self.rbac.get_permissions(role)
        if "admin" in user_perms or "manage" in user_perms:
            return True

        return role in kb.allowed_roles

    async def _search_kb(
        self,
        kb_id: str,
        query: str,
        top_k: int,
    ) -> List[RetrievalResult]:
        """搜索知识库"""

        if kb_id not in self.vector_stores:
            return []

        try:
            store = self.vector_stores[kb_id]

            if hasattr(store, "similarity_search"):
                docs = store.similarity_search(query, k=top_k)
                return [
                    RetrievalResult(
                        content=doc.page_content,
                        source=doc.metadata.get("source", "unknown"),
                        kb_id=kb_id,
                        relevance_score=0.9,
                        metadata=doc.metadata,
                    )
                    for doc in docs
                ]

        except Exception:
            pass

        return []

    def _log_access(
        self,
        user_id: str,
        kb_id: str,
        action: str,
        granted: bool,
        reason: str = "",
    ):
        """记录访问日志"""
        log = AccessLog(
            log_id=hashlib.md5(f"{user_id}{kb_id}{time.time()}".encode()).hexdigest()[:12],
            user_id=user_id,
            kb_id=kb_id,
            action=action,
            timestamp=time.time(),
            granted=granted,
            reason=reason,
        )
        self.access_logs.append(log)

    def get_access_logs(
        self,
        user_id: Optional[str] = None,
        kb_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取访问日志"""
        logs = self.access_logs

        if user_id:
            logs = [log for log in logs if log.user_id == user_id]
        if kb_id:
            logs = [log for log in logs if log.kb_id == kb_id]

        logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)

        return [
            {
                "log_id": log.log_id,
                "user_id": log.user_id,
                "kb_id": log.kb_id,
                "action": log.action,
                "timestamp": log.timestamp,
                "granted": log.granted,
                "reason": log.reason,
            }
            for log in logs[:limit]
        ]


class RAGQueryValidator:
    """RAG 查询验证器"""

    def __init__(self, rag_isolation: RAGIsolation):
        self.rag = rag_isolation

    def validate_query(self, query: str, user_role: str) -> tuple[bool, str]:
        """验证查询"""

        dangerous_patterns = [
            "ignore previous",
            "system prompt",
            "override",
            "admin mode",
        ]

        query_lower = query.lower()
        for pattern in dangerous_patterns:
            if pattern in query_lower:
                return False, f"Dangerous pattern detected: {pattern}"

        perms = self.rag.rbac.get_permissions(user_role)
        if "admin" not in perms and "manage" not in perms:
            if "delete" in query_lower or "drop" in query_lower:
                return False, "Write operations not allowed"

        return True, "Query validated"

    def sanitize_query(self, query: str) -> str:
        """清理查询"""
        sanitized = query

        injection_patterns = [
            r"\{__",
            r"__\}",
            r"\[SYSTEM\]",
            r"\[ADMIN\]",
        ]

        import re

        for pattern in injection_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        return sanitized


class DomainIsolatedRAG:
    """域隔离的 RAG"""

    def __init__(self):
        self.domains: Dict[str, RAGIsolation] = {}

    def create_domain(
        self,
        domain: str,
        knowledge_bases: List[Dict[str, Any]],
    ) -> RAGIsolation:
        """创建域"""
        rag = RAGIsolation()

        for kb in knowledge_bases:
            rag.register_knowledge_base(
                kb_id=kb["id"],
                name=kb["name"],
                domain=domain,
                allowed_roles=set(kb.get("allowed_roles", [])),
                sensitivity_level=kb.get("sensitivity_level", 1),
            )

        self.domains[domain] = rag
        return rag

    def get_domain(self, domain: str) -> Optional[RAGIsolation]:
        """获取域"""
        return self.domains.get(domain)


__all__ = [
    "RAGIsolation",
    "RAGQueryValidator",
    "DomainIsolatedRAG",
    "KnowledgeBase",
    "RetrievalResult",
    "AccessLog",
    "AccessLevel",
    "RBACEngine",
]
