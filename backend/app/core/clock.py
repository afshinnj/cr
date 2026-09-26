"""Injectable clock (ADR-009).

Nothing in the domain layer may call ``datetime.now()`` directly. Backtesting
replaces :class:`RealClock` with :class:`VirtualClock` so that *exactly the same
code* runs live and in replay. ``scripts/check_architecture.py`` enforces this.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta


class Clock(ABC):
    """Abstract source of 'now'. Always timezone-aware UTC."""

    @abstractmethod
    def now(self) -> datetime:
        """Current instant as an aware UTC datetime."""

    def today(self) -> datetime:
        n = self.now()
        return n.replace(hour=0, minute=0, second=0, microsecond=0)

    def timestamp(self) -> float:
        return self.now().timestamp()


class RealClock(Clock):
    """Wall-clock time. The only implementation allowed in live mode."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class VirtualClock(Clock):
    """Deterministic clock for backtesting and tests."""

    def __init__(self, start: datetime) -> None:
        if start.tzinfo is None:
            raise ValueError("VirtualClock requires a timezone-aware datetime")
        self._now = start.astimezone(UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> datetime:
        self._now += delta
        return self._now

    def set(self, moment: datetime) -> datetime:
        if moment.tzinfo is None:
            raise ValueError("VirtualClock requires a timezone-aware datetime")
        self._now = moment.astimezone(UTC)
        return self._now


_default_clock: Clock = RealClock()


def get_clock() -> Clock:
    """FastAPI dependency / service default."""
    return _default_clock
