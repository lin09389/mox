"""自定义异常模块"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """错误码枚举"""

    # 通用错误
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    NOT_FOUND = "NOT_FOUND"

    # 认证错误
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INSUFFICIENT_SCOPE = "INSUFFICIENT_SCOPE"

    # 攻击相关
    ATTACK_FAILED = "ATTACK_FAILED"
    INVALID_ATTACK_TYPE = "INVALID_ATTACK_TYPE"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"

    # 防御相关
    DEFENSE_FAILED = "DEFENSE_FAILED"
    SCAN_FAILED = "SCAN_FAILED"

    # 网关相关
    GATEWAY_ERROR = "GATEWAY_ERROR"
    ENDPOINT_NOT_FOUND = "ENDPOINT_NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # 任务相关
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_FAILED = "TASK_FAILED"


class MoxException(Exception):
    """Mox 基础异常"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.code.value,
            "message": self.message,
            "details": self.details,
        }


class AuthenticationError(MoxException):
    """认证错误"""

    def __init__(
        self,
        message: str = "Authentication failed",
        code: ErrorCode = ErrorCode.UNAUTHORIZED,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=401,
        )


class AuthorizationError(MoxException):
    """授权错误"""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_scope: Optional[str] = None,
    ):
        details = {"required_scope": required_scope} if required_scope else {}
        super().__init__(
            code=ErrorCode.INSUFFICIENT_SCOPE,
            message=message,
            details=details,
            status_code=403,
        )


class NotFoundError(MoxException):
    """资源未找到错误"""

    def __init__(
        self,
        resource: str,
        identifier: Optional[str] = None,
    ):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        super().__init__(
            code=ErrorCode.NOT_FOUND,
            message=message,
            details={"resource": resource, "identifier": identifier},
            status_code=404,
        )


class ValidationError(MoxException):
    """验证错误"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
    ):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(
            code=ErrorCode.INVALID_REQUEST,
            message=message,
            details=details,
            status_code=422,
        )


class AttackError(MoxException):
    """攻击执行错误"""

    def __init__(
        self,
        message: str,
        attack_type: Optional[str] = None,
        code: ErrorCode = ErrorCode.ATTACK_FAILED,
    ):
        details = {"attack_type": attack_type} if attack_type else {}
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=500,
        )


class DefenseError(MoxException):
    """防御执行错误"""

    def __init__(
        self,
        message: str,
        defense_type: Optional[str] = None,
    ):
        details = {"defense_type": defense_type} if defense_type else {}
        super().__init__(
            code=ErrorCode.DEFENSE_FAILED,
            message=message,
            details=details,
            status_code=500,
        )


class GatewayError(MoxException):
    """网关错误"""

    def __init__(
        self,
        message: str,
        endpoint: Optional[str] = None,
        code: ErrorCode = ErrorCode.GATEWAY_ERROR,
    ):
        details = {"endpoint": endpoint} if endpoint else {}
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=502,
        )


class RateLimitError(MoxException):
    """速率限制错误"""

    def __init__(
        self,
        retry_after: int = 60,
        limit: Optional[int] = None,
    ):
        details = {"retry_after": retry_after}
        if limit:
            details["limit"] = limit
        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="Rate limit exceeded",
            details=details,
            status_code=429,
        )
