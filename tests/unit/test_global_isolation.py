"""Meta-tests verifying the autouse isolation fixture in tests/conftest.py.

These guard the reorder-safety guarantees that let the suite run under
pytest-xdist: config-driving env vars are cleared and cached singletons are
reset before every test, so the developer's real ``.env`` (loaded into
``os.environ`` by import-time ``load_dotenv()`` calls) never bleeds into a test
or its failure output.
"""

import os

import pytest

from finwiz.config.manager import ConfigurationError, ConfigurationManager


def test_api_key_env_vars_are_isolated():
    # Real .env keys must never be visible inside tests.
    for var in ("SERPER_API_KEY", "CHART_IMG_API_KEY", "KRAKEN_API_KEY"):
        assert os.getenv(var) is None, f"{var} leaked into the test environment"


def test_resilience_env_vars_are_isolated():
    assert os.getenv("FINWIZ_MAX_RETRIES") is None


def test_building_configuration_manager_sees_no_real_keys():
    # Constructing a manager inside a test must find no API keys — proving the
    # import-time .env pollution was cleared and nothing leaks into api_keys
    # (which is what gets printed on failure).
    mgr = ConfigurationManager()
    with pytest.raises(ConfigurationError) as exc:
        mgr.validate_api_keys()
    assert "SERPER_API_KEY" in exc.value.missing_keys
    assert mgr.api_keys == {}, "real .env keys leaked into ConfigurationManager.api_keys"


def test_config_manager_singleton_is_reset():
    import finwiz.config.manager as cfg

    assert cfg._config_manager is None


def test_settings_singleton_is_reset():
    import finwiz.config.settings as settings

    assert settings._settings is None


def test_resilience_singleton_is_reset():
    import finwiz.config.resilience_config as res

    assert res._resilience_config is None


def test_feature_flags_singleton_is_reset():
    import finwiz.config.features.flags as flags

    assert flags._feature_flags is None


def test_token_monitor_singleton_is_reset():
    import finwiz.infrastructure.monitoring.litellm_callback as llm

    assert llm._token_monitor is None
