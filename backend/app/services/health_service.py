"""Deep health checks for every infrastructure dependency.

The UI must always be able to tell the user *which* component is unavailable
rather than silently showing stale or fabricated data (requirement §29).
"""

from __future__ import annotations

import asyncio
import time
from typing import Final

import httpx
from sqlalchemy import text

from app.core.config import AIProviderName, Settings
from app.core.logging import get_logger
from app.schemas.system import ComponentHealth

logger = get_logger(__name__)

_PROBE_TIMEOUT_SECONDS: Final = 5.0


async def _timed(coro_factory, name: str, optional: bool) -> ComponentHealth:  # type: ignore[no-untyped-def]
    started = time.perf_counter()
    try:
        detail = await asyncio.wait_for(coro_factory(), timeout=_PROBE_TIMEOUT_SECONDS)
        elapsed = (time.perf_counter() - started) * 1000
        return ComponentHealth(
            name=name, status="ok", latency_ms=round(elapsed, 2), detail=detail, optional=optional
        )
    except TimeoutError:
        return ComponentHealth(
            name=name,
            status="down",
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            detail=f"probe timed out after {_PROBE_TIMEOUT_SECONDS}s",
            optional=optional,
        )
    except Exception as exc:
        logger.warning("health_probe_failed", component=name, error=str(exc))
        return ComponentHealth(
            name=name,
            status="down",
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            detail=type(exc).__name__ + ": " + str(exc)[:200],
            optional=optional,
        )


class HealthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def check_database(self) -> str:
        from app.database.session import get_engine

        engine = get_engine()
        dialect = engine.dialect.name
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            if dialect != "postgresql":
                return dialect
            # Timescale is required for the hypertables; report it explicitly.
            result = await conn.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'")
            )
            row = result.first()
            if row is None:
                raise RuntimeError("timescaledb extension is not installed")
            return f"postgresql + timescaledb {row[0]}"

    async def check_redis(self) -> str:
        import redis.asyncio as aioredis

        client = aioredis.from_url(self.settings.redis_dsn)
        try:
            await client.ping()
            info: dict[str, object] = await client.info("server")
            return f"redis {info.get('redis_version', 'unknown')}"
        finally:
            await client.aclose()

    async def check_ai(self) -> str:
        if self.settings.ai_provider is AIProviderName.NULL:
            return "ai provider disabled"
        if self.settings.ai_provider is not AIProviderName.OLLAMA:
            return f"provider {self.settings.ai_provider} not probed"
        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_SECONDS) as client:
            response = await client.get(f"{self.settings.ollama_host}/api/tags")
            response.raise_for_status()
            models = [m["name"] for m in response.json().get("models", [])]
        if self.settings.ai_model not in models:
            raise RuntimeError(
                f"model '{self.settings.ai_model}' not pulled; available: {models[:5]}"
            )
        return f"ollama, model {self.settings.ai_model} available"

    async def check_all(self) -> list[ComponentHealth]:
        checks = [
            _timed(self.check_database, "database", optional=False),
            _timed(self.check_redis, "redis", optional=False),
        ]
        checks.append(_timed(self.check_ai, "ai", optional=True))
        return list(await asyncio.gather(*checks))

    @staticmethod
    def overall(components: list[ComponentHealth]) -> tuple[str, list[str]]:
        """Aggregate component states into one status plus a degraded list."""
        degraded = [c.name for c in components if c.status != "ok"]
        required_down = [c.name for c in components if c.status != "ok" and not c.optional]
        if required_down:
            return "down", degraded
        if degraded:
            return "degraded", degraded
        return "ok", []
