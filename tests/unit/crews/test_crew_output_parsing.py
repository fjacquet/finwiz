"""
Crew output parsing tests.

Tests the 3-branch Pydantic access cascade in CrewFactory:
  1. result.pydantic.model_dump()  (structured output)
  2. result.json_dict              (JSON dict fallback)
  3. {"raw_output": result.raw}    (raw string fallback)

Also covers feature flag disabled path and error handler fallback.
Uses pytest-mock exclusively (mocker fixture).
"""

import pytest

from finwiz.crew_factory import CrewFactory


class TestCrewOutputParsing:
    """Tests for CrewAI output format variations in CrewFactory."""

    @pytest.fixture
    def factory(self, mocker):
        """Create CrewFactory with mocked dependencies."""
        integration_manager = mocker.Mock()
        error_handler = mocker.Mock()
        return CrewFactory(
            integration_manager=integration_manager,
            error_handler=error_handler,
        )

    @pytest.fixture
    def mock_crew_run(self, mocker):
        """Helper: mock _run_crew_with_timeout to return a given result."""

        def _setup(factory_instance, mock_result, crew_class_path):
            mocker.patch(crew_class_path)
            mocker.patch.object(factory_instance, "_run_crew_with_timeout", return_value=mock_result)

        return _setup

    @pytest.fixture
    def mock_feature_enabled(self, mocker):
        """Mock is_feature_enabled to return True for all flags by default."""
        return mocker.patch("finwiz.crew_factory.is_feature_enabled", return_value=True)

    # ---- Crypto crew: pydantic path ----

    def test_crypto_crew_pydantic_output(self, factory, mocker, mock_crew_run, mock_feature_enabled):
        """Crypto crew with pydantic output uses model_dump()."""
        mock_pydantic = mocker.Mock()
        mock_pydantic.model_dump.return_value = {"recommendation": "BUY", "score": 0.85}

        mock_result = mocker.Mock()
        mock_result.pydantic = mock_pydantic
        mock_result.json_dict = None
        mock_result.raw = "fallback text"

        mock_crew_run(factory, mock_result, "finwiz.crew_factory.CryptoCrew")

        result = factory.execute_crypto_crew({"ticker": "BTC"})

        assert result["crypto_analysis_success"] is True
        assert result["crypto_analysis_result"] == {"recommendation": "BUY", "score": 0.85}

    # ---- Crypto crew: json_dict path ----

    def test_crypto_crew_json_dict_output(self, factory, mocker, mock_crew_run, mock_feature_enabled):
        """Crypto crew with json_dict output uses json_dict directly."""
        mock_result = mocker.Mock()
        mock_result.pydantic = None
        mock_result.json_dict = {"recommendation": "HOLD"}
        mock_result.raw = "fallback"

        mock_crew_run(factory, mock_result, "finwiz.crew_factory.CryptoCrew")

        result = factory.execute_crypto_crew({"ticker": "BTC"})

        assert result["crypto_analysis_success"] is True
        assert result["crypto_analysis_result"] == {"recommendation": "HOLD"}

    # ---- Crypto crew: raw fallback path ----

    def test_crypto_crew_raw_fallback_output(self, factory, mocker, mock_crew_run, mock_feature_enabled):
        """Crypto crew with no pydantic/json_dict falls back to raw output."""
        mock_result = mocker.Mock()
        mock_result.pydantic = None
        mock_result.json_dict = None
        mock_result.raw = "Raw analysis text"

        mock_crew_run(factory, mock_result, "finwiz.crew_factory.CryptoCrew")

        result = factory.execute_crypto_crew({"ticker": "BTC"})

        assert result["crypto_analysis_success"] is True
        assert result["crypto_analysis_result"] == {"raw_output": "Raw analysis text"}

    # ---- Crypto crew: pydantic model_dump error ----

    def test_crypto_crew_pydantic_model_dump_error(self, factory, mocker, mock_feature_enabled):
        """Pydantic model_dump() raising AttributeError triggers exception path."""
        mock_pydantic = mocker.Mock()
        mock_pydantic.model_dump.side_effect = AttributeError("no model_dump")

        mock_result = mocker.Mock()
        mock_result.pydantic = mock_pydantic
        mock_result.json_dict = None
        mock_result.raw = "fallback"

        mocker.patch("finwiz.crew_factory.CryptoCrew")
        mocker.patch.object(factory, "_run_crew_with_timeout", return_value=mock_result)

        result = factory.execute_crypto_crew({"ticker": "BTC"})

        # The AttributeError bubbles up into the outer except Exception handler
        assert result["crypto_analysis_success"] is False
        assert "crypto_analysis_error" in result

    # ---- Stock crew: pydantic path ----

    def test_stock_crew_pydantic_output(self, factory, mocker, mock_crew_run, mock_feature_enabled):
        """Stock crew with pydantic output uses model_dump()."""
        mock_pydantic = mocker.Mock()
        mock_pydantic.model_dump.return_value = {"recommendation": "SELL", "score": 0.3}

        mock_result = mocker.Mock()
        mock_result.pydantic = mock_pydantic
        mock_result.json_dict = None
        mock_result.raw = "fallback"

        mock_crew_run(factory, mock_result, "finwiz.crew_factory.StockCrew")

        result = factory.execute_stock_crew({"ticker": "AAPL"})

        assert result["stock_analysis_success"] is True
        assert result["stock_analysis_result"] == {"recommendation": "SELL", "score": 0.3}

    # ---- Stock crew: json_dict path ----

    def test_stock_crew_json_dict_output(self, factory, mocker, mock_crew_run, mock_feature_enabled):
        """Stock crew with json_dict output uses json_dict directly."""
        mock_result = mocker.Mock()
        mock_result.pydantic = None
        mock_result.json_dict = {"recommendation": "HOLD", "confidence": 0.7}
        mock_result.raw = "fallback"

        mock_crew_run(factory, mock_result, "finwiz.crew_factory.StockCrew")

        result = factory.execute_stock_crew({"ticker": "AAPL"})

        assert result["stock_analysis_success"] is True
        assert result["stock_analysis_result"] == {"recommendation": "HOLD", "confidence": 0.7}

    # ---- Stock crew: raw fallback path ----

    def test_stock_crew_raw_fallback_output(self, factory, mocker, mock_crew_run, mock_feature_enabled):
        """Stock crew with no pydantic/json_dict falls back to raw output."""
        mock_result = mocker.Mock()
        mock_result.pydantic = None
        mock_result.json_dict = None
        mock_result.raw = "Raw stock analysis"

        mock_crew_run(factory, mock_result, "finwiz.crew_factory.StockCrew")

        result = factory.execute_stock_crew({"ticker": "AAPL"})

        assert result["stock_analysis_success"] is True
        assert result["stock_analysis_result"] == {"raw_output": "Raw stock analysis"}

    # ---- ETF crew: pydantic path ----

    def test_etf_crew_pydantic_output(self, factory, mocker, mock_crew_run, mock_feature_enabled):
        """ETF crew with pydantic output uses model_dump()."""
        mock_pydantic = mocker.Mock()
        mock_pydantic.model_dump.return_value = {"recommendation": "BUY", "expense_ratio": 0.03}

        mock_result = mocker.Mock()
        mock_result.pydantic = mock_pydantic
        mock_result.json_dict = None
        mock_result.raw = "fallback"

        mock_crew_run(factory, mock_result, "finwiz.crew_factory.EtfCrew")

        result = factory.execute_etf_crew({"ticker": "SPY"})

        assert result["etf_analysis_success"] is True
        assert result["etf_analysis_result"] == {"recommendation": "BUY", "expense_ratio": 0.03}

    # ---- ETF crew: raw fallback path ----

    def test_etf_crew_raw_fallback_output(self, factory, mocker, mock_crew_run, mock_feature_enabled):
        """ETF crew with no pydantic/json_dict falls back to raw output."""
        mock_result = mocker.Mock()
        mock_result.pydantic = None
        mock_result.json_dict = None
        mock_result.raw = "Raw ETF analysis"

        mock_crew_run(factory, mock_result, "finwiz.crew_factory.EtfCrew")

        result = factory.execute_etf_crew({"ticker": "SPY"})

        assert result["etf_analysis_success"] is True
        assert result["etf_analysis_result"] == {"raw_output": "Raw ETF analysis"}

    # ---- Feature flag disabled ----

    def test_crypto_crew_feature_flag_disabled(self, factory, mocker):
        """Feature flag disabled returns disabled dict without calling crew."""
        mocker.patch("finwiz.crew_factory.is_feature_enabled", return_value=False)
        mock_crypto_cls = mocker.patch("finwiz.crew_factory.CryptoCrew")

        result = factory.execute_crypto_crew({"ticker": "BTC"})

        assert result == {"crypto_analysis_disabled": True}
        mock_crypto_cls.assert_not_called()

    # ---- Stock crew execution failure with error handler ----

    def test_stock_crew_execution_failure_uses_error_handler(self, factory, mocker, mock_feature_enabled):
        """Stock crew failure invokes error_handler.handle_crew_failure for fallback."""
        mocker.patch("finwiz.crew_factory.StockCrew")
        mocker.patch.object(
            factory,
            "_run_crew_with_timeout",
            side_effect=RuntimeError("API rate limit"),
        )

        # Configure error handler fallback response
        fallback_response = mocker.Mock()
        fallback_response.success = True
        fallback_response.data = {"cached": True}
        fallback_response.fallback_strategy = "cache"
        fallback_response.degraded_functionality = ["no_live_data"]
        fallback_response.message = "Using cached data"
        factory.error_handler.handle_crew_failure.return_value = fallback_response

        result = factory.execute_stock_crew({"ticker": "AAPL"})

        assert result["stock_analysis_success"] is False
        assert result["stock_analysis_fallback"] is True
        assert result["stock_analysis_result"] == {"cached": True}
        factory.error_handler.handle_crew_failure.assert_called_once()
