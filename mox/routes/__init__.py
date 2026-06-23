"""路由模块"""

from .attack import router as attack_router
from .defense import router as defense_router
from .auth import router as auth_router
from .benchmark import router as benchmark_router
from .monitoring import router as monitoring_router
from .gateway import router as gateway_router
from .tasks import router as tasks_router
from .audit import router as audit_router
from .platform import router as platform_router
from .datasets import router as datasets_router
from .reports import router as reports_router
from .user_templates import router as user_templates_router
from .websocket import router as websocket_router

__all__ = [
    "attack_router",
    "defense_router",
    "auth_router",
    "benchmark_router",
    "monitoring_router",
    "gateway_router",
    "tasks_router",
    "audit_router",
    "platform_router",
    "datasets_router",
    "reports_router",
    "user_templates_router",
    "websocket_router",
]
