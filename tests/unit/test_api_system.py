"""API surface tests for Milestone 1."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from app.core.config import Settings


class TestHealth:
    async def test_health_is_ok(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["env"] == "test"

    async def test_health_reports_the_data_mode(self, api_client: AsyncClient) -> None:
        """The client must always know whether data is real (§29)."""
        body = (await api_client.get("/health")).json()
        assert body["data_mode"] == "mock"

    async def test_deep_health_lists_components(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/health/deep")
        names = {c["name"] for c in response.json()["components"]}
        assert names == {"database", "redis", "ai"}

    async def test_deep_health_marks_ai_as_optional(self, api_client: AsyncClient) -> None:
        """Ollama being down must never take the system down (ADR-005)."""
        components = (await api_client.get("/health/deep")).json()["components"]
        ai = next(c for c in components if c["name"] == "ai")
        assert ai["optional"] is True

    async def test_deep_health_degrades_instead_of_crashing(self, api_client: AsyncClient) -> None:
        # Redis and Ollama are not running in unit tests.
        response = await api_client.get("/health/deep")
        assert response.status_code in (200, 503)
        assert response.json()["degraded"]


class TestConfigEndpoint:
    async def test_exposes_public_config(self, api_client: AsyncClient) -> None:
        body = (await api_client.get("/system/config")).json()
        assert body["universe_profile"] == "small"
        assert body["persisted_timeframes"] == ["1h", "4h", "1d"]

    async def test_always_returns_the_financial_disclaimer(self, api_client: AsyncClient) -> None:
        """Requirement §32."""
        body = (await api_client.get("/system/config")).json()
        assert "پیش‌بینی قطعی" in body["disclaimer"]

    async def test_settings_endpoint_never_leaks_secrets(
        self, api_client: AsyncClient, settings: Settings
    ) -> None:
        body = (await api_client.get("/system/settings")).json()["settings"]
        assert body["local_api_token"] == "***"
        assert "test-token" not in str(body)


class TestLocalAuth:
    async def test_request_without_token_is_rejected(self, settings: Settings) -> None:
        from app.main import create_app

        app = create_app(settings)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test" + settings.api_prefix
        ) as client:
            response = await client.get("/system/config")
        assert response.status_code == 401
        assert response.json()["code"] == "UNAUTHORIZED"

    async def test_request_with_wrong_token_is_rejected(self, settings: Settings) -> None:
        from app.main import create_app

        app = create_app(settings)
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test" + settings.api_prefix,
            headers={"X-Local-Token": "wrong"},
        ) as client:
            response = await client.get("/system/config")
        assert response.status_code == 401


class TestErrorContract:
    async def test_unknown_route_returns_problem_details(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/does-not-exist")
        assert response.status_code == 404
        body = response.json()
        assert {"type", "title", "status", "code"} <= set(body)

    async def test_responses_carry_a_trace_id(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/health")
        assert response.headers["X-Trace-Id"]


class TestOpenAPI:
    async def test_openapi_document_is_generated(self, settings: Settings) -> None:
        from app.main import create_app

        schema = create_app(settings).openapi()
        assert schema["info"]["title"] == settings.app_name
        assert "/api/v1/health" in schema["paths"]
