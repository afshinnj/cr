"""Loader for the YAML configuration files under ``/config``.

Keeping tunables in YAML (and, for scoring, in the database) is what makes
invariant I10 — "no hard-coded values" — enforceable.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

from app.core.errors import ConfigurationError


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {path}", path=str(path))
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid YAML in {path}: {exc}", path=str(path)) from exc
    if not isinstance(data, dict):
        raise ConfigurationError(f"Expected a mapping at the root of {path}", path=str(path))
    return data


@functools.lru_cache(maxsize=32)
def _load_cached(path_str: str) -> dict[str, Any]:
    return load_yaml(Path(path_str))


class ConfigFiles:
    """Typed accessors for the configuration directory."""

    def __init__(self, config_dir: Path) -> None:
        self.config_dir = config_dir

    def _get(self, filename: str) -> dict[str, Any]:
        return _load_cached(str(self.config_dir / filename))

    @property
    def markets(self) -> dict[str, Any]:
        markets: dict[str, Any] = self._get("markets.yaml")["markets"]
        return markets

    @property
    def sources(self) -> list[dict[str, Any]]:
        return list(self._get("sources.yaml")["sources"])

    @property
    def scoring_profiles(self) -> list[dict[str, Any]]:
        return list(self._get("scoring.yaml")["profiles"])

    @property
    def universe_profiles(self) -> dict[str, Any]:
        profiles: dict[str, Any] = self._get("universe.yaml")["profiles"]
        return profiles

    def market(self, market_type: str) -> dict[str, Any]:
        markets = self.markets
        if market_type not in markets:
            raise ConfigurationError(
                f"Unknown market type '{market_type}' in markets.yaml",
                available=sorted(markets),
            )
        return dict(markets[market_type])

    def universe(self, profile: str) -> dict[str, Any]:
        profiles = self.universe_profiles
        if profile not in profiles:
            raise ConfigurationError(
                f"Unknown universe profile '{profile}'", available=sorted(profiles)
            )
        return dict(profiles[profile])
