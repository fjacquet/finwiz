"""Tests for crew output validation functionality."""

from finwiz.validation import ContractValidator, ValidationManager, ValidationMode


class TestContractValidator:
    """Test ContractValidator functionality."""

    def test_should_validate_stock_crew_contract_with_required_keys(self):
        # Arrange
        validator = ContractValidator()
        valid_stock_data = {
            "ten_k_insights": [],
            "market_sentiment": [],
            "risk_score_standardized": [],
        }

        # Act
        result = validator.validate_crew_contract(valid_stock_data, "stock")

        # Assert
        assert result.is_valid is True
        assert result.has_errors is False

    def test_should_reject_stock_crew_contract_with_missing_keys(self):
        # Arrange
        validator = ContractValidator()
        invalid_stock_data = {
            "ten_k_insights": [],
            # Missing market_sentiment and risk_score_standardized
        }

        # Act
        result = validator.validate_crew_contract(invalid_stock_data, "stock")

        # Assert
        assert result.is_valid is False
        assert result.has_errors is True
        assert any("missing_required_keys" in error.error_type for error in result.errors)
        assert any("market_sentiment" in str(error.context) for error in result.errors)

    def test_should_validate_etf_crew_contract_with_required_keys(self):
        # Arrange
        validator = ContractValidator()
        valid_etf_data = {
            "etf_factsheets": [],
            "etf_holdings": [],
            "risk_score_standardized": [],
        }

        # Act
        result = validator.validate_crew_contract(valid_etf_data, "etf")

        # Assert
        assert result.is_valid is True
        assert result.has_errors is False

    def test_should_validate_crypto_crew_contract_with_required_keys(self):
        # Arrange
        validator = ContractValidator()
        valid_crypto_data = {
            "crypto_theses": [],
            "risk_score_standardized": [],
        }

        # Act
        result = validator.validate_crew_contract(valid_crypto_data, "crypto")

        # Assert
        assert result.is_valid is True
        assert result.has_errors is False

    def test_should_warn_about_unexpected_keys(self):
        # Arrange
        validator = ContractValidator()
        data_with_unexpected_keys = {
            "ten_k_insights": [],
            "market_sentiment": [],
            "risk_score_standardized": [],
            "unexpected_key": "should_warn",
            "another_unexpected": "also_warn",
        }

        # Act
        result = validator.validate_crew_contract(data_with_unexpected_keys, "stock")

        # Assert
        assert result.is_valid is True  # Still valid, just warnings
        assert result.has_warnings is True
        assert any("schema drift" in warning.message for warning in result.warnings)

    def test_should_validate_key_types(self):
        # Arrange
        validator = ContractValidator()
        data_with_wrong_types = {
            "ten_k_insights": "should_be_list",  # Wrong type
            "market_sentiment": [],
            "risk_score_standardized": [],
        }

        # Act
        result = validator.validate_crew_contract(data_with_wrong_types, "stock")

        # Assert
        assert result.is_valid is False
        assert result.has_errors is True
        assert any("invalid_type" in error.error_type for error in result.errors)

    def test_should_handle_unknown_crew_type(self):
        # Arrange
        validator = ContractValidator()

        # Act
        result = validator.validate_crew_contract({}, "unknown_crew")

        # Assert
        assert result.is_valid is True  # No validation for unknown crew
        assert result.has_warnings is True
        assert any("No contract keys defined" in warning.message for warning in result.warnings)

    def test_should_validate_reporter_contract_with_all_keys(self):
        # Arrange
        validator = ContractValidator()
        complete_reporter_data = {
            "ten_k_insights": [],
            "stock_sentiments": [],
            "stock_risks": [],
            "etf_factsheets": [],
            "etf_holdings": [],
            "etf_risks": [],
            "crypto_theses": [],
            "crypto_risks": [],
        }

        # Act
        result = validator.validate_reporter_contract(complete_reporter_data)

        # Assert
        assert result.is_valid is True
        assert result.has_errors is False

    def test_should_reject_reporter_contract_with_missing_keys(self):
        # Arrange
        validator = ContractValidator()
        incomplete_reporter_data = {
            "ten_k_insights": [],
            "stock_sentiments": [],
            # Missing other required keys
        }

        # Act
        result = validator.validate_reporter_contract(incomplete_reporter_data)

        # Assert
        assert result.is_valid is False
        assert result.has_errors is True
        assert any("missing_reporter_keys" in error.error_type for error in result.errors)


