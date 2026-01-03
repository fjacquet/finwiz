"""
Unit tests for data consolidation validator.

Tests for DataConsolidationValidator class and related functions.
"""

import pytest
from faker import Faker

from finwiz.validation.consolidation import (
    DataConsolidationValidator,
    DataRetrievalError,
)


class TestDataRetrievalError:
    """Tests for DataRetrievalError exception."""

    def test_should_be_exception(self):
        """Test DataRetrievalError is an Exception."""
        error = DataRetrievalError("test message")

        assert isinstance(error, Exception)
        assert str(error) == "test message"


class TestDataConsolidationValidator:
    """Tests for DataConsolidationValidator class."""

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    @pytest.fixture
    def mock_registry_manager(self, mocker):
        """Create mock registry manager."""
        return mocker.Mock()

    @pytest.fixture
    def validator(self, mock_registry_manager):
        """Create DataConsolidationValidator instance."""
        return DataConsolidationValidator(mock_registry_manager)

    def test_should_initialize_with_registry_manager(self, mock_registry_manager):
        """Test initialization with registry manager."""
        validator = DataConsolidationValidator(mock_registry_manager)

        assert validator.registry_manager is mock_registry_manager


class TestValidateCrewDataRetrieval:
    """Tests for validate_crew_data_retrieval method."""

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    @pytest.fixture
    def mock_registry_manager(self, mocker):
        """Create mock registry manager."""
        return mocker.Mock()

    @pytest.fixture
    def validator(self, mock_registry_manager):
        """Create DataConsolidationValidator instance."""
        return DataConsolidationValidator(mock_registry_manager)

    @pytest.fixture
    def valid_crew_data(self, fake):
        """Create valid crew data."""
        return {
            "crew_name": "stock",
            "execution_id": fake.uuid4(),
            "asset_class": "equity",
            "analysis_timestamp": fake.iso8601(),
            "composite_score": 0.75,
            "grade": "B+",
            "recommendation": "Buy",
            "rationale": fake.sentence(),
        }

    def test_should_retrieve_all_crew_data(
        self, validator, mock_registry_manager, valid_crew_data
    ):
        """Test successful retrieval of all crew data."""
        mock_registry_manager.get_crew_data_with_freshness_check.return_value = (
            valid_crew_data
        )

        result = validator.validate_crew_data_retrieval(["stock"])

        assert "stock" in result
        assert result["stock"] == valid_crew_data

    def test_should_raise_for_missing_crew_data(
        self, validator, mock_registry_manager
    ):
        """Test raises error when crew data is missing."""
        mock_registry_manager.get_crew_data_with_freshness_check.return_value = None

        with pytest.raises(DataRetrievalError, match="Missing data for crews"):
            validator.validate_crew_data_retrieval(["stock"])

    def test_should_raise_for_corrupted_crew_data(
        self, validator, mock_registry_manager
    ):
        """Test raises error when crew data is corrupted."""
        # Data missing required fields
        mock_registry_manager.get_crew_data_with_freshness_check.return_value = {
            "crew_name": "stock"
            # Missing other required fields
        }

        with pytest.raises(DataRetrievalError, match="Corrupted data for crews"):
            validator.validate_crew_data_retrieval(["stock"])

    def test_should_handle_multiple_crews(
        self, validator, mock_registry_manager, valid_crew_data, fake
    ):
        """Test retrieval of multiple crews."""
        etf_data = {
            "crew_name": "etf",
            "execution_id": fake.uuid4(),
            "asset_class": "etf",
            "analysis_timestamp": fake.iso8601(),
            "composite_score": 0.65,
            "grade": "C+",
            "recommendation": "Hold",
            "rationale": fake.sentence(),
        }

        mock_registry_manager.get_crew_data_with_freshness_check.side_effect = [
            valid_crew_data,
            etf_data,
        ]

        result = validator.validate_crew_data_retrieval(["stock", "etf"])

        assert len(result) == 2
        assert "stock" in result
        assert "etf" in result

    def test_should_collect_all_missing_crews(
        self, validator, mock_registry_manager
    ):
        """Test collects all missing crews in error message."""
        mock_registry_manager.get_crew_data_with_freshness_check.return_value = None

        with pytest.raises(DataRetrievalError) as exc_info:
            validator.validate_crew_data_retrieval(["stock", "etf"])

        assert "stock" in str(exc_info.value)
        assert "etf" in str(exc_info.value)


