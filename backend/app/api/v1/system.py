"""System, health and configuration endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app import __version__
from app.api.deps import ClockDep, LocalAuth, SettingsDep
from app.schemas.system import (
    ConfigResponse,
    DeepHealthResponse,
    HealthResponse,
    SafeSettingsResponse,
)
from app.services.health_service import HealthService

router = APIRouter(tags=["system"])

DISCLAIMER_FA = (
    "این خروجی حاصل تحلیل آماری داده‌های تاریخی و لحظه‌ای است، نه پیش‌بینی قطعی. "
    "عملکرد گذشته تضمینی برای آینده نیست."
)


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health(settings: SettingsDep, clock: ClockDep) -> HealthResponse:
    return HealthResponse(
        app=settings.app_name,
        version=__version__,
        env=settings.env.value,
        data_mode=settings.data_mode.value,
        time=clock.now(),
    )


@router.get(
    "/health/deep",
    response_model=DeepHealthResponse,
    summary="Readiness probe covering every dependency",
)
async def health_deep(
    settings: SettingsDep, clock: ClockDep, response: Response
) -> DeepHealthResponse:
    service = HealthService(settings)
    components = await service.check_all()
    overall, degraded = service.overall(components)
    if overall == "down":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return DeepHealthResponse(
        status=overall,
        app=settings.app_name,
        version=__version__,
        env=settings.env.value,
        data_mode=settings.data_mode.value,
        time=clock.now(),
        components=components,
        degraded=degraded,
    )


@router.get(
    "/system/config",
    response_model=ConfigResponse,
    summary="Public configuration",
    dependencies=[LocalAuth],
)
async def system_config(settings: SettingsDep) -> ConfigResponse:
    return ConfigResponse(
        app_name=settings.app_name,
        env=settings.env.value,
        data_mode=settings.data_mode.value,
        api_prefix=settings.api_prefix,
        universe_profile=settings.universe_profile.value,
        persisted_timeframes=settings.persisted_timeframes,
        ai_provider=settings.ai_provider.value,
        ai_model=settings.ai_model,
        disclaimer=DISCLAIMER_FA,
    )


@router.get(
    "/system/settings",
    response_model=SafeSettingsResponse,
    summary="Full settings with secrets redacted",
    dependencies=[LocalAuth],
)
async def system_settings(settings: SettingsDep) -> SafeSettingsResponse:
    return SafeSettingsResponse(settings=settings.safe_dump())
