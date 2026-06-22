"""任务状态存储 - Redis 优先，内存回退"""

import json
from typing import Any, Dict, List, Optional

from mox.core.config import settings
from mox.core.logging import get_logger

logger = get_logger("task_store")

_PREFIX = "mox:task:"


class TaskStore:
    """跨进程任务元数据存储"""

    def __init__(self):
        self._memory: Dict[str, Dict[str, Any]] = {}
        self._redis = None
        if settings.REDIS_ENABLED:
            try:
                import redis

                self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
                self._redis.ping()
                logger.info("TaskStore using Redis backend")
            except Exception as exc:
                logger.warning(f"Redis unavailable, using memory TaskStore: {exc}")
                self._redis = None

    def _key(self, task_id: str) -> str:
        return f"{_PREFIX}{task_id}"

    def set(self, task_id: str, data: Dict[str, Any], ttl: int = 86400) -> None:
        payload = json.dumps(data, ensure_ascii=False, default=str)
        if self._redis:
            self._redis.setex(self._key(task_id), ttl, payload)
        self._memory[task_id] = data

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        if self._redis:
            raw = self._redis.get(self._key(task_id))
            if raw:
                return json.loads(raw)
        return self._memory.get(task_id)

    def update(self, task_id: str, **fields: Any) -> None:
        current = self.get(task_id) or {"id": task_id}
        current.update(fields)
        self.set(task_id, current)

    def list_by_prefix(self, prefix: str = "") -> List[Dict[str, Any]]:
        items = []
        if self._redis:
            for key in self._redis.scan_iter(f"{_PREFIX}*"):
                raw = self._redis.get(key)
                if raw:
                    item = json.loads(raw)
                    if not prefix or item.get("source", "").startswith(prefix):
                        items.append(item)
        else:
            for task_id, item in self._memory.items():
                if not prefix or item.get("source", "").startswith(prefix):
                    items.append(item)
        return items

    def delete(self, task_id: str) -> None:
        if self._redis:
            self._redis.delete(self._key(task_id))
        self._memory.pop(task_id, None)


_store: Optional[TaskStore] = None


def get_task_store() -> TaskStore:
    global _store
    if _store is None:
        _store = TaskStore()
    return _store