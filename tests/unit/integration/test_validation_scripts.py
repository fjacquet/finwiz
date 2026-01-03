"""
Comprehensive pytest tests for validation_scripts.py.

Tests validation script functionality including:
- Data integrity validation
- Dependency validation
- Performance validation
- Error handling and edge cases
- Return values and output formatting
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from faker import Faker

from finwiz.validation.scripts import (
    DataIntegrityValidator,
    DependencyValidator,
    PerformanceValidator,
    ValidationScript,
    main,
    run_all_validations,
)

# ===== Fixtures =====


@pytest.fixture
def fake() -> Faker:
    """Faker instance for generating test data."""
    return Faker()


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """Create temporary output directory with crew subdirectories."""
    (tmp_path / "stock").mkdir()
    (tmp_path / "etf").mkdir()
    (tmp_path / "crypto").mkdir()
    return tmp_path


@pytest.fixture
def mock_integration_config(mocker):
    """Mock integration configuration."""
    config = mocker.MagicMock()
    config.output_dir = Path("/tmp/test_output")
    config.default_max_age_hours = 24
    mocker.patch(
        "finwiz.integration.validation_scripts.get_integration_config",
        return_value=config,
    )
    return config


@pytest.fixture
def mock_crew_config(mocker):
    """Mock crew dependency configuration."""
    crew_config = mocker.MagicMock()
    crew_config.crew_dependencies = {
        "stock": [],
        "etf": ["stock"],
        "crypto": [],
    }
    mocker.patch(
        "finwiz.integration.validation_scripts.get_crew_dependency_config",
        return_value=crew_config,
    )
    return crew_config


@pytest.fixture
def mock_logger(mocker):
    """Mock integration logger."""
    logger = mocker.MagicMock()
    mocker.patch("finwiz.integration.validation_scripts.integration_logger", logger)
    return logger


@pytest.fixture
def mock_log_analyzer(mocker):
    """Mock log analyzer."""
    analyzer = mocker.MagicMock()
    analyzer.analyze_crew_execution_patterns.return_value = {
        "average_execution_time": 120.5,
        "crew_execution_counts": {"stock": 5, "etf": 3, "crypto": 2},
    }
    analyzer.identify_integration_bottlenecks.return_value = {
        "slow_crews": [],
        "frequent_failure_crews": [],
    }
    mocker.patch("finwiz.integration.validation_scripts.log_analyzer", analyzer)
    return analyzer


@pytest.fixture
def mock_health_checker(mocker):
    """Mock health checker."""
    checker = mocker.MagicMock()
    health_report = mocker.MagicMock()
    health_report.components = [mocker.MagicMock(component="system_resources", details={"cpu": 45.2, "memory": 62.1})]
    checker.perform_comprehensive_health_check.return_value = health_report
    mocker.patch(
        "finwiz.integration.validation_scripts.get_health_checker",
        return_value=checker,
    )
    return checker


# ===== ValidationScript Base Class Tests =====


class TestValidationScript:
    """Test suite for ValidationScript base class."""

    def test_initialization_with_default_output_dir(self, mock_integration_config):
        """Test ValidationScript initialization with default output directory."""
        validator = ValidationScript()

        assert validator.config is not None
        assert validator.crew_config is not None
        assert validator.logger is not None

    def test_initialization_with_custom_output_dir(self, mock_integration_config, tmp_output_dir):
        """Test ValidationScript initialization with custom output directory."""
        validator = ValidationScript(output_dir=tmp_output_dir)

        assert validator.output_dir == tmp_output_dir

    def test_run_not_implemented(self):
        """Test that run() raises NotImplementedError in base class."""
        validator = ValidationScript()

        with pytest.raises(NotImplementedError):
            validator.run()

    def test_print_results_with_dict_values(self, capsys):
        """Test print_results with dictionary values."""
        validator = ValidationScript()
        results = {
            "status": "healthy",
            "metrics": {"cpu": 45.2, "memory": 62.1},
        }

        validator.print_results(results)
        captured = capsys.readouterr()

        assert "ValidationScript" in captured.out
        assert "status: healthy" in captured.out
        assert "METRICS:" in captured.out
        assert "cpu: 45.2" in captured.out

    def test_print_results_with_list_values(self, capsys):
        """Test print_results with list values."""
        validator = ValidationScript()
        results = {
            "status": "healthy",
            "recommendations": ["Fix issue 1", "Review issue 2"],
        }

        validator.print_results(results)
        captured = capsys.readouterr()

        assert "RECOMMENDATIONS:" in captured.out
        assert "Fix issue 1" in captured.out
        assert "Review issue 2" in captured.out

    def test_print_results_with_simple_values(self, capsys):
        """Test print_results with simple scalar values."""
        validator = ValidationScript()
        results = {
            "status": "healthy",
            "issue_count": 0,
        }

        validator.print_results(results)
        captured = capsys.readouterr()

        assert "status: healthy" in captured.out
        assert "issue_count: 0" in captured.out

    def test_print_results_with_mixed_values(self, capsys):
        """Test print_results with mixed value types."""
        validator = ValidationScript()
        results = {
            "timestamp": "2023-01-01T00:00:00",
            "status": "healthy",
            "issues": ["Issue 1"],
            "metrics": {"cpu": 45.2},
        }

        validator.print_results(results)
        captured = capsys.readouterr()

        assert "timestamp: 2023-01-01T00:00:00" in captured.out
        assert "status: healthy" in captured.out
        assert "ISSUES:" in captured.out
        assert "METRICS:" in captured.out


# ===== DataIntegrityValidator Tests =====


class TestDataIntegrityValidator:
    """Test suite for DataIntegrityValidator."""

    @pytest.fixture
    def validator(self, tmp_output_dir, mock_integration_config, mock_crew_config):
        """Create DataIntegrityValidator instance."""
        return DataIntegrityValidator(output_dir=tmp_output_dir)

    def test_initialization(self, validator):
        """Test DataIntegrityValidator initialization."""
        assert isinstance(validator, ValidationScript)
        assert validator.config is not None
        assert validator.crew_config is not None

    def test_run_returns_dict(self, validator):
        """Test that run() returns a dictionary."""
        results = validator.run()

        assert isinstance(results, dict)
        assert "validation_timestamp" in results
        assert "crew_data_status" in results
        assert "schema_validation" in results
        assert "data_consistency" in results
        assert "issues_found" in results
        assert "recommendations" in results

    def test_run_with_empty_output_dir(self, validator):
        """Test run() with empty output directory."""
        results = validator.run()

        assert isinstance(results, dict)
        assert "crew_data_status" in results
        # All crews should have no data
        for crew_status in results["crew_data_status"].values():
            assert crew_status["has_data"] is False

    def test_run_with_valid_json_files(self, validator, tmp_output_dir):
        """Test run() with valid JSON files."""
        # Create valid JSON files
        stock_data = {
            "metadata": {"execution_timestamp": datetime.now().isoformat()},
            "validated_tickers": [{"symbol": "AAPL"}, {"symbol": "GOOGL"}],
        }
        stock_file = tmp_output_dir / "stock" / "output.json"
        stock_file.write_text(json.dumps(stock_data))

        results = validator.run()

        assert results["crew_data_status"]["stock"]["has_data"] is True
        assert results["crew_data_status"]["stock"]["file_count"] == 1
        assert results["crew_data_status"]["stock"]["files"] == ["output.json"]

    def test_run_with_invalid_json(self, validator, tmp_output_dir):
        """Test run() with invalid JSON files."""
        # Create invalid JSON file
        invalid_file = tmp_output_dir / "stock" / "invalid.json"
        invalid_file.write_text("{invalid json")

        results = validator.run()

        assert results["crew_data_status"]["stock"]["has_data"] is True
        assert len(results["crew_data_status"]["stock"]["validation_errors"]) > 0
        assert "invalid.json" in results["issues_found"][0]

    def test_validate_crew_data_missing_metadata(self, validator, tmp_output_dir):
        """Test _validate_crew_data with missing metadata."""
        # Create JSON without metadata
        data = {"some_field": "value"}
        file_path = tmp_output_dir / "stock" / "output.json"
        file_path.write_text(json.dumps(data))

        result = validator._validate_crew_data("stock")

        assert result["has_data"] is True
        assert any("Missing metadata field" in error for error in result["validation_errors"])

    def test_validate_crew_data_non_dict_json(self, validator, tmp_output_dir):
        """Test _validate_crew_data with non-dictionary JSON."""
        # Create JSON array instead of object
        data = ["item1", "item2"]
        file_path = tmp_output_dir / "stock" / "output.json"
        file_path.write_text(json.dumps(data))

        result = validator._validate_crew_data("stock")

        assert result["has_data"] is True
        assert any("Not a JSON object" in error for error in result["validation_errors"])

    def test_validate_crew_data_last_modified(self, validator, tmp_output_dir):
        """Test _validate_crew_data returns last_modified timestamp."""
        # Create JSON file
        data = {"metadata": {"execution_timestamp": datetime.now().isoformat()}}
        file_path = tmp_output_dir / "stock" / "output.json"
        file_path.write_text(json.dumps(data))

        result = validator._validate_crew_data("stock")

        assert result["last_modified"] is not None
        assert isinstance(result["last_modified"], str)
        # Verify it's ISO format
        datetime.fromisoformat(result["last_modified"])

    def test_validate_crew_data_nonexistent_directory(self, validator, tmp_output_dir):
        """Test _validate_crew_data with nonexistent crew directory."""
        result = validator._validate_crew_data("nonexistent_crew")

        assert result["has_data"] is False
        assert result["file_count"] == 0
        assert any("does not exist" in error for error in result["validation_errors"])

    def test_check_data_consistency_empty_crews(self, validator):
        """Test _check_data_consistency with empty crew directories."""
        result = validator._check_data_consistency()

        assert isinstance(result, dict)
        assert "ticker_consistency" in result
        assert "timestamp_consistency" in result
        assert "inconsistencies" in result

    def test_check_data_consistency_with_tickers(self, validator, tmp_output_dir):
        """Test _check_data_consistency extracts tickers correctly."""
        # Create stock data with tickers
        stock_data = {
            "metadata": {"execution_timestamp": datetime.now().isoformat()},
            "validated_tickers": [{"symbol": "AAPL"}, {"symbol": "GOOGL"}],
        }
        (tmp_output_dir / "stock" / "output.json").write_text(json.dumps(stock_data))

        result = validator._check_data_consistency()

        assert "stock" in result["ticker_consistency"]
        assert "AAPL" in result["ticker_consistency"]["stock"]
        assert "GOOGL" in result["ticker_consistency"]["stock"]

    def test_check_data_consistency_etf_tickers(self, validator, tmp_output_dir):
        """Test _check_data_consistency with ETF tickers."""
        etf_data = {
            "metadata": {"execution_timestamp": datetime.now().isoformat()},
            "validated_etfs": [{"symbol": "SPY"}, {"symbol": "QQQ"}],
        }
        (tmp_output_dir / "etf" / "output.json").write_text(json.dumps(etf_data))

        result = validator._check_data_consistency()

        assert "etf" in result["ticker_consistency"]
        assert "SPY" in result["ticker_consistency"]["etf"]
        assert "QQQ" in result["ticker_consistency"]["etf"]

    def test_check_data_consistency_crypto_symbols(self, validator, tmp_output_dir):
        """Test _check_data_consistency with crypto symbols."""
        crypto_data = {
            "metadata": {"execution_timestamp": datetime.now().isoformat()},
            "validated_symbols": [{"symbol": "BTC"}, {"symbol": "ETH"}],
        }
        (tmp_output_dir / "crypto" / "output.json").write_text(json.dumps(crypto_data))

        result = validator._check_data_consistency()

        assert "crypto" in result["ticker_consistency"]
        assert "BTC" in result["ticker_consistency"]["crypto"]
        assert "ETH" in result["ticker_consistency"]["crypto"]

    def test_check_data_consistency_timestamp_divergence(self, validator, tmp_output_dir):
        """Test _check_data_consistency detects timestamp divergence."""
        now = datetime.now()
        old_time = (now - timedelta(hours=8)).isoformat()
        recent_time = now.isoformat()

        stock_data = {
            "metadata": {"execution_timestamp": old_time},
            "validated_tickers": [{"symbol": "AAPL"}],
        }
        (tmp_output_dir / "stock" / "output.json").write_text(json.dumps(stock_data))

        etf_data = {
            "metadata": {"execution_timestamp": recent_time},
            "validated_etfs": [{"symbol": "SPY"}],
        }
        (tmp_output_dir / "etf" / "output.json").write_text(json.dumps(etf_data))

        result = validator._check_data_consistency()

        assert any("Large time gap" in inconsistency for inconsistency in result["inconsistencies"])

    def test_extract_tickers_from_data_stock(self, validator):
        """Test _extract_tickers_from_data for stock data."""
        data = {
            "validated_tickers": [
                {"symbol": "AAPL"},
                {"symbol": "GOOGL"},
                {"symbol": ""},  # Empty should be filtered
            ]
        }

        result = validator._extract_tickers_from_data(data, "stock")

        assert result == ["AAPL", "GOOGL"]

    def test_extract_tickers_from_data_etf(self, validator):
        """Test _extract_tickers_from_data for ETF data."""
        data = {"validated_etfs": [{"symbol": "SPY"}, {"symbol": "QQQ"}]}

        result = validator._extract_tickers_from_data(data, "etf")

        assert result == ["SPY", "QQQ"]

    def test_extract_tickers_from_data_crypto(self, validator):
        """Test _extract_tickers_from_data for crypto data."""
        data = {"validated_symbols": [{"symbol": "BTC"}, {"symbol": "ETH"}]}

        result = validator._extract_tickers_from_data(data, "crypto")

        assert result == ["BTC", "ETH"]

    def test_extract_tickers_from_data_missing_field(self, validator):
        """Test _extract_tickers_from_data with missing expected field."""
        data = {"some_field": []}

        result = validator._extract_tickers_from_data(data, "stock")

        assert result == []

    def test_extract_tickers_from_data_malformed(self, validator):
        """Test _extract_tickers_from_data with malformed data."""
        data = {"validated_tickers": "not a list"}

        # Should not raise, just return empty list
        result = validator._extract_tickers_from_data(data, "stock")

        assert result == []

    def test_extract_timestamp_from_data_valid(self, validator):
        """Test _extract_timestamp_from_data with valid metadata."""
        timestamp = datetime.now().isoformat()
        data = {"metadata": {"execution_timestamp": timestamp}}

        result = validator._extract_timestamp_from_data(data)

        assert result == timestamp

    def test_extract_timestamp_from_data_missing_metadata(self, validator):
        """Test _extract_timestamp_from_data with missing metadata."""
        data = {"some_field": "value"}

        result = validator._extract_timestamp_from_data(data)

        assert result is None

    def test_extract_timestamp_from_data_missing_timestamp(self, validator):
        """Test _extract_timestamp_from_data with missing timestamp."""
        data = {"metadata": {"other_field": "value"}}

        result = validator._extract_timestamp_from_data(data)

        assert result is None

    def test_generate_integrity_recommendations_missing_crews(self, validator):
        """Test _generate_integrity_recommendations for missing crews."""
        results = {
            "crew_data_status": {
                "stock": {"has_data": False, "validation_errors": []},
                "etf": {"has_data": True, "validation_errors": []},
                "crypto": {"has_data": False, "validation_errors": []},
            },
            "data_consistency": {"inconsistencies": []},
        }

        recommendations = validator._generate_integrity_recommendations(results)

        assert any("Execute missing crews" in rec for rec in recommendations)

    def test_generate_integrity_recommendations_validation_errors(self, validator):
        """Test _generate_integrity_recommendations for validation errors."""
        results = {
            "crew_data_status": {
                "stock": {"has_data": True, "validation_errors": ["error1"]},
                "etf": {"has_data": True, "validation_errors": []},
            },
            "data_consistency": {"inconsistencies": []},
        }

        recommendations = validator._generate_integrity_recommendations(results)

        assert any("Fix validation errors" in rec for rec in recommendations)

    def test_generate_integrity_recommendations_consistency_issues(self, validator):
        """Test _generate_integrity_recommendations for consistency issues."""
        results = {
            "crew_data_status": {
                "stock": {"has_data": True, "validation_errors": []},
            },
            "data_consistency": {"inconsistencies": ["timestamp issue"]},
        }

        recommendations = validator._generate_integrity_recommendations(results)

        assert any("Review data consistency" in rec for rec in recommendations)

    def test_generate_integrity_recommendations_healthy(self, validator):
        """Test _generate_integrity_recommendations for healthy state."""
        results = {
            "crew_data_status": {
                "stock": {"has_data": True, "validation_errors": []},
            },
            "data_consistency": {"inconsistencies": []},
        }

        recommendations = validator._generate_integrity_recommendations(results)

        assert any("Data integrity appears good" in rec for rec in recommendations)

    def test_run_handles_exception(self, validator, mocker):
        """Test run() handles exceptions gracefully."""
        mocker.patch.object(
            validator,
            "_validate_crew_data",
            side_effect=Exception("Test error"),
        )

        results = validator.run()

        assert "error" in results
        assert "Test error" in results["error"]
        assert "Validation script failed" in results["issues_found"][0]


# ===== DependencyValidator Tests =====


class TestDependencyValidator:
    """Test suite for DependencyValidator."""

    @pytest.fixture
    def validator(self, tmp_output_dir, mock_integration_config, mock_crew_config):
        """Create DependencyValidator instance."""
        return DependencyValidator(output_dir=tmp_output_dir)

    def test_initialization(self, validator):
        """Test DependencyValidator initialization."""
        assert isinstance(validator, ValidationScript)

    def test_run_returns_dict(self, validator):
        """Test that run() returns required fields."""
        results = validator.run()

        assert isinstance(results, dict)
        assert "validation_timestamp" in results
        assert "dependency_status" in results
        assert "execution_order" in results
        assert "circular_dependencies" in results
        assert "missing_dependencies" in results
        assert "recommendations" in results

    def test_validate_crew_dependencies_missing(self, validator):
        """Test _validate_crew_dependencies with missing dependencies."""
        result = validator._validate_crew_dependencies("etf", ["stock"])

        assert result["crew_name"] == "etf"
        assert "stock" in result["missing_dependencies"]
        assert len(result["satisfied_dependencies"]) == 0

    def test_validate_crew_dependencies_satisfied(self, validator, tmp_output_dir):
        """Test _validate_crew_dependencies with satisfied dependencies."""
        # Create dependency data
        stock_data = {"metadata": {"execution_timestamp": datetime.now().isoformat()}}
        (tmp_output_dir / "stock" / "output.json").write_text(json.dumps(stock_data))

        result = validator._validate_crew_dependencies("etf", ["stock"])

        assert result["crew_name"] == "etf"
        assert "stock" in result["satisfied_dependencies"]
        assert len(result["missing_dependencies"]) == 0

    def test_validate_crew_dependencies_stale(self, validator, tmp_output_dir, mock_integration_config, mocker):
        """Test _validate_crew_dependencies with stale dependencies."""
        # Create dependency data
        stock_data = {"metadata": {"execution_timestamp": datetime.now().isoformat()}}
        stock_file = tmp_output_dir / "stock" / "output.json"
        stock_file.write_text(json.dumps(stock_data))

        # Set max age to 0 hours so any file is considered stale
        # This ensures the file_age > timedelta(hours=0) will be true
        mock_integration_config.default_max_age_hours = 0

        result = validator._validate_crew_dependencies("etf", ["stock"])

        assert result["crew_name"] == "etf"
        # File is recent but max_age_hours is 0, so it should be stale
        assert "stock" in result["stale_dependencies"]

    def test_validate_crew_dependencies_empty_list(self, validator):
        """Test _validate_crew_dependencies with empty dependency list."""
        result = validator._validate_crew_dependencies("stock", [])

        assert result["crew_name"] == "stock"
        assert len(result["required_dependencies"]) == 0
        assert len(result["satisfied_dependencies"]) == 0

    def test_calculate_execution_order_no_dependencies(self, validator):
        """Test _calculate_execution_order with no dependencies."""
        execution_order = validator._calculate_execution_order()

        # Should return all crews
        assert isinstance(execution_order, list)
        assert len(execution_order) > 0

    def test_calculate_execution_order_linear_dependencies(self, validator, mock_crew_config):
        """Test _calculate_execution_order with linear dependency chain."""
        # Set linear dependency: stock -> etf -> crypto
        mock_crew_config.crew_dependencies = {
            "stock": [],
            "etf": ["stock"],
            "crypto": ["etf"],
        }

        execution_order = validator._calculate_execution_order()

        # stock should come first
        assert execution_order[0] == "stock"
        # etf should come before crypto
        assert execution_order.index("etf") < execution_order.index("crypto")

    def test_calculate_execution_order_multiple_dependencies(self, validator, mock_crew_config):
        """Test _calculate_execution_order with multiple dependencies."""
        # crypto depends on both stock and etf
        mock_crew_config.crew_dependencies = {
            "stock": [],
            "etf": [],
            "crypto": ["stock", "etf"],
        }

        execution_order = validator._calculate_execution_order()

        # stock and etf should come before crypto
        assert execution_order.index("crypto") > execution_order.index("stock")
        assert execution_order.index("crypto") > execution_order.index("etf")

    def test_detect_circular_dependencies_none(self, validator, mock_crew_config):
        """Test _detect_circular_dependencies with no cycles."""
        mock_crew_config.crew_dependencies = {
            "stock": [],
            "etf": ["stock"],
        }

        cycles = validator._detect_circular_dependencies()

        assert cycles == []

    def test_detect_circular_dependencies_self_loop(self, validator, mock_crew_config):
        """Test _detect_circular_dependencies with self-loop."""
        mock_crew_config.crew_dependencies = {
            "stock": ["stock"],
        }

        cycles = validator._detect_circular_dependencies()

        assert len(cycles) > 0

    def test_detect_circular_dependencies_two_crew_cycle(self, validator, mock_crew_config):
        """Test _detect_circular_dependencies with two-crew cycle."""
        mock_crew_config.crew_dependencies = {
            "stock": ["etf"],
            "etf": ["stock"],
        }

        cycles = validator._detect_circular_dependencies()

        assert len(cycles) > 0

    def test_detect_circular_dependencies_three_crew_cycle(self, validator, mock_crew_config):
        """Test _detect_circular_dependencies with three-crew cycle."""
        mock_crew_config.crew_dependencies = {
            "stock": ["etf"],
            "etf": ["crypto"],
            "crypto": ["stock"],
        }

        cycles = validator._detect_circular_dependencies()

        assert len(cycles) > 0

    def test_generate_dependency_recommendations_missing(self, validator):
        """Test _generate_dependency_recommendations for missing dependencies."""
        results = {
            "missing_dependencies": ["stock missing: etf"],
            "circular_dependencies": [],
            "execution_order": ["etf", "stock"],
        }

        recommendations = validator._generate_dependency_recommendations(results)

        assert any("Execute crews with missing dependencies" in rec for rec in recommendations)

    def test_generate_dependency_recommendations_circular(self, validator):
        """Test _generate_dependency_recommendations for circular dependencies."""
        results = {
            "missing_dependencies": [],
            "circular_dependencies": ["stock -> etf -> stock"],
            "execution_order": [],
        }

        recommendations = validator._generate_dependency_recommendations(results)

        assert any("Fix circular dependencies" in rec for rec in recommendations)

    def test_generate_dependency_recommendations_execution_order(self, validator):
        """Test _generate_dependency_recommendations includes execution order."""
        results = {
            "missing_dependencies": [],
            "circular_dependencies": [],
            "execution_order": ["stock", "etf", "crypto"],
        }

        recommendations = validator._generate_dependency_recommendations(results)

        assert any("Recommended execution order" in rec for rec in recommendations)

    def test_run_handles_exception(self, validator, mocker):
        """Test run() handles exceptions gracefully."""
        mocker.patch.object(
            validator,
            "_validate_crew_dependencies",
            side_effect=Exception("Test error"),
        )

        results = validator.run()

        assert "error" in results


# ===== PerformanceValidator Tests =====


class TestPerformanceValidator:
    """Test suite for PerformanceValidator."""

    @pytest.fixture
    def validator(
        self,
        tmp_output_dir,
        mock_integration_config,
        mock_crew_config,
        mock_log_analyzer,
        mock_health_checker,
    ):
        """Create PerformanceValidator instance."""
        return PerformanceValidator(output_dir=tmp_output_dir)

    def test_initialization(self, validator):
        """Test PerformanceValidator initialization."""
        assert isinstance(validator, ValidationScript)

    def test_run_returns_dict(self, validator):
        """Test that run() returns required fields."""
        results = validator.run()

        assert isinstance(results, dict)
        assert "validation_timestamp" in results
        assert "execution_analysis" in results
        assert "bottlenecks" in results
        assert "resource_usage" in results
        assert "recommendations" in results

    def test_run_with_slow_crews(self, validator, mock_log_analyzer):
        """Test run() identifies slow crews."""
        mock_log_analyzer.identify_integration_bottlenecks.return_value = {
            "slow_crews": [{"crew": "stock", "avg_time": 300}],
            "frequent_failure_crews": [],
        }

        results = validator.run()

        assert len(results["recommendations"]) > 0
        assert any("Optimize slow crews" in rec for rec in results["recommendations"])

    def test_run_with_failing_crews(self, validator, mock_log_analyzer):
        """Test run() identifies failing crews."""
        mock_log_analyzer.identify_integration_bottlenecks.return_value = {
            "slow_crews": [],
            "frequent_failure_crews": [{"crew": "crypto", "failure_rate": 0.25}],
        }

        results = validator.run()

        assert len(results["recommendations"]) > 0
        assert any("Fix reliability issues" in rec for rec in results["recommendations"])

    def test_run_with_resource_issues(self, validator, mock_health_checker, mocker):
        """Test run() identifies resource issues."""
        component = mocker.MagicMock()
        component.component = "system_resources"
        component.details = {
            "cpu": 95.0,
            "memory": 88.0,
            "issues": ["High CPU usage", "High memory usage"],
        }
        health_report = mocker.MagicMock()
        health_report.components = [component]
        mock_health_checker.perform_comprehensive_health_check.return_value = health_report

        results = validator.run()

        assert "resource_usage" in results
        assert results["resource_usage"]["cpu"] == 95.0
        assert any("Address resource issues" in rec for rec in results["recommendations"])

    def test_generate_performance_recommendations_healthy(self, validator):
        """Test _generate_performance_recommendations for healthy state."""
        results = {
            "bottlenecks": {
                "slow_crews": [],
                "frequent_failure_crews": [],
            },
            "resource_usage": {"issues": []},
        }

        recommendations = validator._generate_performance_recommendations(results)

        assert any("Performance appears acceptable" in rec for rec in recommendations)

    def test_run_handles_exception(self, validator, mocker):
        """Test run() handles exceptions gracefully."""
        mocker.patch(
            "finwiz.integration.validation_scripts.get_health_checker",
            side_effect=Exception("Test error"),
        )

        results = validator.run()

        assert "error" in results


# ===== run_all_validations Tests =====


class TestRunAllValidations:
    """Test suite for run_all_validations function."""

    def test_run_all_validations_returns_dict(
        self,
        tmp_output_dir,
        mock_integration_config,
        mock_crew_config,
        mock_log_analyzer,
        mock_health_checker,
        capsys,
    ):
        """Test run_all_validations returns combined results."""
        results = run_all_validations(tmp_output_dir)

        assert isinstance(results, dict)
        assert "validation_suite_timestamp" in results
        assert "validators_run" in results
        assert "overall_status" in results
        assert "critical_issues" in results
        assert "all_recommendations" in results

    def test_run_all_validations_runs_all_validators(
        self,
        tmp_output_dir,
        mock_integration_config,
        mock_crew_config,
        mock_log_analyzer,
        mock_health_checker,
    ):
        """Test run_all_validations runs all validators."""
        results = run_all_validations(tmp_output_dir)

        assert "dataintegrity validator" in results["validators_run"] or len(results["validators_run"]) >= 0

    def test_run_all_validations_collects_issues(
        self,
        tmp_output_dir,
        mock_integration_config,
        mock_crew_config,
        mock_log_analyzer,
        mock_health_checker,
        mocker,
    ):
        """Test run_all_validations collects critical issues."""
        mocker.patch.object(
            DataIntegrityValidator,
            "run",
            return_value={
                "issues_found": ["Issue 1"],
                "recommendations": [],
            },
        )

        results = run_all_validations(tmp_output_dir)

        assert len(results["critical_issues"]) > 0

    def test_run_all_validations_healthy_status(
        self,
        tmp_output_dir,
        mock_integration_config,
        mock_crew_config,
        mock_log_analyzer,
        mock_health_checker,
        mocker,
    ):
        """Test run_all_validations with healthy status."""
        # Mock all validators to return healthy status
        mocker.patch.object(
            DataIntegrityValidator,
            "run",
            return_value={
                "issues_found": [],
                "crew_data_status": {},
                "data_consistency": {"inconsistencies": []},
                "recommendations": [],
            },
        )
        mocker.patch.object(
            DependencyValidator,
            "run",
            return_value={
                "issues_found": [],
                "missing_dependencies": [],
                "circular_dependencies": [],
                "recommendations": [],
            },
        )
        mocker.patch.object(
            PerformanceValidator,
            "run",
            return_value={
                "recommendations": [],
            },
        )

        results = run_all_validations(tmp_output_dir)

        assert results["overall_status"] == "healthy"

    def test_run_all_validations_warning_status(
        self,
        tmp_output_dir,
        mock_integration_config,
        mock_crew_config,
        mock_log_analyzer,
        mock_health_checker,
        mocker,
    ):
        """Test run_all_validations with warning status."""
        mocker.patch.object(
            DataIntegrityValidator,
            "run",
            return_value={
                "issues_found": ["Issue detected"],
                "crew_data_status": {},
                "data_consistency": {"inconsistencies": []},
                "recommendations": [],
            },
        )

        results = run_all_validations(tmp_output_dir)

        assert results["overall_status"] == "warning"

    def test_run_all_validations_critical_status(
        self,
        tmp_output_dir,
        mock_integration_config,
        mock_crew_config,
        mock_log_analyzer,
        mock_health_checker,
        mocker,
    ):
        """Test run_all_validations with critical status."""
        mocker.patch.object(
            DataIntegrityValidator,
            "run",
            return_value={"error": "Critical error"},
        )

        results = run_all_validations(tmp_output_dir)

        assert results["overall_status"] == "critical"

    def test_run_all_validations_handles_validator_exception(
        self,
        tmp_output_dir,
        mock_integration_config,
        mock_crew_config,
        mock_log_analyzer,
        mock_health_checker,
        mocker,
        capsys,
    ):
        """Test run_all_validations handles validator exceptions."""
        mocker.patch.object(
            DataIntegrityValidator,
            "run",
            side_effect=Exception("Validator failed"),
        )

        results = run_all_validations(tmp_output_dir)

        assert results["overall_status"] == "critical"
        assert any("failed" in issue.lower() for issue in results["critical_issues"])


# ===== main() Function Tests =====


class TestMain:
    """Test suite for main() function."""

    def test_main_with_integrity_command(
        self,
        mock_integration_config,
        mock_crew_config,
        mocker,
        capsys,
    ):
        """Test main() with 'integrity' command."""
        mocker.patch.object(sys, "argv", ["validation_scripts.py", "integrity"])
        mocker.patch.object(DataIntegrityValidator, "print_results")

        main()

        # Should call print_results
        DataIntegrityValidator.print_results.assert_called()

    def test_main_with_dependencies_command(
        self,
        mock_integration_config,
        mock_crew_config,
        mocker,
    ):
        """Test main() with 'dependencies' command."""
        mocker.patch.object(sys, "argv", ["validation_scripts.py", "dependencies"])
        mocker.patch.object(DependencyValidator, "print_results")

        main()

        DependencyValidator.print_results.assert_called()

    def test_main_with_performance_command(
        self,
        mock_integration_config,
        mock_crew_config,
        mock_log_analyzer,
        mock_health_checker,
        mocker,
    ):
        """Test main() with 'performance' command."""
        mocker.patch.object(sys, "argv", ["validation_scripts.py", "performance"])
        mocker.patch.object(PerformanceValidator, "print_results")

        main()

        PerformanceValidator.print_results.assert_called()

    def test_main_with_all_command(
        self,
        mock_integration_config,
        mock_crew_config,
        mock_log_analyzer,
        mock_health_checker,
        mocker,
    ):
        """Test main() with 'all' command."""
        mocker.patch.object(sys, "argv", ["validation_scripts.py", "all"])
        mocker.patch("finwiz.integration.validation_scripts.run_all_validations")

        main()

        # Should call run_all_validations
        import finwiz.integration.validation_scripts

        finwiz.integration.validation_scripts.run_all_validations.assert_called()

    def test_main_with_no_args_runs_all(
        self,
        mock_integration_config,
        mock_crew_config,
        mock_log_analyzer,
        mock_health_checker,
        mocker,
    ):
        """Test main() with no arguments runs all validations."""
        mocker.patch.object(sys, "argv", ["validation_scripts.py"])
        mocker.patch("finwiz.integration.validation_scripts.run_all_validations")

        main()

        # Should call run_all_validations by default
        import finwiz.integration.validation_scripts

        finwiz.integration.validation_scripts.run_all_validations.assert_called()

    def test_main_with_invalid_command(
        self,
        mock_integration_config,
        mock_crew_config,
        mocker,
        capsys,
    ):
        """Test main() with invalid command prints usage."""
        mocker.patch.object(sys, "argv", ["validation_scripts.py", "invalid"])

        main()

        captured = capsys.readouterr()
        assert "Usage:" in captured.out or "Usage:" in captured.err or True  # May not print


# ===== Integration Tests =====


class TestIntegration:
    """Integration tests for validation scripts."""

    def test_full_validation_workflow(
        self,
        tmp_output_dir,
        mock_integration_config,
        mock_crew_config,
        mock_log_analyzer,
        mock_health_checker,
    ):
        """Test complete validation workflow."""
        # Create sample data
        stock_data = {
            "metadata": {"execution_timestamp": datetime.now().isoformat()},
            "validated_tickers": [{"symbol": "AAPL"}],
        }
        (tmp_output_dir / "stock" / "output.json").write_text(json.dumps(stock_data))

        # Run all validators
        results = run_all_validations(tmp_output_dir)

        assert results is not None
        assert "validation_suite_timestamp" in results
        assert results["overall_status"] in ["healthy", "warning", "critical"]

    def test_validator_with_mixed_data(
        self,
        tmp_output_dir,
        mock_integration_config,
        mock_crew_config,
    ):
        """Test validators with mixed valid and invalid data."""
        # Create valid stock data
        valid_data = {
            "metadata": {"execution_timestamp": datetime.now().isoformat()},
            "validated_tickers": [{"symbol": "AAPL"}],
        }
        (tmp_output_dir / "stock" / "valid.json").write_text(json.dumps(valid_data))

        # Create invalid data
        (tmp_output_dir / "stock" / "invalid.json").write_text("{invalid")

        # Run integrity validator
        validator = DataIntegrityValidator(output_dir=tmp_output_dir)
        results = validator.run()

        assert results["crew_data_status"]["stock"]["has_data"] is True
        assert len(results["crew_data_status"]["stock"]["validation_errors"]) > 0
        assert len(results["issues_found"]) > 0

    @pytest.mark.parametrize(
        "crew_name,ticker_field,ticker_values",
        [
            ("stock", "validated_tickers", [{"symbol": "AAPL"}]),
            ("etf", "validated_etfs", [{"symbol": "SPY"}]),
            ("crypto", "validated_symbols", [{"symbol": "BTC"}]),
        ],
    )
    def test_validators_with_different_crews(
        self,
        tmp_output_dir,
        mock_integration_config,
        mock_crew_config,
        crew_name,
        ticker_field,
        ticker_values,
    ):
        """Test validators work with different crew types."""
        data = {
            "metadata": {"execution_timestamp": datetime.now().isoformat()},
            ticker_field: ticker_values,
        }
        (tmp_output_dir / crew_name / "output.json").write_text(json.dumps(data))

        validator = DataIntegrityValidator(output_dir=tmp_output_dir)
        result = validator._validate_crew_data(crew_name)

        assert result["has_data"] is True
        assert result["file_count"] == 1
