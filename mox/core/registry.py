"""Generic registry pattern for attack/defense plugins.

Provides a single thread-safe Registry[T] that replaces the previously
duplicated implementations in attacks/registry.py and defense/registry.py.
"""

from __future__ import annotations

import inspect
import threading
from typing import Dict, Type, Optional, TypeVar, Generic, Callable, Any, Tuple

from mox.infrastructure.logging import get_logger

logger = get_logger("core.registry")

T = TypeVar("T")


class Registry(Generic[T]):
    """Thread-safe generic registry with decorator-based registration.

    Tracks the source module for each registration and supports configurable
    conflict policies when the same key is registered twice.

    Usage::

        from mox.core.registry import Registry

        MY_REGISTRY: Registry[MyBase] = Registry("my_plugin", conflict="warn")

        @MY_REGISTRY.register("foo")
        class Foo(MyBase): ...

        instance = MY_REGISTRY.create("foo", arg1=42)

    Conflict policies:
        "warn"       — log a warning and overwrite (default)
        "error"      — raise ValueError on duplicate key
        "last-wins"  — silently overwrite (no warning)
        "first-wins" — silently ignore the new registration
    """

    VALID_CONFLICT_POLICIES = {"warn", "error", "last-wins", "first-wins"}

    def __init__(self, name: str, conflict: str = "warn"):
        if conflict not in self.VALID_CONFLICT_POLICIES:
            raise ValueError(
                f"Invalid conflict policy '{conflict}'. "
                f"Must be one of {self.VALID_CONFLICT_POLICIES}"
            )
        self._name = name
        self._conflict = conflict
        self._entries: Dict[str, Type[T]] = {}
        self._sources: Dict[str, str] = {}  # key → module that registered it
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, key: str) -> Callable[[Type[T]], Type[T]]:
        """Decorator to register a class under *key*.

        Duplicate handling depends on the ``conflict`` policy set at init.
        """
        def decorator(cls: Type[T]) -> Type[T]:
            source = _caller_module()
            with self._lock:
                if key in self._entries:
                    existing_source = self._sources.get(key, "unknown")
                    if self._conflict == "error":
                        raise ValueError(
                            f"{self._name} '{key}' already registered by "
                            f"{existing_source} (attempted by {source})"
                        )
                    elif self._conflict == "first-wins":
                        logger.debug(
                            "%s '%s' already registered by %s, ignoring %s",
                            self._name, key, existing_source, source,
                        )
                        return cls
                    elif self._conflict == "warn":
                        logger.warning(
                            "%s '%s' already registered by %s (was %s), "
                            "overwriting with %s from %s",
                            self._name, key, existing_source,
                            self._entries[key].__name__, cls.__name__, source,
                        )
                    # "last-wins" — silently overwrite
                self._entries[key] = cls
                self._sources[key] = source
            return cls
        return decorator

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[Type[T]]:
        """Return the registered class or ``None``."""
        with self._lock:
            return self._entries.get(key)

    def get_source(self, key: str) -> Optional[str]:
        """Return the module that registered *key*, or ``None``."""
        with self._lock:
            return self._sources.get(key)

    def create(self, key: str, **kwargs: Any) -> T:
        """Instantiate the class registered under *key*.

        Raises ``ValueError`` if *key* is not found.
        """
        cls = self.get(key)
        if cls is None:
            raise ValueError(
                f"{self._name} '{key}' not in registry. "
                f"Available: {self.registered_names}"
            )
        return cls(**kwargs)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def registered_names(self) -> list[str]:
        """Return a snapshot of all registered keys."""
        with self._lock:
            return list(self._entries.keys())

    def entries_with_sources(self) -> Dict[str, Tuple[Type[T], str]]:
        """Return {key: (class, source_module)} for debugging."""
        with self._lock:
            return {
                k: (self._entries[k], self._sources.get(k, "unknown"))
                for k in self._entries
            }

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._entries

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def __repr__(self) -> str:
        return f"Registry({self._name!r}, entries={len(self)}, conflict={self._conflict!r})"


def _caller_module() -> str:
    """Walk the call stack to find the module that invoked register()."""
    frame = inspect.currentframe()
    try:
        # Skip: _caller_module → decorator → register → actual caller
        for _ in range(4):
            if frame is None:
                break
            frame = frame.f_back
        if frame is not None:
            return frame.f_globals.get("__name__", "<unknown>")
    finally:
        del frame
    return "<unknown>"
