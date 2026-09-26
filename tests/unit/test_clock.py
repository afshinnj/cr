"""The injectable clock is what makes backtest == live (ADR-009)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.core.clock import RealClock, VirtualClock


class TestRealClock:
    def test_returns_timezone_aware_utc(self) -> None:
        now = RealClock().now()
        assert now.tzinfo is not None
        assert now.utcoffset() == timedelta(0)

    def test_advances(self) -> None:
        clock = RealClock()
        assert clock.now() <= clock.now()


class TestVirtualClock:
    def test_is_deterministic(self) -> None:
        start = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
        clock = VirtualClock(start)
        assert clock.now() == start
        assert clock.now() == start

    def test_advance(self) -> None:
        clock = VirtualClock(datetime(2024, 1, 1, tzinfo=UTC))
        clock.advance(timedelta(hours=4))
        assert clock.now() == datetime(2024, 1, 1, 4, 0, tzinfo=UTC)

    def test_set(self) -> None:
        clock = VirtualClock(datetime(2024, 1, 1, tzinfo=UTC))
        clock.set(datetime(2025, 6, 1, tzinfo=UTC))
        assert clock.now().year == 2025

    def test_naive_datetime_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            VirtualClock(datetime(2024, 1, 1))  # noqa: DTZ001

    def test_non_utc_input_is_normalised(self) -> None:
        from datetime import timezone

        tehran = timezone(timedelta(hours=3, minutes=30))
        clock = VirtualClock(datetime(2024, 1, 1, 12, 0, tzinfo=tehran))
        assert clock.now() == datetime(2024, 1, 1, 8, 30, tzinfo=UTC)

    def test_today_truncates_time(self) -> None:
        clock = VirtualClock(datetime(2024, 3, 15, 17, 45, 12, tzinfo=UTC))
        assert clock.today() == datetime(2024, 3, 15, 0, 0, tzinfo=UTC)
