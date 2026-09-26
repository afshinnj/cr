"""Schemas for the system/health endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

HealthState = Literal["ok", "degraded", "down", "disabled", "unknown"]


class ComponentHealth(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    status: HealthState
    latency_ms: float | None = None
    detail: str | None = None
    #: True when the system keeps working without this component (e.g. Ollama).
    optional: bool = False


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    app: str
    version: str
    env: str
    data_mode: str
    time: datetime


class DeepHealthResponse(BaseModel):
    status: HealthState
    app: str
    version: str
    env: str
    data_mode: str
    time: datetime
    components: list[ComponentHealth]
    #: Names of degraded/unavailable components — the UI shows a red banner (§29).
    degraded: list[str] = Field(default_factory=list)


class ConfigResponse(BaseModel):
    """Non-secret configuration exposed to the desktop client."""

    app_name: str
    env: str
    data_mode: str
    api_prefix: str
    universe_profile: str
    persisted_timeframes: list[str]
    ai_provider: str
    ai_model: str
    disclaimer: str


class SafeSettingsResponse(BaseModel):
    """Full settings dump with every secret redacted (requirement §25)."""

    settings: dict[str, Any]
