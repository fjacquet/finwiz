"""
Unit tests for A+ Discovery Accessor.

Tests the APlusDiscoveryAccessor class for checking discovery results,
loading discovery data, and generating human-readable summaries.
"""

import json
from pathlib import Path

import pytest

from finwiz.orchestrators.discovery.aplus_discovery_accessor import APlusDiscoveryAccessor


class TestAPlusDiscoveryAccessor:
    """Test suite for APlusDiscoveryAccessor."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return output_dir

    @pytest.fixture
    def discovery_dir(self, output_dir):
        """Create discovery directory."""
        discovery_dir = output_dir / "discovery"
        discovery_dir.mkdir()
        return discovery_dir

    @pytest.fixture
    def accessor(self, output_dir):
        """Create accessor instance for testing."""
        return APlusDiscoveryAccessor(output_dir=output_dir)

    @pytest.fixture
    def sample_stock_discovery(self, discovery_dir):
        """Create sample stock discovery file."""
        data = {
            "opportunities": [
                {
                    "ticker": "AAPL",
                    "name": "Apple Inc.",
                    "grade": "A+",
                    "composite_score": 0.95,
                    "recommendation": "BUY",
                    "rationale": "Strong fundamentals",
                },
                {
                    "ticker": "MSFT",
                    "name": "Microsoft Corp.",
                    "grade": "A",
                    "composite_score": 0.88,
                    "recommendation": "BUY",
                    "rationale": "Good performance",
                },
            ]
        }
        file_path = discovery_dir / "a_plus_stocks.json"
        file_path.write_text(json.dumps(data), encoding="utf-8")
        return file_path

    @pytest.fixture
    def sample_etf_discovery(self, discovery_dir):
        """Create sample ETF discovery file."""
        data = {
            "opportunities": [
                {
                    "ticker": "SPY",
                    "name": "S&P 500 ETF",
                    "grade": "A+",
                    "composite_score": 0.92,
                    "recommendation": "BUY",
                    "rationale": "Low cost, broad diversification",
                }
            ]
        }
        file_path = discovery_dir / "a_plus_etfs.json"
        file_path.write_text(json.dumps(data), encoding="utf-8")
        return file_path

    @pytest.fixture
    def sample_crypto_discovery(self, discovery_dir):
        """Create sample crypto discovery file."""
        data = {"opportunities": []}
        file_path = discovery_dir / "a_plus_crypto.json"
        file_path.write_text(json.dumps(data), encoding="utf-8")
        return file_path

    def test_should_initialize_accessor(self, accessor, output_dir):
        """Test accessor initialization."""
        # Assert
        assert accessor.output_dir == output_dir
        assert accessor.discovery_dir == output_dir / "discovery"

    def test_should_return_false_when_discovery_dir_missing(self, accessor):
        """Test has_discovery_results returns False when directory missing."""
        # Act
        result = accessor.has_discovery_results()

        # Assert
        assert result is False

    def test_should_return_false_when_no_discovery_files(self, accessor, discovery_dir):
        """Test has_discovery_results returns False when no files exist."""
        # Act
        result = accessor.has_discovery_results()

        # Assert
        assert result is False

    def test_should_return_true_when_stock_discovery_exists(self, accessor, sample_stock_discovery):
        """Test has_discovery_results returns True when stock file exists."""
        # Act
        result = accessor.has_discovery_results()

        # Assert
        assert result is True

    def test_should_return_true_when_etf_discovery_exists(self, accessor, sample_etf_discovery):
        """Test has_discovery_results returns True when ETF file exists."""
        # Act
        result = accessor.has_discovery_results()

        # Assert
        assert result is True

    def test_should_return_true_when_crypto_discovery_exists(self, accessor, sample_crypto_discovery):
        """Test has_discovery_results returns True when crypto file exists."""
        # Act
        result = accessor.has_discovery_results()

        # Assert
        assert result is True

    def test_should_return_true_when_any_discovery_file_exists(self, accessor, sample_stock_discovery, sample_etf_discovery):
        """Test has_discovery_results returns True when any file exists."""
        # Act
        result = accessor.has_discovery_results()

        # Assert
        assert result is True

    def test_should_load_stock_discovery_results(self, accessor, sample_stock_discovery):
        """Test loading stock discovery results."""
        # Act
        results = accessor.load_discovery_results()

        # Assert
        assert results is not None
        assert "stocks" in results
        assert len(results["stocks"]["opportunities"]) == 2
        assert results["stocks"]["opportunities"][0]["ticker"] == "AAPL"

    def test_should_load_etf_discovery_results(self, accessor, sample_etf_discovery):
        """Test loading ETF discovery results."""
        # Act
        results = accessor.load_discovery_results()

        # Assert
        assert results is not None
        assert "etfs" in results
        assert len(results["etfs"]["opportunities"]) == 1
        assert results["etfs"]["opportunities"][0]["ticker"] == "SPY"

    def test_should_load_crypto_discovery_results(self, accessor, sample_crypto_discovery):
        """Test loading crypto discovery results."""
        # Act
        results = accessor.load_discovery_results()

        # Assert
        assert results is not None
        assert "crypto" in results
        assert len(results["crypto"]["opportunities"]) == 0

    def test_should_load_all_discovery_results(
        self,
        accessor,
        sample_stock_discovery,
        sample_etf_discovery,
        sample_crypto_discovery,
    ):
        """Test loading all discovery results."""
        # Act
        results = accessor.load_discovery_results()

        # Assert
        assert results is not None
        assert "stocks" in results
        assert "etfs" in results
        assert "crypto" in results
        assert results["total_opportunities"] == 3  # 2 stocks + 1 ETF + 0 crypto

    def test_should_return_none_when_no_discovery_results(self, accessor):
        """Test load_discovery_results returns None when no results available."""
        # Act
        results = accessor.load_discovery_results()

        # Assert
        assert results is None

    def test_should_include_loaded_timestamp(self, accessor, sample_stock_discovery):
        """Test that loaded_at timestamp is included."""
        # Act
        results = accessor.load_discovery_results()

        # Assert
        assert results is not None
        assert "loaded_at" in results
        # Verify it's a valid ISO format timestamp
        assert isinstance(results["loaded_at"], str)
        assert "T" in results["loaded_at"]  # ISO format includes T separator

    def test_should_calculate_total_opportunities(
        self,
        accessor,
        sample_stock_discovery,
        sample_etf_discovery,
        sample_crypto_discovery,
    ):
        """Test calculation of total opportunities."""
        # Act
        results = accessor.load_discovery_results()

        # Assert
        assert results is not None
        assert results["total_opportunities"] == 3

    def test_should_generate_summary_when_no_results(self, accessor):
        """Test summary generation when no results available."""
        # Act
        summary = accessor.get_opportunities_summary()

        # Assert
        assert "no output" in summary.lower()

    def test_should_generate_summary_when_no_opportunities(self, accessor, sample_crypto_discovery):
        """Test summary generation when no opportunities found."""
        # Act
        summary = accessor.get_opportunities_summary()

        # Assert
        assert "no a+ opportunities found" in summary.lower()

    def test_should_generate_summary_with_stock_opportunities(self, accessor, sample_stock_discovery):
        """Test summary generation with stock opportunities."""
        # Act
        summary = accessor.get_opportunities_summary()

        # Assert
        assert "2 stock opportunities" in summary.lower()
        assert "1 a+ grade" in summary.lower()

    def test_should_generate_summary_with_etf_opportunities(self, accessor, sample_etf_discovery):
        """Test summary generation with ETF opportunities."""
        # Act
        summary = accessor.get_opportunities_summary()

        # Assert
        assert "1 etf" in summary.lower()
        assert "1 a+ grade" in summary.lower()

    def test_should_generate_summary_with_all_opportunities(
        self,
        accessor,
        sample_stock_discovery,
        sample_etf_discovery,
        sample_crypto_discovery,
    ):
        """Test summary generation with all opportunity types."""
        # Act
        summary = accessor.get_opportunities_summary()

        # Assert
        assert "3 high-quality investment opportunities" in summary.lower()
        assert "stock" in summary.lower()
        assert "etf" in summary.lower()

    def test_should_count_a_plus_grades_separately(self, accessor, sample_stock_discovery):
        """Test that A+ grades are counted separately from other grades."""
        # Act
        summary = accessor.get_opportunities_summary()

        # Assert
        # 2 total candidates, but only 1 is A+ (AAPL)
        assert "2 stock opportunities" in summary.lower()
        assert "1 a+ grade" in summary.lower()

    def test_should_handle_missing_stock_file(self, accessor, discovery_dir):
        """Test handling when stock file is missing."""
        # Arrange - only create ETF file
        data = {"opportunities": []}
        etf_file = discovery_dir / "a_plus_etfs.json"
        etf_file.write_text(json.dumps(data), encoding="utf-8")

        # Act
        results = accessor.load_discovery_results()

        # Assert
        assert results is not None
        assert results["stocks"] == {}
        assert "etfs" in results

    def test_should_handle_missing_etf_file(self, accessor, discovery_dir):
        """Test handling when ETF file is missing."""
        # Arrange - only create stock file
        data = {"opportunities": []}
        stock_file = discovery_dir / "a_plus_stocks.json"
        stock_file.write_text(json.dumps(data), encoding="utf-8")

        # Act
        results = accessor.load_discovery_results()

        # Assert
        assert results is not None
        assert "stocks" in results
        assert results["etfs"] == {}

    def test_should_handle_missing_crypto_file(self, accessor, discovery_dir):
        """Test handling when crypto file is missing."""
        # Arrange - only create stock file
        data = {"opportunities": []}
        stock_file = discovery_dir / "a_plus_stocks.json"
        stock_file.write_text(json.dumps(data), encoding="utf-8")

        # Act
        results = accessor.load_discovery_results()

        # Assert
        assert results is not None
        assert "stocks" in results
        assert results["crypto"] == {}

    def test_should_handle_invalid_json(self, accessor, discovery_dir):
        """Test handling of invalid JSON in discovery file."""
        # Arrange
        stock_file = discovery_dir / "a_plus_stocks.json"
        stock_file.write_text("invalid json", encoding="utf-8")

        # Act
        results = accessor.load_discovery_results()

        # Assert
        assert results is not None
        assert results["stocks"] == {}

    def test_should_handle_file_read_error(self, accessor, discovery_dir, mocker):
        """Test handling of file read errors."""
        # Arrange
        stock_file = discovery_dir / "a_plus_stocks.json"
        stock_file.write_text('{"opportunities": []}', encoding="utf-8")

        # Mock read_text to raise an exception
        mocker.patch.object(Path, "read_text", side_effect=Exception("Read error"))

        # Act
        results = accessor.load_discovery_results()

        # Assert
        assert results is not None
        assert results["stocks"] == {}

    def test_should_handle_summary_generation_error(self, accessor, mocker):
        """Test handling of errors during summary generation."""
        # Arrange
        mocker.patch.object(accessor, "load_discovery_results", side_effect=Exception("Load error"))

        # Act
        summary = accessor.get_opportunities_summary()

        # Assert
        assert "error" in summary.lower()

    def test_should_handle_exception_in_has_discovery_results(self, accessor, tmp_path, mocker):
        """Test exception handling in has_discovery_results."""
        # Arrange - Create accessor with invalid path that will cause issues
        invalid_accessor = APlusDiscoveryAccessor(output_dir=tmp_path / "nonexistent")

        # Mock the exists method to raise an exception
        mock_exists = mocker.patch.object(Path, "exists", side_effect=Exception("Check error"))

        # Act
        result = invalid_accessor.has_discovery_results()

        # Assert
        assert result is False

    def test_should_handle_empty_candidates_list(self, accessor, discovery_dir):
        """Test handling of empty candidates list."""
        # Arrange
        data = {"opportunities": []}
        stock_file = discovery_dir / "a_plus_stocks.json"
        stock_file.write_text(json.dumps(data), encoding="utf-8")

        # Act
        results = accessor.load_discovery_results()

        # Assert
        assert results is not None
        assert results["total_opportunities"] == 0

    def test_should_handle_missing_grade_field(self, accessor, discovery_dir):
        """Test handling when grade field is missing."""
        # Arrange
        data = {
            "opportunities": [
                {
                    "ticker": "AAPL",
                    "name": "Apple Inc.",
                    # Missing grade field
                    "composite_score": 0.95,
                    "recommendation": "BUY",
                    "rationale": "Strong fundamentals",
                }
            ]
        }
        stock_file = discovery_dir / "a_plus_stocks.json"
        stock_file.write_text(json.dumps(data), encoding="utf-8")

        # Act
        summary = accessor.get_opportunities_summary()

        # Assert
        # Should still count the opportunity, just not as A+
        assert "1 stock" in summary.lower()
        assert "0 a+ grade" in summary.lower()
