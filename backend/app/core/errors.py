"""Application exception hierarchy.

Every exception carries a stable ``code`` so the UI can react programmatically
and so requirement §29 (explicit error instead of fabricated data) is honoured.
"""

from __future__ import annotations

from typing import Any

_ERROR_BASE_URI = "https://amip.local/errors/"


class AppError(Exception):
    """Base class for all expected application errors."""

    code: str = "INTERNAL_ERROR"
    status_code: int = 500
    title: str = "Internal error"

    def __init__(self, detail: str | None = None, **context: Any) -> None:
        self.detail = detail or self.title
        self.context = context
        super().__init__(self.detail)

    @property
    def type_uri(self) -> str:
        return _ERROR_BASE_URI + self.code.lower().replace("_", "-")

    def to_problem(self, trace_id: str | None = None) -> dict[str, Any]:
        """RFC 7807-style payload (see docs/04-api-contract.md §4.1)."""
        problem: dict[str, Any] = {
            "type": self.type_uri,
            "title": self.title,
            "status": self.status_code,
            "code": self.code,
            "detail": self.detail,
        }
        problem.update({k: v for k, v in self.context.items() if v is not None})
        if trace_id:
            problem["trace_id"] = trace_id
        return problem


# --- configuration -------------------------------------------------------
class ConfigurationError(AppError):
    code = "CONFIGURATION_ERROR"
    status_code = 500
    title = "Invalid configuration"


# --- client errors -------------------------------------------------------
class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404
    title = "Resource not found"


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 422
    title = "Invalid request"


class UnauthorizedError(AppError):
    code = "UNAUTHORIZED"
    status_code = 401
    title = "Missing or invalid local token"


# --- data / provider errors ---------------------------------------------
class DataSourceError(AppError):
    code = "DATA_SOURCE_ERROR"
    status_code = 502
    title = "Data source error"


class DataSourceUnavailableError(DataSourceError):
    code = "DATA_SOURCE_DOWN"
    status_code = 503
    title = "Market data source unavailable"


class RateLimitedError(DataSourceError):
    code = "RATE_LIMITED"
    status_code = 429
    title = "Upstream rate limit reached"


class CircuitOpenError(DataSourceError):
    code = "CIRCUIT_OPEN"
    status_code = 503
    title = "Circuit breaker is open for this source"


class DataQualityError(AppError):
    code = "DATA_QUALITY_ERROR"
    status_code = 422
    title = "Record failed validation"


class DataUnavailableError(AppError):
    """Raised instead of returning fabricated values (requirement §29)."""

    code = "DATA_UNAVAILABLE"
    status_code = 503
    title = "Required data is not available"


# --- AI ------------------------------------------------------------------
class AIProviderError(AppError):
    code = "AI_PROVIDER_ERROR"
    status_code = 503
    title = "AI provider error"


class AIOutputInvalidError(AIProviderError):
    code = "AI_OUTPUT_INVALID"
    status_code = 502
    title = "AI returned an output that failed validation"
