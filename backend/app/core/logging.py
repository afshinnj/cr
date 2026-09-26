"""Structured logging with automatic secret masking (requirement §25)."""

from __future__ import annotations

import logging
import re
import sys
from typing import Any

import structlog

from app.core.config import LogFormat, Settings

#: Keys whose values must never reach a log sink.
SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "api_secret",
        "authorization",
        "cookie",
        "set-cookie",
        "local_api_token",
        "postgres_password",
        "redis_password",
        "binance_api_key",
        "binance_api_secret",
        "coingecko_api_key",
    }
)

_REDACTED = "***REDACTED***"

# Catches `key=value` / `key: value` / `"key":"value"` inside free-form strings.
_INLINE_SECRET_RE = re.compile(
    r"(?i)\b(" + "|".join(sorted(SENSITIVE_KEYS)) + r")\b(\s*[=:]\s*)(\"?)([^\s\",;&]+)"
)


def _mask_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: (_REDACTED if k.lower() in SENSITIVE_KEYS else _mask_value(v))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return type(value)(_mask_value(v) for v in value)
    if isinstance(value, str):
        return _INLINE_SECRET_RE.sub(
            lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}{_REDACTED}", value
        )
    return value


def mask_secrets(
    _logger: Any, _method: str, event_dict: structlog.types.EventDict
) -> structlog.types.EventDict:
    """structlog processor that redacts sensitive keys and inline secrets."""
    return {
        key: (_REDACTED if key.lower() in SENSITIVE_KEYS else _mask_value(value))
        for key, value in event_dict.items()
    }


def configure_logging(settings: Settings) -> None:
    """Configure stdlib logging + structlog. Idempotent."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
        force=True,
    )
    # Third-party loggers are noisy at DEBUG.
    for noisy in ("httpx", "httpcore", "asyncio", "aiosqlite"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    shared: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        mask_secrets,
    ]
    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer(ensure_ascii=False)
        if settings.log_format is LogFormat.JSON
        else structlog.dev.ConsoleRenderer(colors=False)
    )

    structlog.configure(
        processors=[*shared, structlog.processors.format_exc_info, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level)),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)  # type: ignore[no-any-return]
