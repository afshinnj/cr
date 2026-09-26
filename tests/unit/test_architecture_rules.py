"""The architecture checker itself is tested — a silent checker is worthless."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "scripts" / "check_architecture.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import check_architecture as ca  # noqa: E402


def _check(source: str, relative: str, func) -> list[ca.Violation]:  # type: ignore[no-untyped-def]
    path = ca.APP_ROOT / relative
    return func(path, ast.parse(source))


def test_checker_passes_on_the_current_codebase() -> None:
    result = subprocess.run(
        [sys.executable, str(CHECKER)], capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert result.returncode == 0, result.stdout + result.stderr


class TestImportRules:
    def test_risk_importing_ai_is_a_violation(self) -> None:
        """Invariant I6."""
        violations = _check(
            "from app.ai.base import AIProvider", "risk/engine.py", ca.check_imports
        )
        assert [v.rule for v in violations] == ["I6"]

    def test_indicators_importing_ai_is_a_violation(self) -> None:
        """Invariant I5."""
        violations = _check(
            "import app.ai.ollama_provider", "indicators/trend.py", ca.check_imports
        )
        assert [v.rule for v in violations] == ["I5"]

    def test_api_importing_orm_models_is_a_violation(self) -> None:
        """Invariant I2."""
        violations = _check("from app.models import Asset", "api/v1/assets.py", ca.check_imports)
        assert [v.rule for v in violations] == ["I2"]

    def test_allowed_imports_produce_no_violations(self) -> None:
        source = "from app.core.enums import Timeframe\nimport numpy as np"
        assert _check(source, "risk/engine.py", ca.check_imports) == []

    def test_rules_only_apply_to_their_own_package(self) -> None:
        assert _check("from app.ai.base import X", "services/ai_service.py", ca.check_imports) == []


class TestEnvironmentRule:
    def test_os_environ_outside_config_is_a_violation(self) -> None:
        violations = _check(
            "import os\nx = os.environ['SECRET']", "services/x.py", ca.check_env_access
        )
        assert [v.rule for v in violations] == ["I11"]

    def test_config_module_may_read_the_environment(self) -> None:
        assert _check("import os\nos.getenv('X')", "core/config.py", ca.check_env_access) == []


class TestClockRule:
    def test_datetime_now_is_a_violation(self) -> None:
        source = "from datetime import datetime\nx = datetime.now()"
        violations = _check(source, "services/x.py", ca.check_clock_usage)
        assert [v.rule for v in violations] == ["ADR-009"]

    def test_utcnow_is_a_violation(self) -> None:
        source = "import datetime\nx = datetime.datetime.utcnow()"
        assert _check(source, "services/x.py", ca.check_clock_usage)

    def test_clock_module_is_exempt(self) -> None:
        source = "from datetime import datetime\nx = datetime.now()"
        assert _check(source, "core/clock.py", ca.check_clock_usage) == []

    def test_clock_now_is_allowed(self) -> None:
        assert _check("x = clock.now()", "services/x.py", ca.check_clock_usage) == []


class TestMockIsolation:
    def test_importing_mock_providers_from_production_code_is_a_violation(self) -> None:
        """Invariant I9 / requirement §29."""
        violations = _check(
            "from app.providers.mock.crypto import MockCrypto",
            "services/market_service.py",
            ca.check_mock_isolation,
        )
        assert [v.rule for v in violations] == ["I9"]

    def test_mock_package_may_import_itself(self) -> None:
        assert (
            _check(
                "from app.providers.mock.base import Base",
                "providers/mock/crypto.py",
                ca.check_mock_isolation,
            )
            == []
        )
