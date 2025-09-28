"""
Unit tests for ValidationPipeline class.

Tests schema validation logic, cross-crew data consistency checking,
and validation error collection and reporting with full mocking.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from finwiz.integration.validation_pipeline import CrossCrewValidationResult, ValidationPipeline, ValidationPipelineResult
from finwiz.validation.enums import ValidationMode
from finwiz.validation.result import ValidationResult as BaseValidationResult


class TestValidationPipeline:
    """Test cases for ValidationPipeline class."""

    @pytest.fixture
    def mock_logger(self):
        """Mock logger for testing."""
        return Mock()

    @pytest.fixture
    def mock_validation_manager(self):
        """Mock validation manager for testing."""
        manager = Mock()
        manager.get_strictness_mode.return_value = ValidationMode.WARN
        manager.set_strictness_mode = Mock()
        return manager

    @pytest.fixture
    def validation_pipeline(self, mock_validation_manager, mock_logger):
        """Create ValidationPipeline instance for testing."""
        with patch("finwiz.integration.validation_pipeline.get_validation_manager", return_value=mock_validation_manager):
            pipeline = ValidationPipeline(
                output_dir=Path("/mock/output"), validation_manager=mock_validation_manager, logger=mock_logger
            )
            return pipeline

    @pytest.fixture
    def sample_crew_metadata(self):
        """Sample crew output metadata for testing."""
        return {
            "crew_name": "stock",
            "execution_timestamp": datetime.now().isoformat(),
            "schema_version": 1,
            "validation_status": {
                "is_valid": True,
                "validation_timestamp": datetime.now().isoformat(),
                "validation_errors": [],
                "validation_warnings": [],
                "schema_version": 1,
            },
            "data_sources": [
                {
                    "source_type": "YAHOO_FINANCE",
                    "source_url": "https://finance.yahoo.com",
                    "accessed_at": datetime.now().isoformat(),
                    "data_quality": "HIGH",
                    "response_time_ms": 150.0,
                }
            ],
            "dependencies_met": True,
            "freshness_status": {
                "is_fresh": True,
                "age_hours": 1.0,
                "max_age_hours": 24,
                "refresh_recommended": False,
                "last_updated": datetime.now().isoformat(),
            },
            "execution_duration_seconds": 45.5,
            "input_hash": "abc123",
        }

    @pytest.fixture
    def sample_stock_output(self, sample_crew_metadata):
        """Sample stock crew output for testing."""
        return {
            "metadata": sample_crew_metadata,
            "ten_k_insights": [
                {"ticker": "AAPL", "section": "Business Overview", "insight": "Apple designs and manufactures consumer electronics"}
            ],
            "validated_tickers": [
                {
                    "symbol": "AAPL",
                    "is_valid": True,
                    "validation_source": "yahoo_finance",
                    "validation_timestamp": datetime.now().isoformat(),
                    "market": "NASDAQ",
                    "sector": "Technology",
                    "company_name": "Apple Inc.",
                    "validation_errors": [],
                    "alternative_suggestions": [],
                }
            ],
            "market_sentiments": [{"ticker": "AAPL", "sentiment_score": 0.75, "sentiment_label": "Positive"}],
            "risk_assessments": [{"ticker": "AAPL", "risk_score": 5, "risk_factors": ["Market volatility", "Competition"]}],
            "sec_citations": [
                {
                    "ticker": "AAPL",
                    "filing_url": "https://sec.gov/filing/123",
                    "filed_at": datetime.now().isoformat(),
                    "section": "Item 1A",
                    "excerpt": "Risk factors include market competition",
                    "sec_citation": "10-K (2024), Item 1A, p. 17",
                    "extraction_timestamp": datetime.now().isoformat(),
                    "validation_status": {
                        "is_valid": True,
                        "validation_timestamp": datetime.now().isoformat(),
                        "validation_errors": [],
                        "validation_warnings": [],
                        "schema_version": 1,
                    },
                }
            ],
        }

    @pytest.fixture
    def sample_etf_output(self, sample_crew_metadata):
        """Sample ETF crew output for testing."""
        etf_metadata = sample_crew_metadata.copy()
        etf_metadata["crew_name"] = "etf"

        return {
            "metadata": etf_metadata,
            "validated_etfs": [
                {
                    "symbol": "SPY",
                    "is_valid": True,
                    "validation_source": "yahoo_finance",
                    "validation_timestamp": datetime.now().isoformat(),
                    "fund_name": "SPDR S&P 500 ETF Trust",
                    "issuer": "State Street",
                    "expense_ratio": 0.09,
                    "validation_errors": [],
                }
            ],
            "factsheets": [{"symbol": "SPY", "expense_ratio": 0.09, "aum": 400000000000}],
            "holdings_analysis": [{"symbol": "SPY", "top_holdings": ["AAPL", "MSFT", "GOOGL"]}],
            "risk_assessments": [{"symbol": "SPY", "risk_score": 4, "risk_factors": ["Market risk", "Tracking error"]}],
        }

    def test_should_initialize_validation_pipeline_successfully(self, mock_validation_manager, mock_logger):
        """Test ValidationPipeline initialization."""
        with patch("finwiz.integration.validation_pipeline.get_validation_manager", return_value=mock_validation_manager):
            pipeline = ValidationPipeline(
                output_dir=Path("/test/output"), validation_manager=mock_validation_manager, logger=mock_logger
            )

            assert pipeline.output_dir == Path("/test/output")
            assert pipeline.validation_manager == mock_validation_manager
            assert pipeline.logger == mock_logger
            assert "stock" in pipeline.crew_schema_mapping
            assert "etf" in pipeline.crew_schema_mapping
            assert "crypto" in pipeline.crew_schema_mapping
            assert "discovery" in pipeline.crew_schema_mapping

            # Should have been called twice: once for SECCitationValidator, once for ValidationPipeline
        assert mock_logger.info.call_count == 2

    def test_should_validate_single_crew_output_successfully_when_valid_data_provided(
        self, validation_pipeline, sample_stock_output
    ):
        """Test successful validation of single crew output."""
        result = validation_pipeline.validate_crew_output("stock", sample_stock_output)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.sanitized_data is not None
        assert "metadata" in result.sanitized_data
        assert "validated_tickers" in result.sanitized_data

    def test_should_fail_validation_when_invalid_crew_name_provided(self, validation_pipeline):
        """Test validation failure with invalid crew name."""
        result = validation_pipeline.validate_crew_output("invalid_crew", {"some": "data"})

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].error_type == "schema_not_found"
        assert "invalid_crew" in result.errors[0].message

    def test_should_fail_validation_when_missing_required_fields(self, validation_pipeline):
        """Test validation failure with missing required fields."""
        invalid_data = {
            "metadata": {
                "crew_name": "stock"
                # Missing required fields
            }
        }

        result = validation_pipeline.validate_crew_output("stock", invalid_data)

        assert result.is_valid is False
        assert len(result.errors) > 0
        # Should have errors for missing required fields
        error_types = [error.error_type for error in result.errors]
        assert "missing" in str(error_types).lower()

    def test_should_validate_crew_metadata_successfully_when_valid_metadata_provided(
        self, validation_pipeline, sample_crew_metadata
    ):
        """Test successful metadata validation."""
        result = validation_pipeline._validate_crew_metadata(sample_crew_metadata)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_should_fail_metadata_validation_when_metadata_missing(self, validation_pipeline):
        """Test metadata validation failure when metadata is missing."""
        result = validation_pipeline._validate_crew_metadata(None)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].error_type == "missing_field"
        assert "metadata" in result.errors[0].field_path

    def test_should_extract_validated_tickers_from_crew_outputs(self, validation_pipeline, sample_stock_output, sample_etf_output):
        """Test extraction of validated tickers from crew outputs."""
        crew_outputs = {"stock": sample_stock_output, "etf": sample_etf_output}

        all_tickers = validation_pipeline._extract_all_validated_tickers(crew_outputs)

        assert "stock" in all_tickers
        assert "etf" in all_tickers
        assert len(all_tickers["stock"]) == 1
        assert len(all_tickers["etf"]) == 1
        assert all_tickers["stock"][0]["symbol"] == "AAPL"
        assert all_tickers["etf"][0]["symbol"] == "SPY"

    def test_should_find_ticker_validation_conflicts_when_crews_disagree(self, validation_pipeline):
        """Test detection of ticker validation conflicts."""
        # Create conflicting ticker validations
        all_tickers = {
            "stock": [
                {
                    "symbol": "AAPL",
                    "is_valid": True,
                    "validation_source": "yahoo_finance",
                    "validation_timestamp": datetime.now().isoformat(),
                    "validation_errors": [],
                }
            ],
            "etf": [
                {
                    "symbol": "AAPL",  # Same ticker but different validation result
                    "is_valid": False,
                    "validation_source": "alpha_vantage",
                    "validation_timestamp": datetime.now().isoformat(),
                    "validation_errors": ["Ticker not found"],
                }
            ],
        }

        conflicts = validation_pipeline._find_ticker_validation_conflicts(all_tickers)

        assert len(conflicts) == 1
        assert conflicts[0]["ticker"] == "AAPL"
        assert conflicts[0]["conflict_type"] == "validation_disagreement"
        assert len(conflicts[0]["validations"]) == 2

    def test_should_validate_cross_crew_consistency_successfully_when_no_conflicts(
        self, validation_pipeline, sample_stock_output, sample_etf_output
    ):
        """Test successful cross-crew consistency validation."""
        crew_outputs = {"stock": sample_stock_output, "etf": sample_etf_output}

        result = validation_pipeline._validate_cross_crew_consistency(crew_outputs)

        assert result.is_consistent is True
        assert len(result.consistency_errors) == 0
        assert len(result.ticker_conflicts) == 0
        assert len(result.data_conflicts) == 0

    def test_should_detect_cross_crew_inconsistency_when_ticker_conflicts_exist(
        self, validation_pipeline, sample_stock_output, sample_etf_output
    ):
        """Test detection of cross-crew inconsistency with ticker conflicts."""
        # Modify ETF output to have conflicting ticker validation
        sample_etf_output["validated_etfs"][0]["symbol"] = "AAPL"  # Same as stock
        sample_etf_output["validated_etfs"][0]["is_valid"] = False  # Conflict

        crew_outputs = {"stock": sample_stock_output, "etf": sample_etf_output}

        result = validation_pipeline._validate_cross_crew_consistency(crew_outputs)

        assert result.is_consistent is False
        assert len(result.consistency_errors) > 0
        assert len(result.ticker_conflicts) > 0
        assert "AAPL" in result.consistency_errors[0]

    def test_should_check_metadata_consistency_and_find_issues(self, validation_pipeline):
        """Test metadata consistency checking."""
        crew_outputs = {
            "stock": {"metadata": {"schema_version": 1, "dependencies_met": True}},
            "etf": {
                "metadata": {
                    "schema_version": 2,  # Different version
                    "dependencies_met": False,  # Unmet dependencies
                }
            },
        }

        issues = validation_pipeline._check_metadata_consistency(crew_outputs)

        assert len(issues) == 2
        assert any("schema version mismatch" in issue.lower() for issue in issues)
        assert any("unmet dependencies" in issue.lower() for issue in issues)

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.stat")
    def test_should_load_crew_data_successfully_when_files_exist(
        self, mock_stat, mock_glob, mock_exists, mock_file, validation_pipeline, sample_stock_output
    ):
        """Test successful loading of crew data from files."""
        # Mock file system operations
        mock_exists.return_value = True
        mock_file_path = Mock()
        mock_file_path.stat.return_value.st_mtime = 1234567890
        mock_glob.return_value = [mock_file_path]
        mock_file.return_value.read.return_value = json.dumps(sample_stock_output)

        result = validation_pipeline._load_crew_data("stock")

        assert result is not None
        assert result == sample_stock_output
        mock_exists.assert_called_once()
        mock_glob.assert_called_once()

    @patch("pathlib.Path.exists")
    def test_should_return_none_when_crew_directory_does_not_exist(self, mock_exists, validation_pipeline):
        """Test loading crew data when directory doesn't exist."""
        mock_exists.return_value = False

        result = validation_pipeline._load_crew_data("nonexistent_crew")

        assert result is None
        mock_exists.assert_called_once()

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.glob")
    def test_should_return_none_when_no_output_files_found(self, mock_glob, mock_exists, validation_pipeline):
        """Test loading crew data when no output files exist."""
        mock_exists.return_value = True
        mock_glob.return_value = []  # No files found

        result = validation_pipeline._load_crew_data("stock")

        assert result is None
        mock_exists.assert_called_once()
        mock_glob.assert_called_once()

    @patch("finwiz.integration.validation_pipeline.ValidationPipeline._load_crew_data")
    def test_should_validate_all_crew_outputs_successfully_when_valid_data_available(
        self, mock_load_data, validation_pipeline, sample_stock_output, sample_etf_output
    ):
        """Test comprehensive validation of all crew outputs."""

        # Mock data loading
        def mock_load_side_effect(crew_name):
            if crew_name == "stock":
                return sample_stock_output
            elif crew_name == "etf":
                return sample_etf_output
            else:
                return None

        mock_load_data.side_effect = mock_load_side_effect

        result = validation_pipeline.validate_all_crew_outputs()

        assert isinstance(result, ValidationPipelineResult)
        assert result.overall_valid is True
        assert len(result.validated_crews) >= 2  # At least stock and etf
        assert len(result.failed_crews) <= 2  # crypto and discovery might fail (no data)
        assert result.total_errors == 0
        assert isinstance(result.cross_crew_validation, CrossCrewValidationResult)

    @patch("finwiz.integration.validation_pipeline.ValidationPipeline._load_crew_data")
    def test_should_handle_validation_errors_gracefully_when_crew_data_invalid(self, mock_load_data, validation_pipeline):
        """Test graceful handling of validation errors."""
        # Mock invalid data
        invalid_data = {"invalid": "data", "missing": "required_fields"}
        mock_load_data.return_value = invalid_data

        result = validation_pipeline.validate_all_crew_outputs()

        assert isinstance(result, ValidationPipelineResult)
        assert result.overall_valid is False
        assert result.total_errors > 0
        assert len(result.failed_crews) > 0

    @patch("finwiz.integration.validation_pipeline.ValidationPipeline._load_crew_data")
    def test_should_use_strict_mode_when_requested(self, mock_load_data, validation_pipeline, sample_stock_output):
        """Test validation pipeline with strict mode enabled."""
        mock_load_data.return_value = sample_stock_output

        result = validation_pipeline.validate_all_crew_outputs(strict_mode=True)

        # Verify strict mode was set
        validation_pipeline.validation_manager.set_strictness_mode.assert_called_with(ValidationMode.ERROR)
        assert isinstance(result, ValidationPipelineResult)

    def test_should_generate_comprehensive_validation_report(self, validation_pipeline, sample_stock_output):
        """Test generation of comprehensive validation report."""
        # Create a sample validation result
        validation_result = ValidationPipelineResult(
            overall_valid=True,
            validation_timestamp=datetime.now(),
            cross_crew_validation=CrossCrewValidationResult(is_consistent=True, validation_timestamp=datetime.now()),
        )

        # Add some sample schema validation results
        schema_result = BaseValidationResult(is_valid=True)
        validation_result.schema_validation_results["stock"] = schema_result

        report = validation_pipeline.generate_validation_report(validation_result)

        assert "validation_summary" in report
        assert "schema_validation" in report
        assert "cross_crew_validation" in report
        assert "integration_errors" in report

        assert report["validation_summary"]["overall_valid"] is True
        assert "stock" in report["schema_validation"]
        assert report["cross_crew_validation"]["is_consistent"] is True

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    def test_should_save_validation_report_to_file_when_path_provided(self, mock_mkdir, mock_file, validation_pipeline):
        """Test saving validation report to file."""
        validation_result = ValidationPipelineResult(
            overall_valid=True,
            validation_timestamp=datetime.now(),
            cross_crew_validation=CrossCrewValidationResult(is_consistent=True, validation_timestamp=datetime.now()),
        )

        output_path = Path("/test/report.json")
        report = validation_pipeline.generate_validation_report(validation_result, output_path)

        assert report is not None
        mock_mkdir.assert_called_once()
        mock_file.assert_called_once_with(output_path, "w", encoding="utf-8")

    def test_should_handle_exception_during_validation_gracefully(self, validation_pipeline, mock_logger):
        """Test graceful handling of exceptions during validation."""
        # Create invalid data that will cause an exception
        with patch.object(validation_pipeline, "_validate_crew_schema", side_effect=Exception("Test error")):
            result = validation_pipeline.validate_crew_output("stock", {"test": "data"})

            assert result.is_valid is False
            assert len(result.errors) == 1
            assert result.errors[0].error_type == "unexpected_error"
            assert "Test error" in result.errors[0].message

    def test_should_validate_cross_crew_consistency_with_empty_outputs(self, validation_pipeline):
        """Test cross-crew consistency validation with empty outputs."""
        result = validation_pipeline.validate_cross_crew_consistency({})

        assert isinstance(result, CrossCrewValidationResult)
        assert result.is_consistent is True
        assert len(result.consistency_errors) == 0
        assert len(result.ticker_conflicts) == 0

    def test_should_handle_malformed_ticker_data_gracefully(self, validation_pipeline):
        """Test handling of malformed ticker data in cross-crew validation."""
        crew_outputs = {
            "stock": {
                "validated_tickers": [
                    {"symbol": "AAPL", "is_valid": True},
                    {"invalid": "ticker_data"},  # Malformed data
                    {"symbol": "", "is_valid": False},  # Empty symbol
                ]
            }
        }

        # Should not raise exception
        result = validation_pipeline._validate_cross_crew_consistency(crew_outputs)

        assert isinstance(result, CrossCrewValidationResult)
        # Should still process valid ticker data
        assert result.is_consistent is True


