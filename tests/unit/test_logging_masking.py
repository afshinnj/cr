"""Secrets must never reach a log sink (requirement §25)."""

from __future__ import annotations

from app.core.logging import mask_secrets


def mask(**kwargs: object) -> dict[str, object]:
    return mask_secrets(None, "info", dict(kwargs))  # type: ignore[arg-type]


def test_top_level_sensitive_key_is_redacted() -> None:
    assert mask(password="hunter2")["password"] == "***REDACTED***"


def test_nested_sensitive_key_is_redacted() -> None:
    out = mask(context={"api_key": "abc123", "symbol": "BTCUSDT"})
    assert out["context"] == {"api_key": "***REDACTED***", "symbol": "BTCUSDT"}


def test_sensitive_key_inside_list_is_redacted() -> None:
    out = mask(items=[{"token": "t0k3n"}, {"ok": 1}])
    assert out["items"][0]["token"] == "***REDACTED***"  # type: ignore[index]


def test_inline_secret_in_free_text_is_redacted() -> None:
    out = mask(event="request failed url=https://x/y?api_key=SECRETVALUE&z=1")
    assert "SECRETVALUE" not in str(out["event"])


def test_case_insensitive_key_matching() -> None:
    assert mask(Authorization="Bearer abc")["Authorization"] == "***REDACTED***"


def test_non_sensitive_values_are_untouched() -> None:
    out = mask(symbol="BTCUSDT", rsi=58.4, count=3)
    assert out == {"symbol": "BTCUSDT", "rsi": 58.4, "count": 3}


def test_dsn_password_is_redacted_in_message() -> None:
    out = mask(event="connecting with postgres_password=pw123 to db")
    assert "pw123" not in str(out["event"])
