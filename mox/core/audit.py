"""审计日志模块"""

import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from mox.core.logging import get_logger

logger = get_logger("audit")


class SensitiveLevel(Enum):
    """敏感等级"""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"


@dataclass
class AuditContext:
    """审计上下文"""

    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None


class SensitiveDataMasker:
    """敏感数据脱敏器"""

    PATTERNS = {
        "api_key": (
            re.compile(r'(api[_-]?key["\']?\s*[:=]\s*["\']?)([a-zA-Z0-9\-_]{20,})', re.I),
            r"\1****",
        ),
        "password": (
            re.compile(r'(password["\']?\s*[:=]\s*["\']?)([^\s"\'}]+)', re.I),
            r"\1****",
        ),
        "secret": (
            re.compile(r'(secret["\']?\s*[:=]\s*["\']?)([^\s"\'}]+)', re.I),
            r"\1****",
        ),
        "token": (
            re.compile(r'(token["\']?\s*[:=]\s*["\']?)([a-zA-Z0-9\-_]{20,})', re.I),
            r"\1****",
        ),
        "bearer_token": (
            re.compile(r"(Bearer\s+)([a-zA-Z0-9\-_.~+/]{20,}=*)", re.I),
            r"\1****",
        ),
        "email": (
            re.compile(r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"),
            r"***@\2",
        ),
        "phone": (
            re.compile(r"(1[3-9]\d{9})"),
            r"***********",
        ),
        "ip_address": (
            re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b"),
            r"***.***.***.***",
        ),
        "id_card": (
            re.compile(r"\b(\d{6}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx])\b"),
            r"******************",
        ),
        "credit_card": (
            re.compile(r"\b(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})\b"),
            r"**** **** **** ****",
        ),
    }

    @classmethod
    def mask(cls, text: str, patterns: Optional[List[str]] = None) -> str:
        """脱敏文本"""
        if not text:
            return text

        result = text

        if patterns is None:
            patterns = list(cls.PATTERNS.keys())

        for pattern_name in patterns:
            if pattern_name in cls.PATTERNS:
                pattern, replacement = cls.PATTERNS[pattern_name]
                result = pattern.sub(replacement, result)

        return result

    @classmethod
    def mask_dict(
        cls, data: Dict[str, Any], sensitive_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """脱敏字典数据"""
        if sensitive_keys is None:
            sensitive_keys = [
                "api_key",
                "apiKey",
                "api-key",
                "secret",
                "Secret",
                "SECRET",
                "password",
                "Password",
                "PASSWORD",
                "token",
                "Token",
                "TOKEN",
                "access_token",
                "accessToken",
                "refresh_token",
                "refreshToken",
                "credential",
                "Credential",
            ]

        result = {}

        for key, value in data.items():
            is_sensitive = any(sk.lower() in key.lower() for sk in sensitive_keys)

            if is_sensitive:
                if isinstance(value, str):
                    result[key] = "****"
                elif isinstance(value, dict):
                    result[key] = cls.mask_dict(value, sensitive_keys)
                else:
                    result[key] = value
            else:
                if isinstance(value, str):
                    result[key] = cls.mask(value)
                elif isinstance(value, dict):
                    result[key] = cls.mask_dict(value, sensitive_keys)
                elif isinstance(value, list):
                    result[key] = [cls.mask(v) if isinstance(v, str) else v for v in value]
                else:
                    result[key] = value

        return result


class AuditLogger:
    """审计日志记录器"""

    def __init__(self):
        self._db = None

    def _get_db(self):
        from mox.core.database import get_extended_database

        if self._db is None:
            self._db = get_extended_database()
        return self._db

    async def log(
        self,
        action: str,
        resource: str = "",
        context: Optional[AuditContext] = None,
        request_body: Optional[Dict[str, Any]] = None,
        response_status: Optional[int] = None,
        duration_ms: Optional[int] = None,
        is_sensitive: bool = False,
    ) -> None:
        """记录审计日志"""
        try:
            db = self._get_db()

            log_data = {
                "action": action,
                "resource": resource,
                "method": context.method if context else None,
                "endpoint": context.endpoint if context else None,
                "ip_address": context.ip_address if context else None,
                "user_agent": context.user_agent if context else None,
                "user_id": context.user_id if context else None,
                "username": context.username if context else None,
                "response_status": response_status,
                "duration_ms": duration_ms,
                "is_sensitive": is_sensitive,
            }

            if request_body:
                masked_body = SensitiveDataMasker.mask_dict(request_body)
                log_data["request_body"] = json.dumps(masked_body, ensure_ascii=False)

            await db.save_audit_log(log_data)

        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")

    async def get_logs(
        self,
        limit: int = 100,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """获取审计日志"""
        db = self._get_db()
        logs = await db.get_audit_logs(
            limit=limit,
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
        )

        return [
            {
                "id": log.id,
                "action": log.action,
                "resource": log.resource,
                "method": log.method,
                "endpoint": log.endpoint,
                "username": log.username,
                "ip_address": log.ip_address,
                "response_status": log.response_status,
                "duration_ms": log.duration_ms,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]

    def create_context(
        self,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
    ) -> AuditContext:
        """创建审计上下文"""
        return AuditContext(
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
        )


_default_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """获取审计日志记录器"""
    global _default_audit_logger
    if _default_audit_logger is None:
        _default_audit_logger = AuditLogger()
    return _default_audit_logger
