"""Tests for integration/data_transformation.py module."""

from datetime import datetime
from types import MappingProxyType

from pydantic import BaseModel

from finwiz.integration.data_transformation import (
    _calculate_data_completeness,
    _extract_key_insights,
    _identify_cross_crew_correlations,
    consolidate_market_sentiment_data,
    consolidate_ticker_validation_data,
    create_error_response_for_sentiment,
    create_error_response_for_ticker_validation,
    generate_core_analysis_summary,
    serialize_datetime_objects,
)


class TestSerializeDatetimeObjects:
    """Tests for serialize_datetime_objects function."""

    def test_should_return_string_as_is(self):
        """Test that strings are returned unchanged."""
        result = serialize_datetime_objects("hello")
        assert result == "hello"

    def test_should_return_int_as_is(self):
        """Test that integers are returned unchanged."""
        result = serialize_datetime_objects(42)
        assert result == 42

    def test_should_return_float_as_is(self):
        """Test that floats are returned unchanged."""
        result = serialize_datetime_objects(3.14)
        assert result == 3.14

    def test_should_return_bool_as_is(self):
        """Test that booleans are returned unchanged."""
        result = serialize_datetime_objects(True)
        assert result is True

    def test_should_return_none_as_is(self):
        """Test that None is returned unchanged."""
        result = serialize_datetime_objects(None)
        assert result is None

    def test_should_serialize_datetime_to_isoformat(self):
        """Test that datetime objects are converted to ISO format."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = serialize_datetime_objects(dt)
        assert result == "2024-01-15T10:30:00"

    def test_should_serialize_dict_with_datetime(self):
        """Test that dicts containing datetime objects are serialized."""
        data = {
            "name": "test",
            "date": datetime(2024, 1, 15),
        }
        result = serialize_datetime_objects(data)
        assert result["name"] == "test"
        assert result["date"] == "2024-01-15T00:00:00"

    def test_should_serialize_nested_dict(self):
        """Test that nested dicts are serialized recursively."""
        data = {
            "outer": {
                "inner": {
                    "date": datetime(2024, 1, 15),
                }
            }
        }
        result = serialize_datetime_objects(data)
        assert result["outer"]["inner"]["date"] == "2024-01-15T00:00:00"

    def test_should_serialize_list_with_datetime(self):
        """Test that lists containing datetime objects are serialized."""
        data = [datetime(2024, 1, 15), "test", 42]
        result = serialize_datetime_objects(data)
        assert result == ["2024-01-15T00:00:00", "test", 42]

    def test_should_serialize_tuple_to_list(self):
        """Test that tuples are converted to lists."""
        data = (1, 2, 3)
        result = serialize_datetime_objects(data)
        assert result == [1, 2, 3]

    def test_should_serialize_set_to_list(self):
        """Test that sets are converted to lists."""
        data = {1, 2, 3}
        result = serialize_datetime_objects(data)
        assert sorted(result) == [1, 2, 3]

    def test_should_serialize_mapping_proxy(self):
        """Test that MappingProxyType objects are serialized."""
        data = MappingProxyType({"key": "value", "date": datetime(2024, 1, 15)})
        result = serialize_datetime_objects(data)
        assert result["key"] == "value"
        assert result["date"] == "2024-01-15T00:00:00"

    def test_should_serialize_pydantic_v2_model(self):
        """Test that Pydantic v2 models are serialized via model_dump."""
        class SampleModel(BaseModel):
            name: str
            value: int

        model = SampleModel(name="test", value=42)
        result = serialize_datetime_objects(model)
        assert result == {"name": "test", "value": 42}

    def test_should_handle_circular_reference(self):
        """Test that circular references are handled gracefully."""
        data: dict = {"key": "value"}
        data["self"] = data  # Create circular reference
        result = serialize_datetime_objects(data)
        assert result["key"] == "value"
        assert "circular reference" in result["self"]

    def test_should_serialize_object_with_dict(self):
        """Test that objects with __dict__ are serialized."""
        class SimpleObject:
            def __init__(self):
                self.name = "test"
                self.value = 42

        obj = SimpleObject()
        result = serialize_datetime_objects(obj)
        assert result["name"] == "test"
        assert result["value"] == 42

    def test_should_return_string_for_special_classes(self):
        """Test that special class instances return string representation."""
        class CrewDataAccessor:
            pass

        obj = CrewDataAccessor()
        result = serialize_datetime_objects(obj)
        assert result == "<CrewDataAccessor instance>"

    def test_should_convert_unknown_types_to_string(self):
        """Test that unknown types are converted to string."""
        class UnknownType:
            __slots__ = ()  # No __dict__

            def __str__(self):
                return "UnknownType instance"

            def __iter__(self):
                raise TypeError("not iterable")

        obj = UnknownType()
        result = serialize_datetime_objects(obj)
        assert "UnknownType" in str(result)


class TestConsolidateMarketSentimentData:
    """Tests for consolidate_market_sentiment_data function."""

    def test_should_return_empty_sentiment_for_empty_input(self):
        """Test that empty input returns default sentiment structure."""
        result = consolidate_market_sentiment_data({})
        assert result["aggregated_scores"]["total_sources"] == 0
        assert result["data_quality"] == "INSUFFICIENT"
        assert result["crew_sentiments"] == {}

    def test_should_consolidate_stock_sentiment(self):
        """Test consolidation of stock market sentiment data."""
        crew_data = {
            "stock": {
                "market_sentiments": [
                    {
                        "positive": 0.6,
                        "neutral": 0.3,
                        "negative": 0.1,
                        "source_url": "https://example.com/1",
                        "confidence": 0.8,
                    },
                    {
                        "positive": 0.5,
                        "neutral": 0.4,
                        "negative": 0.1,
                        "source_url": "https://example.com/2",
                        "confidence": 0.7,
                    },
                ]
            }
        }
        result = consolidate_market_sentiment_data(crew_data)
        assert result["aggregated_scores"]["total_sources"] == 2
        assert result["aggregated_scores"]["positive"] > 0
        assert "stock" in result["crew_sentiments"]
        assert result["data_quality"] == "MEDIUM"  # 2-4 sources = MEDIUM

    def test_should_consolidate_crypto_sentiment(self):
        """Test consolidation of crypto market sentiment data."""
        crew_data = {
            "crypto": {
                "market_analysis": [
                    {
                        "sentiment": {
                            "positive": 0.7,
                            "neutral": 0.2,
                            "negative": 0.1,
                            "confidence": 0.9,
                        }
                    }
                ]
            }
        }
        result = consolidate_market_sentiment_data(crew_data)
        assert "crypto" in result["crew_sentiments"]

    def test_should_handle_crypto_sentiment_as_dict(self):
        """Test handling of crypto sentiment as a single dict."""
        crew_data = {
            "crypto": {
                "market_analysis": {
                    "sentiment": {
                        "positive": 0.7,
                        "neutral": 0.2,
                        "negative": 0.1,
                    }
                }
            }
        }
        result = consolidate_market_sentiment_data(crew_data)
        assert "crypto" in result["crew_sentiments"]

    def test_should_normalize_percentage_scores(self):
        """Test normalization of percentage-based sentiment scores."""
        crew_data = {
            "stock": {
                "market_sentiments": [
                    {
                        "positive": 60,  # Percentage
                        "neutral": 30,
                        "negative": 10,
                        "confidence": 0.8,
                    }
                ]
            }
        }
        result = consolidate_market_sentiment_data(crew_data)
        # Scores should be normalized to 0-1 range
        scores = result["aggregated_scores"]
        assert 0 <= scores["positive"] <= 1
        assert 0 <= scores["neutral"] <= 1
        assert 0 <= scores["negative"] <= 1

    def test_should_extract_top_sources(self):
        """Test extraction of top sentiment sources."""
        crew_data = {
            "stock": {
                "market_sentiments": [
                    {"positive": 0.8, "neutral": 0.1, "negative": 0.1, "confidence": 0.9},
                    {"positive": 0.6, "neutral": 0.2, "negative": 0.2, "confidence": 0.8},
                    {"positive": 0.4, "neutral": 0.3, "negative": 0.3, "confidence": 0.7},
                    {"positive": 0.5, "neutral": 0.3, "negative": 0.2, "confidence": 0.6},
                ]
            }
        }
        result = consolidate_market_sentiment_data(crew_data)
        assert len(result["top_sources"]) <= 3

    def test_should_assess_data_quality_high(self):
        """Test HIGH data quality assessment."""
        crew_data = {
            "stock": {
                "market_sentiments": [
                    {"positive": 0.5, "neutral": 0.3, "negative": 0.2, "confidence": 0.5}
                    for _ in range(5)
                ]
            }
        }
        result = consolidate_market_sentiment_data(crew_data)
        assert result["data_quality"] == "HIGH"

    def test_should_assess_data_quality_medium(self):
        """Test MEDIUM data quality assessment."""
        crew_data = {
            "stock": {
                "market_sentiments": [
                    {"positive": 0.5, "neutral": 0.3, "negative": 0.2, "confidence": 0.5}
                    for _ in range(3)
                ]
            }
        }
        result = consolidate_market_sentiment_data(crew_data)
        assert result["data_quality"] == "MEDIUM"

    def test_should_skip_non_dict_sentiments(self):
        """Test that non-dict sentiments are skipped."""
        crew_data = {
            "stock": {
                "market_sentiments": [
                    {"positive": 0.5, "neutral": 0.3, "negative": 0.2},
                    "invalid_sentiment",
                    None,
                ]
            }
        }
        result = consolidate_market_sentiment_data(crew_data)
        assert result["aggregated_scores"]["total_sources"] == 1


class TestConsolidateTickerValidationData:
    """Tests for consolidate_ticker_validation_data function."""

    def test_should_return_empty_validation_for_empty_input(self):
        """Test that empty input returns default validation structure."""
        result = consolidate_ticker_validation_data({})
        assert result["validation_summary"]["total_symbols"] == 0
        assert result["validated_tickers"] == []
        assert result["validated_etfs"] == []
        assert result["validated_cryptos"] == []

    def test_should_consolidate_stock_validation(self):
        """Test consolidation of stock ticker validation."""
        crew_data = {
            "stock": {
                "validated_tickers": [
                    {"symbol": "AAPL", "is_valid": True, "company_name": "Apple Inc."},
                    {"symbol": "GOOGL", "is_valid": True, "company_name": "Alphabet Inc."},
                ]
            }
        }
        result = consolidate_ticker_validation_data(crew_data)
        assert result["validation_summary"]["total_symbols"] == 2
        assert result["validation_summary"]["valid_symbols"] == 2
        assert result["validation_summary"]["validation_rate"] == 100.0
        assert len(result["validated_tickers"]) == 2

    def test_should_consolidate_etf_validation(self):
        """Test consolidation of ETF validation."""
        crew_data = {
            "etf": {
                "validated_etfs": [
                    {"symbol": "SPY", "is_valid": True},
                    {"symbol": "QQQ", "is_valid": True},
                ]
            }
        }
        result = consolidate_ticker_validation_data(crew_data)
        assert len(result["validated_etfs"]) == 2

    def test_should_consolidate_crypto_validation(self):
        """Test consolidation of crypto symbol validation."""
        crew_data = {
            "crypto": {
                "validated_symbols": [
                    {"symbol": "BTC", "is_valid": True},
                    {"symbol": "ETH", "is_valid": True},
                ]
            }
        }
        result = consolidate_ticker_validation_data(crew_data)
        assert len(result["validated_cryptos"]) == 2

    def test_should_track_failed_validations(self):
        """Test tracking of failed validations."""
        crew_data = {
            "stock": {
                "validated_tickers": [
                    {
                        "symbol": "INVALID",
                        "is_valid": False,
                        "validation_errors": ["Symbol not found"],
                        "alternative_suggestions": ["AAPL", "AMZN"],
                    }
                ]
            }
        }
        result = consolidate_ticker_validation_data(crew_data)
        assert result["validation_summary"]["invalid_symbols"] == 1
        assert len(result["failed_validations"]) == 1
        assert "recovery_suggestions" in result["failed_validations"][0]

    def test_should_calculate_validation_rate(self):
        """Test calculation of validation rate."""
        crew_data = {
            "stock": {
                "validated_tickers": [
                    {"symbol": "AAPL", "is_valid": True},
                    {"symbol": "INVALID", "is_valid": False},
                ]
            }
        }
        result = consolidate_ticker_validation_data(crew_data)
        assert result["validation_summary"]["validation_rate"] == 50.0

    def test_should_skip_non_dict_validations(self):
        """Test that non-dict validations are skipped."""
        crew_data = {
            "stock": {
                "validated_tickers": [
                    {"symbol": "AAPL", "is_valid": True},
                    "invalid_entry",
                    None,
                ]
            }
        }
        result = consolidate_ticker_validation_data(crew_data)
        assert result["validation_summary"]["total_symbols"] == 1

    def test_should_standardize_validation_format(self):
        """Test standardization of validation format."""
        crew_data = {
            "stock": {
                "validated_tickers": [
                    {
                        "symbol": "AAPL",
                        "is_valid": True,
                        "full_name": "Apple Inc.",  # Alternative field name
                    }
                ]
            }
        }
        result = consolidate_ticker_validation_data(crew_data)
        validation = result["validated_tickers"][0]
        assert validation["company_name"] == "Apple Inc."
        assert validation["crew_source"] == "stock"


class TestGenerateCoreAnalysisSummary:
    """Tests for generate_core_analysis_summary function."""

    def test_should_return_summary_for_empty_input(self):
        """Test that empty input returns basic summary structure."""
        result = generate_core_analysis_summary({}, max_age_hours=24)
        assert result["total_crews"] == 0
        assert result["available_crews"] == []
        assert result["data_freshness_hours"] == 24

    def test_should_analyze_crew_coverage(self):
        """Test analysis of crew coverage."""
        data = {
            "stock": {
                "analysis": "Stock analysis text",
                "recommendations": ["buy", "hold"],
                "risk_assessment": {"level": "low"},
            }
        }
        result = generate_core_analysis_summary(data, max_age_hours=24)
        assert "stock" in result["analysis_coverage"]
        coverage = result["analysis_coverage"]["stock"]
        assert coverage["has_analysis"] is True
        assert coverage["has_recommendations"] is True
        assert coverage["has_risk_assessment"] is True

    def test_should_calculate_data_quality_indicators(self):
        """Test calculation of data quality indicators."""
        data = {
            "stock": {
                "analysis": "text",
                "recommendations": ["buy"],
            },
            "etf": {
                "analysis": "text",
            },
        }
        result = generate_core_analysis_summary(data, max_age_hours=24)
        indicators = result["data_quality_indicators"]
        assert indicators["crews_with_analysis"] == 2
        assert indicators["crews_with_recommendations"] == 1

    def test_should_extract_key_insights(self):
        """Test extraction of key insights from crews."""
        data = {
            "stock": {
                "analysis": {"summary": "Market is bullish"},
                "recommendations": ["buy", "hold", "sell"],
            }
        }
        result = generate_core_analysis_summary(data, max_age_hours=24)
        assert len(result["key_insights"]) > 0

    def test_should_identify_cross_crew_correlations(self):
        """Test identification of cross-crew correlations."""
        data = {
            "stock": {"symbols": ["AAPL", "GOOGL"]},
            "etf": {"tickers": ["AAPL", "SPY"]},
        }
        result = generate_core_analysis_summary(data, max_age_hours=24)
        correlations = result["cross_crew_correlations"]
        # AAPL appears in both crews
        common = correlations["common_symbols"]
        assert any(s["symbol"] == "AAPL" for s in common)

    def test_should_skip_non_dict_crew_data(self):
        """Test that non-dict crew data is skipped."""
        data = {
            "stock": {"analysis": "text"},
            "invalid": "not a dict",
        }
        result = generate_core_analysis_summary(data, max_age_hours=24)
        assert "stock" in result["analysis_coverage"]
        assert "invalid" not in result["analysis_coverage"]


class TestCalculateDataCompleteness:
    """Tests for _calculate_data_completeness function."""

    def test_should_return_zero_for_empty_data(self):
        """Test that empty data returns 0 completeness."""
        result = _calculate_data_completeness({})
        assert result == 0.0

    def test_should_return_full_completeness_for_all_fields(self):
        """Test that all expected fields returns 1.0 completeness."""
        data = {
            "analysis": "text",
            "recommendations": ["buy"],
            "risk_assessment": {"level": "low"},
            "technical_analysis": {"rsi": 50},
            "market_data": {"price": 100},
        }
        result = _calculate_data_completeness(data)
        assert result == 1.0

    def test_should_return_partial_completeness(self):
        """Test that partial data returns partial completeness."""
        data = {
            "analysis": "text",
            "recommendations": ["buy"],
        }
        result = _calculate_data_completeness(data)
        assert result == 0.4  # 2 out of 5 fields


class TestExtractKeyInsights:
    """Tests for _extract_key_insights function."""

    def test_should_return_empty_for_no_insights(self):
        """Test that empty data returns no insights."""
        result = _extract_key_insights("stock", {})
        assert result == []

    def test_should_extract_string_analysis_insight(self):
        """Test extraction of string analysis insight."""
        data = {"analysis": "A" * 100}  # Long enough string
        result = _extract_key_insights("stock", data)
        assert len(result) == 1
        assert "stock:" in result[0]

    def test_should_extract_dict_analysis_insight(self):
        """Test extraction of dict analysis insight with summary."""
        data = {"analysis": {"summary": "Market is bullish"}}
        result = _extract_key_insights("stock", data)
        assert len(result) == 1
        assert "Market is bullish" in result[0]

    def test_should_extract_recommendations_count(self):
        """Test extraction of recommendations count."""
        data = {"recommendations": ["buy", "hold", "sell"]}
        result = _extract_key_insights("stock", data)
        assert len(result) == 1
        assert "3 recommendations" in result[0]

    def test_should_skip_short_analysis_string(self):
        """Test that short analysis strings are skipped."""
        data = {"analysis": "short"}
        result = _extract_key_insights("stock", data)
        assert len(result) == 0


class TestIdentifyCrossCrewCorrelations:
    """Tests for _identify_cross_crew_correlations function."""

    def test_should_return_empty_correlations_for_empty_input(self):
        """Test that empty input returns empty correlations."""
        result = _identify_cross_crew_correlations({})
        assert result["common_symbols"] == []

    def test_should_identify_common_symbols(self):
        """Test identification of symbols common to multiple crews."""
        data = {
            "stock": {"symbols": ["AAPL", "GOOGL"]},
            "etf": {"symbols": ["AAPL", "SPY"]},
        }
        result = _identify_cross_crew_correlations(data)
        common = result["common_symbols"]
        assert len(common) == 1
        assert common[0]["symbol"] == "AAPL"
        assert common[0]["coverage"] == 2

    def test_should_handle_tickers_field(self):
        """Test handling of 'tickers' field in addition to 'symbols'."""
        data = {
            "stock": {"tickers": ["AAPL"]},
            "etf": {"tickers": ["AAPL"]},
        }
        result = _identify_cross_crew_correlations(data)
        assert len(result["common_symbols"]) == 1

    def test_should_not_report_unique_symbols(self):
        """Test that unique symbols are not reported as common."""
        data = {
            "stock": {"symbols": ["AAPL"]},
            "etf": {"symbols": ["SPY"]},
        }
        result = _identify_cross_crew_correlations(data)
        assert len(result["common_symbols"]) == 0


class TestCreateErrorResponseForSentiment:
    """Tests for create_error_response_for_sentiment function."""

    def test_should_create_error_response_with_message(self):
        """Test creation of error response with custom message."""
        result = create_error_response_for_sentiment("Test error message")
        assert result["error"] == "Test error message"
        assert result["data_quality"] == "ERROR"
        assert result["aggregated_scores"]["total_sources"] == 0

    def test_should_include_timestamp(self):
        """Test that error response includes timestamp."""
        result = create_error_response_for_sentiment("error")
        assert "consolidation_timestamp" in result
        assert isinstance(result["consolidation_timestamp"], datetime)

    def test_should_have_empty_collections(self):
        """Test that error response has empty collections."""
        result = create_error_response_for_sentiment("error")
        assert result["top_sources"] == []
        assert result["crew_sentiments"] == {}


class TestCreateErrorResponseForTickerValidation:
    """Tests for create_error_response_for_ticker_validation function."""

    def test_should_create_error_response_with_message(self):
        """Test creation of error response with custom message."""
        result = create_error_response_for_ticker_validation("Test error message")
        assert result["error"] == "Test error message"
        assert result["validation_summary"]["validation_rate"] == 0.0

    def test_should_include_timestamp(self):
        """Test that error response includes timestamp."""
        result = create_error_response_for_ticker_validation("error")
        assert "consolidation_timestamp" in result
        assert isinstance(result["consolidation_timestamp"], datetime)

    def test_should_have_empty_validation_lists(self):
        """Test that error response has empty validation lists."""
        result = create_error_response_for_ticker_validation("error")
        assert result["validated_tickers"] == []
        assert result["validated_etfs"] == []
        assert result["validated_cryptos"] == []
        assert result["failed_validations"] == []

    def test_should_have_zero_summary_values(self):
        """Test that error response has zero summary values."""
        result = create_error_response_for_ticker_validation("error")
        summary = result["validation_summary"]
        assert summary["total_symbols"] == 0
        assert summary["valid_symbols"] == 0
        assert summary["invalid_symbols"] == 0
