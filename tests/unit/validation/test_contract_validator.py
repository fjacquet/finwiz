"""Tests for contract_validator module."""



class TestContractValidator:
    """Tests for ContractValidator class."""

    def test_init(self):
        """Test ContractValidator initialization."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()
        assert validator is not None

    def test_contract_keys_defined(self):
        """Test that contract keys are properly defined."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        # Stock contract keys
        assert "ten_k_insights" in validator.STOCK_CONTRACT_KEYS
        assert "market_sentiment" in validator.STOCK_CONTRACT_KEYS
        assert "risk_score_standardized" in validator.STOCK_CONTRACT_KEYS

        # ETF contract keys
        assert "etf_factsheets" in validator.ETF_CONTRACT_KEYS
        assert "etf_holdings" in validator.ETF_CONTRACT_KEYS

        # Crypto contract keys
        assert "crypto_theses" in validator.CRYPTO_CONTRACT_KEYS

    def test_all_contract_keys_includes_all(self):
        """Test ALL_CONTRACT_KEYS includes all individual contract keys."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        for key in validator.STOCK_CONTRACT_KEYS:
            assert key in validator.ALL_CONTRACT_KEYS

        for key in validator.ETF_CONTRACT_KEYS:
            assert key in validator.ALL_CONTRACT_KEYS

        for key in validator.CRYPTO_CONTRACT_KEYS:
            assert key in validator.ALL_CONTRACT_KEYS

    def test_validate_crew_contract_stock_valid(self):
        """Test validating valid stock crew contract."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        data = {
            "ten_k_insights": [{"insight": "test"}],
            "market_sentiment": [{"sentiment": "positive"}],
            "risk_score_standardized": [{"score": 0.5}],
        }

        result = validator.validate_crew_contract(data, "stock")

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_crew_contract_stock_missing_keys(self):
        """Test validating stock crew contract with missing keys."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        data = {
            "ten_k_insights": [{"insight": "test"}],
            # Missing market_sentiment and risk_score_standardized
        }

        result = validator.validate_crew_contract(data, "stock")

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("missing" in str(e).lower() for e in result.errors)

    def test_validate_crew_contract_etf_valid(self):
        """Test validating valid ETF crew contract."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        data = {
            "etf_factsheets": [{"factsheet": "test"}],
            "etf_holdings": [{"holding": "AAPL"}],
            "risk_score_standardized": [{"score": 0.3}],
        }

        result = validator.validate_crew_contract(data, "etf")

        assert result.is_valid is True

    def test_validate_crew_contract_crypto_valid(self):
        """Test validating valid crypto crew contract."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        data = {
            "crypto_theses": [{"thesis": "bullish"}],
            "risk_score_standardized": [{"score": 0.8}],
        }

        result = validator.validate_crew_contract(data, "crypto")

        assert result.is_valid is True

    def test_validate_crew_contract_unknown_type(self):
        """Test validating contract with unknown crew type."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        data = {"some_key": "value"}

        result = validator.validate_crew_contract(data, "unknown_crew")

        # Should have warning about unknown crew type
        assert len(result.warnings) > 0
        assert any("no contract keys" in str(w).lower() for w in result.warnings)

    def test_validate_crew_contract_unexpected_keys(self):
        """Test validating contract with unexpected keys."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        data = {
            "ten_k_insights": [{"insight": "test"}],
            "market_sentiment": [{"sentiment": "positive"}],
            "risk_score_standardized": [{"score": 0.5}],
            "unexpected_key": "value",
            "another_unexpected": "data",
        }

        result = validator.validate_crew_contract(data, "stock")

        # Should have warnings about unexpected keys
        assert len(result.warnings) > 0
        assert any("unexpected" in str(w).lower() for w in result.warnings)

    def test_validate_crew_contract_private_keys_ignored(self):
        """Test that private keys (starting with _) are ignored."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        data = {
            "ten_k_insights": [{"insight": "test"}],
            "market_sentiment": [{"sentiment": "positive"}],
            "risk_score_standardized": [{"score": 0.5}],
            "_internal_key": "ignored",
            "_metadata": {"debug": True},
        }

        result = validator.validate_crew_contract(data, "stock")

        # Private keys should not trigger warnings
        for warning in result.warnings:
            assert "_internal_key" not in str(warning)
            assert "_metadata" not in str(warning)

    def test_validate_crew_contract_invalid_type_list_expected(self):
        """Test validating contract with wrong type (list expected, got other)."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        data = {
            "ten_k_insights": "not a list",  # Should be list
            "market_sentiment": [{"sentiment": "positive"}],
            "risk_score_standardized": [{"score": 0.5}],
        }

        result = validator.validate_crew_contract(data, "stock")

        assert result.is_valid is False
        assert any("invalid_type" in str(e) for e in result.errors)

    def test_validate_crew_contract_report_type(self):
        """Test validating report crew type (no output contract)."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        data = {"any_key": "any_value"}

        result = validator.validate_crew_contract(data, "report")

        # Report type has no contract keys, so should pass with warning
        assert len(result.warnings) > 0

    def test_validate_reporter_contract_valid(self):
        """Test validating valid reporter contract."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        data = {
            "ten_k_insights": [{"insight": "test"}],
            "stock_sentiments": [{"sentiment": "positive"}],
            "stock_risks": [{"risk": "medium"}],
            "etf_factsheets": [{"factsheet": "data"}],
            "etf_holdings": [{"holding": "SPY"}],
            "etf_risks": [{"risk": "low"}],
            "crypto_theses": [{"thesis": "bullish"}],
            "crypto_risks": [{"risk": "high"}],
        }

        result = validator.validate_reporter_contract(data)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_reporter_contract_missing_keys(self):
        """Test validating reporter contract with missing keys."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        data = {
            "ten_k_insights": [{"insight": "test"}],
            # Missing most required keys
        }

        result = validator.validate_reporter_contract(data)

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("missing" in str(e).lower() for e in result.errors)

    def test_get_expected_keys_stock(self):
        """Test _get_expected_keys for stock crew."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        keys = validator._get_expected_keys("stock")

        assert keys == validator.STOCK_CONTRACT_KEYS

    def test_get_expected_keys_etf(self):
        """Test _get_expected_keys for ETF crew."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        keys = validator._get_expected_keys("etf")

        assert keys == validator.ETF_CONTRACT_KEYS

    def test_get_expected_keys_crypto(self):
        """Test _get_expected_keys for crypto crew."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        keys = validator._get_expected_keys("crypto")

        assert keys == validator.CRYPTO_CONTRACT_KEYS

    def test_get_expected_keys_report(self):
        """Test _get_expected_keys for report crew."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        keys = validator._get_expected_keys("report")

        assert keys == {}

    def test_get_expected_keys_unknown(self):
        """Test _get_expected_keys for unknown crew type."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        keys = validator._get_expected_keys("unknown")

        assert keys == {}

    def test_validate_key_type_list_valid(self):
        """Test _validate_key_type with valid list type."""
        from finwiz.validation.contract_validator import ContractValidator
        from finwiz.validation.result import ValidationResult

        validator = ContractValidator()
        result = ValidationResult(is_valid=True)

        validator._validate_key_type(
            [{"item": 1}], "test_key", "list[TestItem]", result
        )

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_key_type_list_invalid(self):
        """Test _validate_key_type with invalid list type."""
        from finwiz.validation.contract_validator import ContractValidator
        from finwiz.validation.result import ValidationResult

        validator = ContractValidator()
        result = ValidationResult(is_valid=True)

        validator._validate_key_type("not a list", "test_key", "list[TestItem]", result)

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_key_type_dict_valid(self):
        """Test _validate_key_type with valid dict type."""
        from finwiz.validation.contract_validator import ContractValidator
        from finwiz.validation.result import ValidationResult

        validator = ContractValidator()
        result = ValidationResult(is_valid=True)

        validator._validate_key_type({"key": "value"}, "test_key", "dict", result)

        assert result.is_valid is True

    def test_validate_key_type_dict_invalid(self):
        """Test _validate_key_type with invalid dict type."""
        from finwiz.validation.contract_validator import ContractValidator
        from finwiz.validation.result import ValidationResult

        validator = ContractValidator()
        result = ValidationResult(is_valid=True)

        validator._validate_key_type("not a dict", "test_key", "dict", result)

        assert result.is_valid is False


class TestValidationResultIntegration:
    """Tests for ValidationResult integration with ContractValidator."""

    def test_validation_result_errors_structure(self):
        """Test that validation errors have proper structure."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        data = {
            "ten_k_insights": "not a list",
        }

        result = validator.validate_crew_contract(data, "stock")

        for error in result.errors:
            # Errors should have required attributes
            assert hasattr(error, "field_path") or "field_path" in str(error)

    def test_validation_result_warnings_structure(self):
        """Test that validation warnings have proper structure."""
        from finwiz.validation.contract_validator import ContractValidator

        validator = ContractValidator()

        data = {"unexpected_key": "value"}

        result = validator.validate_crew_contract(data, "unknown")

        assert len(result.warnings) > 0
