"""
Unit tests for contract validator.

Tests for the ContractValidator class and related validation logic.
"""

import pytest
from faker import Faker

from finwiz.validation.contract import ContractValidator


class TestContractValidator:
    """Tests for ContractValidator class."""

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    @pytest.fixture
    def validator(self):
        """Create ContractValidator instance."""
        return ContractValidator()

    def test_should_initialize(self, validator):
        """Test ContractValidator initializes correctly."""
        assert validator is not None
        assert validator.STOCK_CONTRACT_KEYS is not None
        assert validator.ETF_CONTRACT_KEYS is not None
        assert validator.CRYPTO_CONTRACT_KEYS is not None

    def test_should_have_all_contract_keys(self, validator):
        """Test ALL_CONTRACT_KEYS combines all crew contracts."""
        all_keys = validator.ALL_CONTRACT_KEYS

        assert "ten_k_insights" in all_keys
        assert "market_sentiment" in all_keys
        assert "etf_factsheets" in all_keys
        assert "crypto_theses" in all_keys


class TestValidateCrewContract:
    """Tests for validate_crew_contract method."""

    @pytest.fixture
    def validator(self):
        """Create ContractValidator instance."""
        return ContractValidator()

    def test_should_validate_stock_crew_with_all_keys(self, validator):
        """Test valid stock crew data passes validation."""
        data = {
            "ten_k_insights": [],
            "market_sentiment": [],
            "risk_score_standardized": [],
        }

        result = validator.validate_crew_contract(data, "stock")

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_should_fail_stock_crew_missing_keys(self, validator):
        """Test stock crew with missing keys fails validation."""
        data = {"ten_k_insights": []}  # Missing other required keys

        result = validator.validate_crew_contract(data, "stock")

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "missing_required_keys" in str(result.errors)

    def test_should_validate_etf_crew_with_all_keys(self, validator):
        """Test valid ETF crew data passes validation."""
        data = {
            "etf_factsheets": [],
            "etf_holdings": [],
            "risk_score_standardized": [],
        }

        result = validator.validate_crew_contract(data, "etf")

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_should_fail_etf_crew_missing_keys(self, validator):
        """Test ETF crew with missing keys fails validation."""
        data = {"etf_factsheets": []}  # Missing other required keys

        result = validator.validate_crew_contract(data, "etf")

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_should_validate_crypto_crew_with_all_keys(self, validator):
        """Test valid crypto crew data passes validation."""
        data = {
            "crypto_theses": [],
            "risk_score_standardized": [],
        }

        result = validator.validate_crew_contract(data, "crypto")

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_should_warn_for_unknown_crew_type(self, validator):
        """Test unknown crew type generates warning."""
        data = {"some_key": "value"}

        result = validator.validate_crew_contract(data, "unknown")

        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert "No contract keys defined" in str(result.warnings)

    def test_should_warn_for_unexpected_keys(self, validator):
        """Test unexpected keys generate warnings."""
        data = {
            "ten_k_insights": [],
            "market_sentiment": [],
            "risk_score_standardized": [],
            "unexpected_field": "value",  # Not in contract
        }

        result = validator.validate_crew_contract(data, "stock")

        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert "Unexpected keys" in str(result.warnings)

    def test_should_ignore_private_keys(self, validator):
        """Test keys starting with underscore are ignored."""
        data = {
            "ten_k_insights": [],
            "market_sentiment": [],
            "risk_score_standardized": [],
            "_private_field": "value",  # Should be ignored
        }

        result = validator.validate_crew_contract(data, "stock")

        assert result.is_valid is True
        # No warning about _private_field

    def test_should_fail_for_wrong_type_list(self, validator):
        """Test wrong type for list field fails validation."""
        data = {
            "ten_k_insights": "not a list",  # Should be list
            "market_sentiment": [],
            "risk_score_standardized": [],
        }

        result = validator.validate_crew_contract(data, "stock")

        assert result.is_valid is False
        assert "invalid_type" in str(result.errors)

    def test_should_handle_report_crew_type(self, validator):
        """Test report crew type has no contract keys."""
        data = {"report_data": "value"}

        result = validator.validate_crew_contract(data, "report")

        assert result.is_valid is True
        # No missing keys error for report crew


