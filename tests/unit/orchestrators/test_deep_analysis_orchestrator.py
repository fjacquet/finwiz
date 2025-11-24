"""Unit tests for DeepAnalysisOrchestrator."""

import json
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pytest import approx

from finwiz.flow_state import DeepAnalysisResult, FinwizState
from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator


class TestDeepAnalysisOrchestrator:
    """Test suite for DeepAnalysisOrchestrator."""

    @pytest.fixture
    def state(self):
        """Create test state."""
        return FinwizState(
            session_id="test_session",
            current_day=17,
            current_month=11,
            current_year=2025,
            current_date="2025-11-17",
            full_date="November 17, 2025",
            timestamp="2025-11-17T10:00:00",
            report_language="en",
        )

    @pytest.fixture
    def batch_config(self, mocker):
        """Create test batch config."""
        config = mocker.Mock()
        config.enabled = True
        config.min_holdings_for_batch = 3
        config.alpha_vantage_rate_limit = 5
        return config

    @pytest.fixture
    def orchestrator(self, state, batch_config):
        """Create orchestrator instance."""
        return DeepAnalysisOrchestrator(state, batch_prefetch_config=batch_config, cache_service=None, cache_enabled=False)

    def test_should_return_empty_dict_when_no_holdings(self, orchestrator):
        """Test deep analysis with no holdings."""
        result = orchestrator.run_deep_analysis_on_holdings([])
        assert result == {}

    def test_should_create_result_from_pydantic_output(self, orchestrator, mocker):
        """Test result creation from crew output with pydantic."""
        # Arrange
        pydantic_data = mocker.Mock()
        pydantic_data.model_dump.return_value = {"grade": "A", "composite_score": 0.85, "fundamental_score": 0.9, "technical_score": 0.8, "risk_score": 2.5}
        pydantic_data.fundamental_score = 0.9
        pydantic_data.technical_score = 0.8
        pydantic_data.risk_score = 2.5

        crew_output = mocker.Mock()
        crew_output.pydantic = pydantic_data

        # Mock extractor at the source import location
        mock_extractor = mocker.patch("finwiz.utils.data_extractor.CrewDataExtractor")
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.extract_grade_and_score.return_value = {"grade": "A", "composite_score": 0.85}
        mock_extractor_instance.validate_grade_score_consistency.return_value = True

        # Act
        result = orchestrator.create_deep_analysis_result_from_crew_output(crew_output, "AAPL", "stock", "TestCrew", False)

        # Assert
        assert isinstance(result, DeepAnalysisResult)
        assert result.ticker == "AAPL"
        assert result.asset_class == "stock"
        assert result.grade == "A"
        assert result.composite_score == approx(0.85)
        assert result.fundamental_score == approx(0.9)
        assert result.technical_score == approx(0.8)
        assert result.risk_score == approx(2.5)

    def test_should_parse_from_raw_output(self, orchestrator, mocker):
        """Test parsing from raw text output."""
        # Arrange
        crew_output = mocker.Mock()
        crew_output.pydantic = None
        crew_output.raw = "Analysis complete. Grade: B Score: 0.75"

        # Act
        result = orchestrator.create_deep_analysis_result_from_crew_output(crew_output, "MSFT", "stock", "TestCrew", False)

        # Assert
        assert result.ticker == "MSFT"
        assert result.grade == "B"
        assert result.composite_score == approx(0.75)

    def test_should_save_metrics_to_file(self, orchestrator, tmp_path):
        """Test metrics file saving."""
        # Arrange
        metrics = {"total_tickers": 10, "successful_tickers": 9, "prefetch_duration_seconds": 5.5}
        output_path = str(tmp_path / "metrics.json")

        # Act
        orchestrator.save_batch_metrics_to_file(metrics, output_path)

        # Assert
        assert Path(output_path).exists()
        with open(output_path) as f:
            saved_metrics = json.load(f)
        assert saved_metrics["total_tickers"] == 10
        assert saved_metrics["successful_tickers"] == 9

    def test_should_handle_missing_required_fields(self, orchestrator, mocker):
        """Test error handling for missing fields."""
        from finwiz.exceptions.data_quality import MissingRequiredFieldError

        # Arrange
        crew_output = mocker.Mock()
        crew_output.pydantic = None
        crew_output.raw = "No grade or score here"

        # Act & Assert
        with pytest.raises(MissingRequiredFieldError):
            orchestrator.create_deep_analysis_result_from_crew_output(crew_output, "TEST", "stock", "TestCrew", False)

    @pytest.mark.parametrize(
        "holdings",
        [
            [{"ticker": "AAPL", "asset_class": "stock"}],
            [{"ticker": "AAPL", "asset_class": "stock"}, {"ticker": "GOOGL", "asset_class": "stock"}],
            [{"ticker": "AAPL", "asset_class": "stock"}, {"ticker": "SPY", "asset_class": "etf"}, {"ticker": "BTC", "asset_class": "crypto"}],
        ],
    )
    def test_property_deep_analysis_completeness(self, mocker, holdings):
        """
        **Feature: flow-orchestrator-refactoring, Property 8: Deep Analysis Completeness**

        For any portfolio with N holdings, the DeepAnalysisOrchestrator
        should execute analysis on all N holdings.

        **Validates: Requirements 3.1**
        """
        # Arrange
        state = FinwizState(
            session_id="test_session",
            current_day=17,
            current_month=11,
            current_year=2025,
            current_date="2025-11-17",
            full_date="November 17, 2025",
            timestamp="2025-11-17T10:00:00",
            report_language="en",
        )

        batch_config = mocker.Mock()
        batch_config.enabled = False  # Disable batch mode for simplicity
        batch_config.min_holdings_for_batch = 100  # Set high to avoid batch mode

        orchestrator = DeepAnalysisOrchestrator(state, batch_prefetch_config=batch_config, cache_service=None, cache_enabled=False)

        # Mock _collect_data_with_python to prevent slow flow execution (CRITICAL for fast tests)
        mocker.patch.object(
            orchestrator,
            "_collect_data_with_python",
            return_value={"price": 150.0, "volume": 1000000, "market_cap": 2500000000000},
        )

        # Mock DeepAnalysisScorer to prevent actual scoring and return proper DeepAnalysisResult objects
        def create_score_result(ticker_arg, asset_class_arg, raw_data):
            return DeepAnalysisResult(
                ticker=ticker_arg,
                asset_class=asset_class_arg,
                crew_name="DeepAnalysisCrew",
                analysis_timestamp="2025-11-17T10:00:00",
                composite_score=0.85,
                grade="A",
                recommendation="BUY",
                rationale="Test analysis",
                risk_details={},
                fundamental_score=0.9,
                technical_score=0.8,
                risk_score=2.5,
                data_freshness_hours=1.0,
                confidence_level=0.9,
                warnings=[],
                cached=False,
            )

        mock_scorer = mocker.Mock()
        mock_scorer.calculate_composite_score.side_effect = create_score_result
        mocker.patch("finwiz.scoring.deep_analysis_scorer.DeepAnalysisScorer", return_value=mock_scorer)

        # Create a mock result that will be returned for each holding
        def create_mock_result(ticker, asset_class):
            mock_result = mocker.Mock()
            mock_pydantic = mocker.Mock()
            mock_pydantic.model_dump.return_value = {"grade": "A", "composite_score": 0.85, "fundamental_score": 0.9, "technical_score": 0.8, "risk_score": 2.5}
            mock_pydantic.fundamental_score = 0.9
            mock_pydantic.technical_score = 0.8
            mock_pydantic.risk_score = 2.5
            mock_result.pydantic = mock_pydantic
            return mock_result

        # Configure mock to return different results based on inputs
        def kickoff_side_effect(inputs):
            ticker = inputs.get("ticker")
            asset_class = inputs.get("asset_class")
            return create_mock_result(ticker, asset_class)

        # Mock the crew execution to return valid results
        mock_crew_class = mocker.patch("finwiz.crews.deep_analysis.deep_analysis.DeepAnalysisCrew")
        mock_cache_mgr = mocker.patch("finwiz.cache.analysis_cache_manager.get_analysis_cache_manager")
        mock_extractor = mocker.patch("finwiz.utils.data_extractor.CrewDataExtractor")

        mock_crew_instance = mock_crew_class.return_value
        mock_crew = mock_crew_instance.crew.return_value
        mock_crew.kickoff.side_effect = kickoff_side_effect

        mock_cache_instance = mock_cache_mgr.return_value
        mock_cache_instance.get_cached_analysis.return_value = None
        mock_cache_instance.log_cache_stats.return_value = None

        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.extract_grade_and_score.return_value = {"grade": "A", "composite_score": 0.85}
        mock_extractor_instance.validate_grade_score_consistency.return_value = True

        # Act
        results = orchestrator.run_deep_analysis_on_holdings(holdings)

        # Assert - Property 8: Completeness
        # For any portfolio with N holdings, all N holdings should be analyzed
        assert len(results) == len(holdings), f"Expected {len(holdings)} results but got {len(results)}. All holdings should be analyzed."

        # Verify each holding has a corresponding result
        for holding in holdings:
            ticker = holding["ticker"]
            assert ticker in results, f"Ticker {ticker} not found in results. Every holding should have an analysis result."

            # Verify the result is a valid DeepAnalysisResult
            result = results[ticker]
            assert isinstance(result, DeepAnalysisResult), f"Result for {ticker} is not a DeepAnalysisResult instance"

            # Verify the result has the correct ticker and asset_class
            assert result.ticker == ticker, f"Result ticker {result.ticker} doesn't match holding ticker {ticker}"
            assert result.asset_class == holding["asset_class"], f"Result asset_class {result.asset_class} doesn't match holding asset_class {holding['asset_class']}"

    @given(
        ticker=st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=1, max_size=5),
        asset_class=st.sampled_from(["stock", "etf", "crypto"]),
        grade=st.sampled_from(["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]),
        composite_score=st.floats(min_value=0.0, max_value=1.0),
        fundamental_score=st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0)),
        technical_score=st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0)),
        risk_score=st.one_of(st.none(), st.floats(min_value=0.0, max_value=5.0)),
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_result_structure_validation(self, mocker, ticker, asset_class, grade, composite_score, fundamental_score, technical_score, risk_score):
        """
        **Feature: flow-orchestrator-refactoring, Property 9: Deep Analysis Result Structure**

        For any deep analysis result, it should conform to the DeepAnalysisResult Pydantic schema.

        **Validates: Requirements 3.2**
        """
        from pydantic import ValidationError

        # Arrange
        state = FinwizState(
            session_id="test_session",
            current_day=17,
            current_month=11,
            current_year=2025,
            current_date="2025-11-17",
            full_date="November 17, 2025",
            timestamp="2025-11-17T10:00:00",
            report_language="en",
        )

        batch_config = mocker.Mock()
        batch_config.enabled = False
        batch_config.min_holdings_for_batch = 100

        orchestrator = DeepAnalysisOrchestrator(state, batch_prefetch_config=batch_config, cache_service=None, cache_enabled=False)

        # Create mock crew output with the generated values
        mock_result = mocker.Mock()
        mock_pydantic = mocker.Mock()
        mock_pydantic.model_dump.return_value = {
            "grade": grade,
            "composite_score": composite_score,
            "fundamental_score": fundamental_score,
            "technical_score": technical_score,
            "risk_score": risk_score,
        }
        mock_pydantic.fundamental_score = fundamental_score
        mock_pydantic.technical_score = technical_score
        mock_pydantic.risk_score = risk_score
        mock_result.pydantic = mock_pydantic

        mock_extractor = mocker.patch("finwiz.utils.data_extractor.CrewDataExtractor")
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.extract_grade_and_score.return_value = {"grade": grade, "composite_score": composite_score}
        mock_extractor_instance.validate_grade_score_consistency.return_value = True

        # Act
        result = orchestrator.create_deep_analysis_result_from_crew_output(mock_result, ticker, asset_class, "TestCrew", False)

        # Assert - Property 9: Result Structure Validation
        # The result should be a valid DeepAnalysisResult instance
        assert isinstance(result, DeepAnalysisResult), f"Result is not a DeepAnalysisResult instance, got {type(result)}"

        # Verify all required fields are present and have correct types
        assert isinstance(result.ticker, str), "ticker must be a string"
        assert isinstance(result.asset_class, str), "asset_class must be a string"
        assert isinstance(result.crew_name, str), "crew_name must be a string"
        assert isinstance(result.analysis_timestamp, str), "analysis_timestamp must be a string"
        assert isinstance(result.composite_score, float), "composite_score must be a float"
        assert isinstance(result.grade, str), "grade must be a string"
        assert isinstance(result.recommendation, str), "recommendation must be a string"
        assert isinstance(result.rationale, str), "rationale must be a string"
        assert isinstance(result.risk_details, dict), "risk_details must be a dict"
        assert isinstance(result.data_freshness_hours, float), "data_freshness_hours must be a float"
        assert isinstance(result.confidence_level, float), "confidence_level must be a float"
        assert isinstance(result.warnings, list), "warnings must be a list"
        assert isinstance(result.cached, bool), "cached must be a bool"

        # Verify field constraints from Pydantic schema
        assert 0.0 <= result.composite_score <= 1.0, f"composite_score {result.composite_score} must be between 0.0 and 1.0"
        assert 0.0 <= result.confidence_level <= 1.0, f"confidence_level {result.confidence_level} must be between 0.0 and 1.0"
        assert result.data_freshness_hours >= 0.0, f"data_freshness_hours {result.data_freshness_hours} must be >= 0.0"

        # Verify optional scores have correct constraints when present
        if result.fundamental_score is not None:
            assert isinstance(result.fundamental_score, float), "fundamental_score must be a float"
            assert 0.0 <= result.fundamental_score <= 1.0, f"fundamental_score {result.fundamental_score} must be between 0.0 and 1.0"

        if result.technical_score is not None:
            assert isinstance(result.technical_score, float), "technical_score must be a float"
            assert 0.0 <= result.technical_score <= 1.0, f"technical_score {result.technical_score} must be between 0.0 and 1.0"

        if result.risk_score is not None:
            assert isinstance(result.risk_score, float), "risk_score must be a float"
            assert 0.0 <= result.risk_score <= 5.0, f"risk_score {result.risk_score} must be between 0.0 and 5.0"

        # Verify the result matches the input values
        assert result.ticker == ticker, f"ticker mismatch: {result.ticker} != {ticker}"
        assert result.asset_class == asset_class, f"asset_class mismatch: {result.asset_class} != {asset_class}"
        assert result.grade == grade, f"grade mismatch: {result.grade} != {grade}"
        assert result.composite_score == composite_score, f"composite_score mismatch: {result.composite_score} != {composite_score}"

        # Verify Pydantic validation would accept this result
        # (This ensures the result can be serialized/deserialized)
        try:
            result_dict = result.model_dump()
            DeepAnalysisResult.model_validate(result_dict)
        except ValidationError as e:
            pytest.fail(f"Result failed Pydantic validation: {e}")

    @given(
        ticker=st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=1, max_size=5),
        asset_class=st.sampled_from(["stock", "etf", "crypto"]),
        grade=st.sampled_from(["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]),
        composite_score=st.floats(min_value=0.0, max_value=1.0),
        output_format=st.sampled_from(["pydantic", "raw"]),
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_parsing_correctness(self, mocker, ticker, asset_class, grade, composite_score, output_format):
        """
        **Feature: flow-orchestrator-refactoring, Property 10: Deep Analysis Parsing Correctness**

        For any crew output, the DeepAnalysisOrchestrator should extract
        ticker, grade, and composite_score fields.

        **Validates: Requirements 3.5**
        """
        # Arrange
        state = FinwizState(
            session_id="test_session",
            current_day=17,
            current_month=11,
            current_year=2025,
            current_date="2025-11-17",
            full_date="November 17, 2025",
            timestamp="2025-11-17T10:00:00",
            report_language="en",
        )

        batch_config = mocker.Mock()
        batch_config.enabled = False
        batch_config.min_holdings_for_batch = 100

        orchestrator = DeepAnalysisOrchestrator(state, batch_prefetch_config=batch_config, cache_service=None, cache_enabled=False)

        # Create mock crew output in different formats
        mock_result = mocker.Mock()

        if output_format == "pydantic":
            # Test Pydantic output format
            mock_pydantic = mocker.Mock()
            mock_pydantic.model_dump.return_value = {"grade": grade, "composite_score": composite_score, "fundamental_score": 0.9, "technical_score": 0.8, "risk_score": 2.5}
            mock_pydantic.fundamental_score = 0.9
            mock_pydantic.technical_score = 0.8
            mock_pydantic.risk_score = 2.5
            mock_result.pydantic = mock_pydantic

            mock_extractor = mocker.patch("finwiz.utils.data_extractor.CrewDataExtractor")
            mock_extractor_instance = mock_extractor.return_value
            mock_extractor_instance.extract_grade_and_score.return_value = {"grade": grade, "composite_score": composite_score}
            mock_extractor_instance.validate_grade_score_consistency.return_value = True

            # Act
            result = orchestrator.create_deep_analysis_result_from_crew_output(mock_result, ticker, asset_class, "TestCrew", False)
        else:
            # Test raw text output format
            # Note: Raw format has precision limitations due to string formatting
            mock_result.pydantic = None
            mock_result.raw = f"Analysis complete. Grade: {grade} Score: {composite_score:.3f}"

            # Act
            result = orchestrator.create_deep_analysis_result_from_crew_output(mock_result, ticker, asset_class, "TestCrew", False)

        # Assert - Property 10: Parsing Correctness
        # The orchestrator should correctly extract ticker, grade, and composite_score
        assert result.ticker == ticker, f"Failed to parse ticker correctly: expected {ticker}, got {result.ticker}"
        assert result.grade == grade, f"Failed to parse grade correctly: expected {grade}, got {result.grade}"

        # For raw format, account for precision loss due to .3f formatting
        if output_format == "raw":
            # The raw format uses .3f, so we need to compare with tolerance
            expected_score = float(f"{composite_score:.3f}")
            assert abs(result.composite_score - expected_score) < 0.0001, (
                f"Failed to parse composite_score correctly from raw format: expected {expected_score}, got {result.composite_score}"
            )
        else:
            # Pydantic format should preserve exact value
            assert result.composite_score == composite_score, f"Failed to parse composite_score correctly: expected {composite_score}, got {result.composite_score}"

        # Verify the result is a valid DeepAnalysisResult
        assert isinstance(result, DeepAnalysisResult), f"Parsing did not produce a DeepAnalysisResult, got {type(result)}"

        # Verify asset_class is preserved
        assert result.asset_class == asset_class, f"Asset class not preserved: expected {asset_class}, got {result.asset_class}"
