"""Exception handlers producing a single, consistent error shape."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import AppError
from app.core.logging import get_logger

logger = get_logger(__name__)

_PROBLEM_MEDIA_TYPE = "application/problem+json"


def _trace_id() -> str | None:
    ctx: dict[str, Any] = structlog.contextvars.get_contextvars()
    value = ctx.get("trace_id")
    return str(value) if value else None


async def app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    if exc.status_code >= 500:
        logger.error("app_error", code=exc.code, detail=exc.detail, **exc.context)
    else:
        logger.info("app_error", code=exc.code, detail=exc.detail, **exc.context)
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_problem(_trace_id()),
        media_type=_PROBLEM_MEDIA_TYPE,
    )


async def validation_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "https://amip.local/errors/validation-error",
            "title": "Invalid request",
            "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "code": "VALIDATION_ERROR",
            "detail": "Request payload failed validation",
            "errors": exc.errors(),
            "trace_id": _trace_id(),
        },
        media_type=_PROBLEM_MEDIA_TYPE,
    )


async def http_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://amip.local/errors/http-{exc.status_code}",
            "title": str(exc.detail),
            "status": exc.status_code,
            "code": f"HTTP_{exc.status_code}",
            "detail": str(exc.detail),
            "trace_id": _trace_id(),
        },
        media_type=_PROBLEM_MEDIA_TYPE,
    )


async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://amip.local/errors/internal-error",
            "title": "Internal error",
            "status": 500,
            "code": "INTERNAL_ERROR",
            # Never leak internals to the client.
            "detail": "An unexpected error occurred. See server logs.",
            "trace_id": _trace_id(),
        },
        media_type=_PROBLEM_MEDIA_TYPE,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
