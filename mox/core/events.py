"""Simple event bus for decoupling persistence from core logic.

BaseAttack and BaseDefense emit events; infrastructure layers (API,
orchestrator, etc.) subscribe and handle persistence, logging, etc.

Usage::

    from mox.core.events import event_bus

    # Subscribe
    async def on_attack(outcome, attack, **kw):
        await db.save(outcome)
    event_bus.on("attack_completed", on_attack)

    # Emit (from BaseAttack)
    await event_bus.emit("attack_completed", outcome=outcome, attack=self)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, List, Union

logger = logging.getLogger(__name__)

# Handler can be sync or async
Handler = Callable[..., Union[None, Coroutine[Any, Any, None]]]


class EventBus:
    """Minimal async-safe event bus."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Handler]] = {}

    def on(self, event: str, handler: Handler) -> None:
        """Register *handler* for *event*."""
        self._handlers.setdefault(event, []).append(handler)

    def off(self, event: str, handler: Handler) -> None:
        """Remove *handler* from *event* (no-op if not found)."""
        handlers = self._handlers.get(event)
        if handlers:
            try:
                handlers.remove(handler)
            except ValueError:
                pass

    async def emit(self, event: str, **data: Any) -> None:
        """Call all handlers registered for *event*.

        Handlers are invoked in registration order.  A failing handler
        is logged and does **not** prevent subsequent handlers from running.
        """
        for handler in self._handlers.get(event, []):
            try:
                result = handler(**data)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.warning("Event handler %r for '%s' failed", handler, event, exc_info=True)


# Module-level singleton used throughout the project.
event_bus = EventBus()