class TestValidationManagerWithContracts:
    """Test ValidationManager integration with contract validation."""

    def test_should_validate_crew_output_with_contract_and_schema(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.WARN)

        # Valid stock crew output with proper contract keys
        valid_stock_output = {
            "ten_k_insights": [],
            "market_sentiment": [],
            "risk_score_standardized": [],
        }

        # Act
        result = manager.validate_crew_output(valid_stock_output, "stock", "analysis")

        # Assert
        assert result.is_valid is True
        # May have warnings about missing schema, but should not fail

    def test_should_fail_crew_output_validation_in_error_mode_with_contract_violations(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.ERROR)

        # Invalid stock crew output missing required contract keys
        invalid_stock_output = {
            "ten_k_insights": [],
            # Missing market_sentiment and risk_score_standardized
        }

        # Act
        result = manager.validate_crew_output(invalid_stock_output, "stock", "analysis")

        # Assert
        assert result.is_valid is False
        assert result.has_errors is True

    def test_should_validate_reporter_input_with_contract_and_schema(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.WARN)

        # Complete reporter input matching ReporterInput schema
        complete_reporter_input = {
            "schema_version": 1,
            "ten_k_insights": [],
            "stock_sentiments": [],
            "stock_risks": [],
            "etf_factsheets": [],
            "etf_holdings": [],
            "etf_risks": [],
            "crypto_theses": [],
            "crypto_risks": [],
            "as_of": "2025-01-01",
        }

        # Act
        result = manager.validate_reporter_input(complete_reporter_input)

        # Assert
        assert result.is_valid is True
        assert result.sanitized_data is not None

    def test_should_handle_contract_violations_based_on_strictness_mode(self):
        # Arrange
        manager = ValidationManager()
        invalid_data = {"incomplete": "data"}

        # Test OFF mode - should ignore contract violations
        manager.set_strictness_mode(ValidationMode.OFF)
        result_off = manager.validate_crew_output(invalid_data, "stock", "analysis")
        assert result_off.is_valid is True

        # Test WARN mode - should warn but continue
        manager.set_strictness_mode(ValidationMode.WARN)
        result_warn = manager.validate_crew_output(invalid_data, "stock", "analysis")
        assert result_warn.is_valid is True
        assert result_warn.has_warnings is True

        # Test ERROR mode - should fail
        manager.set_strictness_mode(ValidationMode.ERROR)
        result_error = manager.validate_crew_output(invalid_data, "stock", "analysis")
        assert result_error.is_valid is False
        assert result_error.has_errors is True


class TestCrewOutputValidationIntegration:
    """Integration tests for crew output validation with real schemas."""

    def test_should_validate_stock_crew_with_real_schema_data(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.ERROR)

        # Real-looking individual TenKInsight data (not full crew output)
        ten_k_insight_data = {
            "schema_version": 1,
            "ticker": "AAPL",
            "filing_url": "https://sec.gov/filing/123",
            "filed_at": "2024-01-01T00:00:00Z",
            "section": "Item 1A",
            "excerpt": "This is a sample excerpt from the 10-K filing that meets minimum length requirements.",
            "sec_citation": "10-K (2024), Item 1A, p. 17",
        }

        # Act - validate individual schema item
        result = manager.validate_with_schema(ten_k_insight_data, "TenKInsight")

        # Assert
        assert result.is_valid is True
        assert result.sanitized_data is not None

    def test_should_validate_etf_crew_with_real_schema_data(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.ERROR)

        # Real-looking individual ETFFactsheet data
        etf_factsheet_data = {
            "schema_version": 1,
            "ticker": "SPY",
            "issuer": "State Street",
            "expense_ratio": 0.09,
            "tracking_diff": 0.02,
            "replication_method": "physical",
            "factsheet_url": "https://example.com/spy-factsheet",
            "as_of": "2025-01-01",
            "factsheet_highlights": ["Low cost", "High liquidity"],
            "top_holdings": [],
        }

        # Act - validate individual schema item
        result = manager.validate_with_schema(etf_factsheet_data, "ETFFactsheet")

        # Assert
        assert result.is_valid is True
        assert result.sanitized_data is not None

    def test_should_validate_crypto_crew_with_real_schema_data(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.ERROR)

        # Real-looking individual CryptoThesis data
        crypto_thesis_data = {
            "schema_version": 1,
            "symbol": "BTC",
            "thesis_bullets": ["Digital gold narrative strengthening", "Institutional adoption increasing"],
            "references": ["https://example.com/btc-analysis"],
        }

        # Act - validate individual schema item
        result = manager.validate_with_schema(crypto_thesis_data, "CryptoThesis")

        # Assert
        assert result.is_valid is True
        assert result.sanitized_data is not None
