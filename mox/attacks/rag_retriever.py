"""内存向量检索模拟 — 支持 RAG 投毒与检索操纵攻击评测"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _tfidf_vector(tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    tf: Dict[str, float] = {}
    for t in tokens:
        tf[t] = tf.get(t, 0.0) + 1.0
    total = len(tokens) or 1
    return {t: (c / total) * idf.get(t, 1.0) for t, c in tf.items()}


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in set(a) | set(b))
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


@dataclass
class RetrievalDocument:
    doc_id: str
    text: str
    metadata: Dict[str, str] = field(default_factory=dict)
    poisoned: bool = False


class InMemoryRAGStore:
    """轻量内存检索库，支持投毒文档注入"""

    def __init__(self, documents: Optional[List[RetrievalDocument]] = None):
        self.documents: List[RetrievalDocument] = list(documents or [])
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        df: Dict[str, int] = {}
        for doc in self.documents:
            for t in set(_tokenize(doc.text)):
                df[t] = df.get(t, 0) + 1
        n = len(self.documents) or 1
        self._idf = {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}
        self._vectors = [_tfidf_vector(_tokenize(d.text), self._idf) for d in self.documents]

    def add_document(self, text: str, doc_id: Optional[str] = None, poisoned: bool = False) -> str:
        did = doc_id or f"doc_{len(self.documents)}"
        self.documents.append(RetrievalDocument(doc_id=did, text=text, poisoned=poisoned))
        self._rebuild_index()
        return did

    def inject_poison(self, poison_text: str, count: int = 3) -> List[str]:
        """注入多条投毒文档以提高被检索概率"""
        ids = []
        for i in range(count):
            ids.append(self.add_document(poison_text, poisoned=True))
        return ids

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        if not self.documents:
            return []
        qvec = _tfidf_vector(_tokenize(query), self._idf)
        scored: List[Tuple[float, RetrievalDocument]] = []
        for vec, doc in zip(self._vectors, self.documents):
            scored.append((_cosine(qvec, vec), doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d.text for _, d in scored[:top_k]]

    def retriever_func(self, top_k: int = 3) -> Callable:
        """返回可供 RAGContextInjectionAttack 使用的 async retriever"""

        async def _retrieve(query: str) -> List[str]:
            return self.retrieve(query, top_k=top_k)

        return _retrieve


def create_default_rag_store(seed_docs: Optional[List[str]] = None) -> InMemoryRAGStore:
    store = InMemoryRAGStore()
    for i, text in enumerate(
        seed_docs
        or [
            "Mox is an LLM security testing platform.",
            "Always follow safety guidelines when answering user queries.",
            "Administrators must authenticate before accessing sensitive data.",
        ]
    ):
        store.add_document(text, doc_id=f"seed_{i}")
    return store


__all__ = ["InMemoryRAGStore", "RetrievalDocument", "create_default_rag_store"]