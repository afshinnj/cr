"""The YAML configuration files are part of the contract — validate them."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config_files import ConfigFiles
from app.core.errors import ConfigurationError

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def config() -> ConfigFiles:
    return ConfigFiles(REPO_ROOT / "config")


class TestMarkets:
    def test_both_markets_are_defined(self, config: ConfigFiles) -> None:
        assert {"crypto", "iran_stock"} <= set(config.markets)

    def test_iran_market_models_price_limits_and_queue(self, config: ConfigFiles) -> None:
        """ADR-013: without these, Iranian backtests report unachievable profits."""
        execution = config.market("iran_stock")["execution"]
        assert execution["price_limit_pct"] > 0
        assert execution["model_order_queue"] is True
        assert execution["halt_blocks_execution"] is True

    def test_every_market_declares_costs(self, config: ConfigFiles) -> None:
        for name in config.markets:
            assert config.market(name)["costs"], f"{name} has no cost model"

    def test_unknown_market_raises(self, config: ConfigFiles) -> None:
        with pytest.raises(ConfigurationError):
            config.market("nasdaq")


class TestScoringProfiles:
    def test_profiles_exist_for_both_markets(self, config: ConfigFiles) -> None:
        markets = {p["market_type"] for p in config.scoring_profiles}
        assert markets == {"crypto", "iran_stock"}

    @pytest.mark.parametrize("profile_index", [0, 1])
    def test_component_weights_sum_to_one(self, config: ConfigFiles, profile_index: int) -> None:
        weights = config.scoring_profiles[profile_index]["weights"]
        components = [
            "technical",
            "momentum",
            "volume",
            "market",
            "news",
            "sentiment",
            "liquidity",
            "ml",
        ]
        total = sum(weights[c] for c in components)
        assert total == pytest.approx(1.0, abs=1e-9)

    @pytest.mark.parametrize("profile_index", [0, 1])
    def test_confidence_weights_sum_to_one(self, config: ConfigFiles, profile_index: int) -> None:
        confidence = config.scoring_profiles[profile_index]["weights"]["confidence"]
        assert sum(confidence.values()) == pytest.approx(1.0, abs=1e-9)

    @pytest.mark.parametrize("profile_index", [0, 1])
    def test_ai_is_never_the_dominant_confidence_input(
        self, config: ConfigFiles, profile_index: int
    ) -> None:
        """Requirement §13/§32: the LLM is one input, not the arbiter."""
        confidence = config.scoring_profiles[profile_index]["weights"]["confidence"]
        assert confidence["ai"] == min(confidence.values())

    @pytest.mark.parametrize("profile_index", [0, 1])
    def test_veto_thresholds_are_present(self, config: ConfigFiles, profile_index: int) -> None:
        veto = config.scoring_profiles[profile_index]["thresholds"]["veto"]
        assert veto["rr_min"] > 1.0
        assert 0 < veto["min_data_completeness"] <= 1

    @pytest.mark.parametrize("profile_index", [0, 1])
    def test_buy_candidate_requires_better_rr_than_the_veto_floor(
        self, config: ConfigFiles, profile_index: int
    ) -> None:
        thresholds = config.scoring_profiles[profile_index]["thresholds"]
        assert thresholds["buy_candidate"]["rr_min"] >= thresholds["veto"]["rr_min"]


class TestSources:
    def test_every_source_declares_a_rate_limit_or_explains_why_not(
        self, config: ConfigFiles
    ) -> None:
        for source in config.sources:
            assert "rate_limit" in source, f"{source['code']} has no rate_limit key"

    def test_mock_source_is_disabled_by_default(self, config: ConfigFiles) -> None:
        mock = next(s for s in config.sources if s["code"] == "MOCK")
        assert mock["is_enabled"] is False
        assert mock["credibility"] == 0.0

    def test_source_codes_are_unique(self, config: ConfigFiles) -> None:
        codes = [s["code"] for s in config.sources]
        assert len(codes) == len(set(codes))


class TestUniverse:
    def test_small_profile_matches_the_agreed_scope(self, config: ConfigFiles) -> None:
        universe = config.universe("small")
        assert 25 <= len(universe["crypto"]["symbols"]) <= 40
        assert 25 <= len(universe["iran_stock"]["symbols"]) <= 60

    def test_crypto_symbols_are_unique(self, config: ConfigFiles) -> None:
        symbols = config.universe("small")["crypto"]["symbols"]
        assert len(symbols) == len(set(symbols))

    def test_iran_symbols_are_unique(self, config: ConfigFiles) -> None:
        symbols = [e["symbol"] for e in config.universe("small")["iran_stock"]["symbols"]]
        assert len(symbols) == len(set(symbols))

    def test_unknown_profile_raises(self, config: ConfigFiles) -> None:
        with pytest.raises(ConfigurationError):
            config.universe("gigantic")