class TestValidateCrewDataStructure:
    """Tests for _validate_crew_data_structure method."""

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    @pytest.fixture
    def mock_registry_manager(self, mocker):
        """Create mock registry manager."""
        return mocker.Mock()

    @pytest.fixture
    def validator(self, mock_registry_manager):
        """Create DataConsolidationValidator instance."""
        return DataConsolidationValidator(mock_registry_manager)

    def test_should_return_false_for_missing_required_fields(self, validator):
        """Test returns False when required fields missing."""
        data = {"crew_name": "stock"}  # Missing other required fields

        result = validator._validate_crew_data_structure(data, "stock")

        assert result is False

    def test_should_return_true_for_valid_individual_data(self, validator, fake):
        """Test returns True for valid individual ticker data."""
        data = {
            "crew_name": "stock",
            "execution_id": fake.uuid4(),
            "asset_class": "equity",
            "analysis_timestamp": fake.iso8601(),
            "composite_score": 0.75,
            "grade": "B+",
            "recommendation": "Buy",
            "rationale": fake.sentence(),
        }

        result = validator._validate_crew_data_structure(data, "stock")

        assert result is True

    def test_should_return_true_for_valid_consolidated_data(self, validator, fake):
        """Test returns True for valid consolidated data."""
        data = {
            "crew_name": "stock",
            "execution_id": fake.uuid4(),
            "asset_class": "equity",
            "analysis_timestamp": fake.iso8601(),
            "ticker_analyses": {"AAPL": {"score": 0.8}},
            "summary_statistics": {"avg_score": 0.8},
        }

        result = validator._validate_crew_data_structure(data, "stock")

        assert result is True

    def test_should_return_false_for_empty_ticker_analyses(self, validator, fake):
        """Test returns False when ticker_analyses is empty."""
        data = {
            "crew_name": "stock",
            "execution_id": fake.uuid4(),
            "asset_class": "equity",
            "analysis_timestamp": fake.iso8601(),
            "ticker_analyses": {},
            "summary_statistics": {"avg_score": 0.0},
        }

        result = validator._validate_crew_data_structure(data, "stock")

        assert result is False

    def test_should_return_false_for_invalid_ticker_analyses_type(
        self, validator, fake
    ):
        """Test returns False when ticker_analyses is not a dict."""
        data = {
            "crew_name": "stock",
            "execution_id": fake.uuid4(),
            "asset_class": "equity",
            "analysis_timestamp": fake.iso8601(),
            "ticker_analyses": "not a dict",
            "summary_statistics": {"avg_score": 0.0},
        }

        result = validator._validate_crew_data_structure(data, "stock")

        assert result is False

    def test_should_return_false_for_invalid_summary_statistics_type(
        self, validator, fake
    ):
        """Test returns False when summary_statistics is not a dict."""
        data = {
            "crew_name": "stock",
            "execution_id": fake.uuid4(),
            "asset_class": "equity",
            "analysis_timestamp": fake.iso8601(),
            "ticker_analyses": {"AAPL": {}},
            "summary_statistics": "not a dict",
        }

        result = validator._validate_crew_data_structure(data, "stock")

        assert result is False

    def test_should_return_false_for_missing_analysis_fields(self, validator, fake):
        """Test returns False when no analysis fields present."""
        data = {
            "crew_name": "stock",
            "execution_id": fake.uuid4(),
            "asset_class": "equity",
            "analysis_timestamp": fake.iso8601(),
            # No analysis fields like composite_score, grade, etc.
        }

        result = validator._validate_crew_data_structure(data, "stock")

        assert result is False

    def test_should_return_false_for_invalid_composite_score(self, validator, fake):
        """Test returns False for invalid composite_score."""
        data = {
            "crew_name": "stock",
            "execution_id": fake.uuid4(),
            "asset_class": "equity",
            "analysis_timestamp": fake.iso8601(),
            "composite_score": 1.5,  # Invalid - must be 0-1
        }

        result = validator._validate_crew_data_structure(data, "stock")

        assert result is False

    def test_should_return_false_for_negative_composite_score(self, validator, fake):
        """Test returns False for negative composite_score."""
        data = {
            "crew_name": "stock",
            "execution_id": fake.uuid4(),
            "asset_class": "equity",
            "analysis_timestamp": fake.iso8601(),
            "composite_score": -0.5,  # Invalid - must be 0-1
        }

        result = validator._validate_crew_data_structure(data, "stock")

        assert result is False

    def test_should_return_false_for_invalid_grade(self, validator, fake):
        """Test returns False for invalid grade."""
        data = {
            "crew_name": "stock",
            "execution_id": fake.uuid4(),
            "asset_class": "equity",
            "analysis_timestamp": fake.iso8601(),
            "grade": "X",  # Invalid grade
        }

        result = validator._validate_crew_data_structure(data, "stock")

        assert result is False

    def test_should_accept_all_valid_grades(self, validator, fake):
        """Test accepts all valid grades."""
        valid_grades = ["A+", "A", "B+", "B", "C+", "C", "D+", "D", "F"]

        for grade in valid_grades:
            data = {
                "crew_name": "stock",
                "execution_id": fake.uuid4(),
                "asset_class": "equity",
                "analysis_timestamp": fake.iso8601(),
                "grade": grade,
            }

            result = validator._validate_crew_data_structure(data, "stock")

            assert result is True, f"Grade {grade} should be valid"

    def test_should_accept_recommendation_as_analysis_field(self, validator, fake):
        """Test accepts recommendation as valid analysis field."""
        data = {
            "crew_name": "stock",
            "execution_id": fake.uuid4(),
            "asset_class": "equity",
            "analysis_timestamp": fake.iso8601(),
            "recommendation": "Buy",
        }

        result = validator._validate_crew_data_structure(data, "stock")

        assert result is True

    def test_should_accept_rationale_as_analysis_field(self, validator, fake):
        """Test accepts rationale as valid analysis field."""
        data = {
            "crew_name": "stock",
            "execution_id": fake.uuid4(),
            "asset_class": "equity",
            "analysis_timestamp": fake.iso8601(),
            "rationale": fake.sentence(),
        }

        result = validator._validate_crew_data_structure(data, "stock")

        assert result is True

    def test_should_allow_crew_name_mismatch_for_generic_crews(self, validator, fake):
        """Test allows crew name mismatch for stock/etf/crypto."""
        data = {
            "crew_name": "different_name",
            "execution_id": fake.uuid4(),
            "asset_class": "equity",
            "analysis_timestamp": fake.iso8601(),
            "composite_score": 0.75,
        }

        # For generic crew types (stock, etf, crypto), mismatch is allowed
        result = validator._validate_crew_data_structure(data, "stock")

        assert result is True

    def test_should_fail_crew_name_mismatch_for_specific_crews(self, validator, fake):
        """Test fails crew name mismatch for specific crew names."""
        data = {
            "crew_name": "wrong_name",
            "execution_id": fake.uuid4(),
            "asset_class": "equity",
            "analysis_timestamp": fake.iso8601(),
            "composite_score": 0.75,
        }

        # For specific crew names, mismatch is not allowed
        result = validator._validate_crew_data_structure(data, "specific_crew")

        assert result is False