class TestValidationPipelineIntegration:
    """Integration tests for ValidationPipeline with mocked dependencies."""

    @pytest.fixture
    def mock_file_system(self):
        """Mock file system for integration tests."""
        with (
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.glob") as mock_glob,
            patch("builtins.open", new_callable=mock_open) as mock_file,
        ):
            # Configure mocks
            mock_exists.return_value = True
            mock_file_path = Mock()
            mock_file_path.stat.return_value.st_mtime = 1234567890
            mock_glob.return_value = [mock_file_path]

            yield {"exists": mock_exists, "glob": mock_glob, "open": mock_file}

    def test_should_perform_end_to_end_validation_with_mocked_file_system(
        self, mock_file_system, sample_stock_output, sample_etf_output
    ):
        """Test end-to-end validation pipeline with mocked file system."""

        # Configure mock file system to return sample data
        def mock_read_side_effect(*args, **kwargs):
            if "stock" in str(args):
                return json.dumps(sample_stock_output)
            elif "etf" in str(args):
                return json.dumps(sample_etf_output)
            else:
                return "{}"

        mock_file_system["open"].return_value.read.side_effect = mock_read_side_effect

        # Create pipeline and run validation
        with patch("finwiz.integration.validation_pipeline.get_validation_manager"):
            pipeline = ValidationPipeline(output_dir=Path("/mock/output"))
            result = pipeline.validate_all_crew_outputs()

        # Verify results
        assert isinstance(result, ValidationPipelineResult)
        assert result.validation_timestamp is not None
        assert isinstance(result.cross_crew_validation, CrossCrewValidationResult)

    def test_should_handle_missing_crew_data_gracefully_in_full_validation(self, mock_file_system):
        """Test full validation pipeline with missing crew data."""
        # Configure mock to simulate missing data
        mock_file_system["exists"].return_value = False

        with patch("finwiz.integration.validation_pipeline.get_validation_manager"):
            pipeline = ValidationPipeline(output_dir=Path("/mock/output"))
            result = pipeline.validate_all_crew_outputs()

        # Should handle missing data gracefully
        assert isinstance(result, ValidationPipelineResult)
        assert len(result.failed_crews) > 0  # All crews should fail due to missing data
        assert result.overall_valid is False
