"""Standard exception types for dataenginex integrations.

These are plain Python exceptions.  Applications that expose an HTTP
layer (e.g. a FastAPI server) can catch them and map to HTTP status codes.
"""

from __future__ import annotations

__all__ = [
    "DexAPIError",
    "BadRequestError",
    "NotFoundError",
    "ServiceUnavailableError",
]


class DexAPIError(Exception):
    """Base error for dataenginex API operations."""

    def __init__(self, message: str, code: str = "api_error") -> None:
        super().__init__(message)
        self.code = code


class BadRequestError(DexAPIError):
    """Invalid input or malformed request."""

    def __init__(self, message: str = "Bad request") -> None:
        super().__init__(message, code="bad_request")


class NotFoundError(DexAPIError):
    """Requested resource does not exist."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, code="not_found")


class ServiceUnavailableError(DexAPIError):
    """A required dependency is unavailable."""

    def __init__(self, message: str = "Service unavailable") -> None:
        super().__init__(message, code="service_unavailable")
