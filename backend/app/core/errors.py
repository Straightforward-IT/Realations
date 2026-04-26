"""Custom application exceptions mapped to HTTP responses by the FastAPI layer."""

from __future__ import annotations

from fastapi import status


class AppError(Exception):
    """Base class for domain errors that should surface as HTTP responses."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    default_message: str = "Application error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)
        self.message = message or self.default_message


class AuthError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = "Authentication failed"


class PermissionDeniedError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = "Permission denied"


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Resource not found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    default_message = "Resource conflict"


class LicenseError(AppError):
    """Raised when the active subscription does not permit a requested action."""

    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_message = "Subscription does not permit this action"


class IntegrationError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_message = "Upstream integration error"