class TestValidateReporterContract:
    """Tests for validate_reporter_contract method."""

    @pytest.fixture
    def validator(self):
        """Create ContractValidator instance."""
        return ContractValidator()

    def test_should_validate_reporter_with_all_keys(self, validator):
        """Test valid reporter data passes validation."""
        data = {
            "ten_k_insights": [],
            "stock_sentiments": [],
            "stock_risks": [],
            "etf_factsheets": [],
            "etf_holdings": [],
            "etf_risks": [],
            "crypto_theses": [],
            "crypto_risks": [],
        }

        result = validator.validate_reporter_contract(data)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_should_fail_reporter_missing_keys(self, validator):
        """Test reporter with missing keys fails validation."""
        data = {
            "ten_k_insights": [],
            "stock_sentiments": [],
            # Missing other required keys
        }

        result = validator.validate_reporter_contract(data)

        assert result.is_valid is False
        assert "missing_reporter_keys" in str(result.errors)

    def test_should_report_all_missing_keys(self, validator):
        """Test all missing keys are reported."""
        data = {}  # Empty data

        result = validator.validate_reporter_contract(data)

        assert result.is_valid is False
        # Should have 8 missing keys
        assert len(result.errors) > 0


class TestGetExpectedKeys:
    """Tests for _get_expected_keys method."""

    @pytest.fixture
    def validator(self):
        """Create ContractValidator instance."""
        return ContractValidator()

    def test_should_return_stock_keys(self, validator):
        """Test returns stock contract keys."""
        keys = validator._get_expected_keys("stock")

        assert "ten_k_insights" in keys
        assert "market_sentiment" in keys
        assert "risk_score_standardized" in keys

    def test_should_return_etf_keys(self, validator):
        """Test returns ETF contract keys."""
        keys = validator._get_expected_keys("etf")

        assert "etf_factsheets" in keys
        assert "etf_holdings" in keys
        assert "risk_score_standardized" in keys

    def test_should_return_crypto_keys(self, validator):
        """Test returns crypto contract keys."""
        keys = validator._get_expected_keys("crypto")

        assert "crypto_theses" in keys
        assert "risk_score_standardized" in keys

    def test_should_return_empty_for_report(self, validator):
        """Test returns empty dict for report crew."""
        keys = validator._get_expected_keys("report")

        assert keys == {}

    def test_should_return_empty_for_unknown(self, validator):
        """Test returns empty dict for unknown crew type."""
        keys = validator._get_expected_keys("unknown")

        assert keys == {}


class TestValidateKeyType:
    """Tests for _validate_key_type method."""

    @pytest.fixture
    def validator(self):
        """Create ContractValidator instance."""
        return ContractValidator()

    def test_should_pass_valid_list_type(self, validator):
        """Test valid list type passes."""
        from finwiz.validation.result import ValidationResult

        result = ValidationResult(is_valid=True)

        validator._validate_key_type([], "test_key", "list[SomeType]", result)

        assert result.is_valid is True

    def test_should_fail_invalid_list_type(self, validator):
        """Test non-list for list type fails."""
        from finwiz.validation.result import ValidationResult

        result = ValidationResult(is_valid=True)

        validator._validate_key_type("not a list", "test_key", "list[SomeType]", result)

        assert result.is_valid is False
        assert "invalid_type" in str(result.errors)

    def test_should_pass_valid_dict_type(self, validator):
        """Test valid dict type passes."""
        from finwiz.validation.result import ValidationResult

        result = ValidationResult(is_valid=True)

        validator._validate_key_type({}, "test_key", "dict", result)

        assert result.is_valid is True

    def test_should_fail_invalid_dict_type(self, validator):
        """Test non-dict for dict type fails."""
        from finwiz.validation.result import ValidationResult

        result = ValidationResult(is_valid=True)

        validator._validate_key_type("not a dict", "test_key", "dict", result)

        assert result.is_valid is False
        assert "invalid_type" in str(result.errors)
