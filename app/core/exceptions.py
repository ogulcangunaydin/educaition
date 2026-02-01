from typing import Any, Optional

class AppException(Exception):
    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> dict:
        result = {"error": self.message, "status_code": self.status_code}
        if self.details:
            result["details"] = self.details
        return result

class NotFoundError(AppException):
    """Resource not found exception (404)."""
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
    ):
        details = None
        if resource_type or resource_id:
            details = {}
            if resource_type:
                details["resource_type"] = resource_type
            if resource_id:
                details["resource_id"] = resource_id
        super().__init__(message=message, status_code=404, details=details)

class ValidationError(AppException):
    """Validation error exception (422)."""
    def __init__(
        self,
        message: str = "Validation error",
        field: Optional[str] = None,
        errors: Optional[list] = None,
    ):
        details = {}
        if field:
            details["field"] = field
        if errors:
            details["errors"] = errors
        super().__init__(
            message=message, status_code=422, details=details if details else None
        )

class AuthenticationError(AppException):
    """Authentication error exception (401)."""
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, status_code=401, details=details)

class AuthorizationError(AppException):
    """Authorization error exception (403)."""
    def __init__(
        self,
        message: str = "Access denied",
        required_permission: Optional[str] = None,
    ):
        details = None
        if required_permission:
            details = {"required_permission": required_permission}
        super().__init__(message=message, status_code=403, details=details)

class ConflictError(AppException):
    """Conflict error exception (409) - e.g., duplicate resource."""
    def __init__(
        self,
        message: str = "Resource already exists",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, status_code=409, details=details)

class RateLimitError(AppException):
    """Rate limit exceeded exception (429)."""
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        details = None
        if retry_after:
            details = {"retry_after_seconds": retry_after}
        super().__init__(message=message, status_code=429, details=details)

class ServiceError(AppException):
    """External service error exception (502)."""
    def __init__(
        self,
        message: str = "External service error",
        service_name: Optional[str] = None,
    ):
        details = None
        if service_name:
            details = {"service": service_name}
        super().__init__(message=message, status_code=502, details=details)
