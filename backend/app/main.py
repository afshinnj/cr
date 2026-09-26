"""FastAPI application factory."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.errors import register_exception_handlers
from app.api.v1.router import api_router
from app.core.config import DataMode, Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.database.session import dispose_engine, init_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    init_engine(settings)
    logger.info(
        "application_startup",
        version=__version__,
        env=settings.env.value,
        data_mode=settings.data_mode.value,
        universe_profile=settings.universe_profile.value,
        ai_provider=settings.ai_provider.value,
    )
    if settings.data_mode is DataMode.MOCK:
        # Loud and repeated: mock data must never be mistaken for real data (§29).
        logger.warning(
            "mock_data_mode_enabled",
            detail="Market data is SIMULATED. Not valid for any real decision.",
        )
    try:
        yield
    finally:
        await dispose_engine()
        logger.info("application_shutdown")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Multi-layer market analysis for the Tehran Stock Exchange and crypto markets. "
            "Outputs are statistical assessments (opportunity / risk / confidence), "
            "not price predictions."
        ),
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def bind_trace_id(request: Request, call_next):  # type: ignore[no-untyped-def]
        """Attach a trace id to every log line emitted while serving a request."""
        trace_id = request.headers.get("X-Trace-Id") or uuid.uuid4().hex
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id, path=request.url.path, method=request.method
        )
        try:
            response: Response = await call_next(request)
        finally:
            structlog.contextvars.unbind_contextvars("trace_id", "path", "method")
        response.headers["X-Trace-Id"] = trace_id
        return response

    # The app instance owns its settings: tests and embedded runs can pass a
    # different Settings object without touching the global cache.
    app.dependency_overrides[get_settings] = lambda: settings

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
