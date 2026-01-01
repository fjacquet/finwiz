"""
Data transformation utilities for crew data processing.

This module contains utilities for transforming and serializing crew data
for compatibility with CrewAI and other systems.
"""

from datetime import datetime
from typing import Any, cast


def serialize_datetime_objects(obj: Any, _seen: set[int] | None = None) -> Any:
    """
    Recursively serialize datetime objects and other non-serializable types to CrewAI-compatible formats.

    This is required for CrewAI compatibility as it only accepts
    str, int, float, bool, dict, and list types in inputs.

    Args:
        obj: Object that may contain datetime objects or other non-serializable types
        _seen: Set to track visited objects to prevent infinite recursion

    Returns:
        Object with all non-serializable types converted to compatible formats

    """
    if _seen is None:
        _seen = set()

    # Prevent infinite recursion
    obj_id = id(obj)
    if obj_id in _seen:
        return f"<circular reference to {type(obj).__name__}>"

    # For basic types that CrewAI accepts, return as-is
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj

    # Add to seen set for complex objects
    _seen.add(obj_id)

    try:
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: serialize_datetime_objects(value, _seen) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [serialize_datetime_objects(item, _seen) for item in obj]
        elif isinstance(obj, tuple):
            return [serialize_datetime_objects(item, _seen) for item in obj]
        elif isinstance(obj, set):
            return [serialize_datetime_objects(item, _seen) for item in obj]
        elif hasattr(obj, "items") and callable(getattr(obj, "items")):
            # Handle mappingproxy and other dict-like objects
            return {key: serialize_datetime_objects(value, _seen) for key, value in obj.items()}
        elif hasattr(obj, "model_dump"):
            # Pydantic v2 model
            return serialize_datetime_objects(obj.model_dump(), _seen)
        elif hasattr(obj, "dict"):
            # Pydantic v1 model
            return serialize_datetime_objects(obj.dict(), _seen)
        elif hasattr(obj, "__dict__"):
            # Generic object with __dict__ - but avoid certain types
            if type(obj).__name__ in ["CrewDataAccessor", "CrewDataIntegrationManager", "APlusDataExtractor"]:
                return f"<{type(obj).__name__} instance>"
            return serialize_datetime_objects(obj.__dict__, _seen)
        elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
            # Handle other iterable types (but not strings/bytes)
            try:
                return [serialize_datetime_objects(item, _seen) for item in obj]
            except (TypeError, RecursionError):
                # If iteration fails, convert to string
                return str(obj)
        else:
            # Convert other types to string representation
            return str(obj)
    finally:
        # Remove from seen set when done processing
        _seen.discard(obj_id)


def consolidate_market_sentiment_data(crew_data_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """
    Consolidate market sentiment data from multiple crew outputs.

    Args:
        crew_data_map: Dictionary mapping crew names to their data

    Returns:
        Dictionary containing consolidated sentiment data

    """
    consolidated_sentiment = {
        "aggregated_scores": {"positive": 0.0, "neutral": 0.0, "negative": 0.0, "total_sources": 0},
        "top_sources": [],
        "crew_sentiments": {},
        "data_quality": "HIGH",
        "consolidation_timestamp": datetime.now(),
    }

    all_sources = []
    total_positive = 0.0
    total_neutral = 0.0
    total_negative = 0.0
    total_weight = 0.0

    # Get sentiment data from each crew
    crews_with_sentiment = ["stock", "crypto"]  # ETF typically doesn't have sentiment

    for crew_name in crews_with_sentiment:
        crew_data = crew_data_map.get(crew_name)
        if not crew_data:
            continue

        # Extract sentiment data based on crew structure
        crew_sentiments = []
        if crew_name == "stock" and "market_sentiments" in crew_data:
            crew_sentiments = crew_data["market_sentiments"]
        elif crew_name == "crypto" and "market_analysis" in crew_data:
            # Extract sentiment from crypto market analysis
            market_analysis = crew_data["market_analysis"]
            if isinstance(market_analysis, list):
                for analysis in market_analysis:
                    if "sentiment" in analysis:
                        crew_sentiments.append(analysis["sentiment"])
            elif isinstance(market_analysis, dict) and "sentiment" in market_analysis:
                crew_sentiments.append(market_analysis["sentiment"])

        if not crew_sentiments:
            continue

        # Process sentiment data for this crew
        crew_sentiment_summary = {"positive": 0.0, "neutral": 0.0, "negative": 0.0, "source_count": 0, "sources": []}

        for sentiment in crew_sentiments:
            if not isinstance(sentiment, dict):
                continue

            # Extract sentiment scores (normalize different formats)
            pos_score = sentiment.get("positive", sentiment.get("positive_score", 0.0))
            neu_score = sentiment.get("neutral", sentiment.get("neutral_score", 0.0))
            neg_score = sentiment.get("negative", sentiment.get("negative_score", 0.0))

            # Normalize scores if they're percentages
            if pos_score > 1.0 or neu_score > 1.0 or neg_score > 1.0:
                total_score = pos_score + neu_score + neg_score
                if total_score > 0:
                    pos_score /= total_score
                    neu_score /= total_score
                    neg_score /= total_score

            crew_sentiment_summary["positive"] += pos_score
            crew_sentiment_summary["neutral"] += neu_score
            crew_sentiment_summary["negative"] += neg_score
            crew_sentiment_summary["source_count"] += 1

            # Collect source information
            source_info = {
                "crew": crew_name,
                "url": sentiment.get("source_url", sentiment.get("url", "")),
                "date": sentiment.get("date", sentiment.get("published_date", "")),
                "source_name": sentiment.get("source", sentiment.get("source_name", f"{crew_name}_analysis")),
                "sentiment_score": pos_score - neg_score,  # Net sentiment
                "confidence": sentiment.get("confidence", 0.5),
            }

            all_sources.append(source_info)
            cast(list, crew_sentiment_summary["sources"]).append(source_info)

        # Average the crew sentiment scores
        if crew_sentiment_summary["source_count"] > 0:
            count = crew_sentiment_summary["source_count"]
            crew_sentiment_summary["positive"] /= count
            crew_sentiment_summary["neutral"] /= count
            crew_sentiment_summary["negative"] /= count

            # Add to overall totals (weight by source count)
            weight = count
            total_positive += crew_sentiment_summary["positive"] * weight
            total_neutral += crew_sentiment_summary["neutral"] * weight
            total_negative += crew_sentiment_summary["negative"] * weight
            total_weight += weight

        consolidated_sentiment["crew_sentiments"][crew_name] = crew_sentiment_summary

    # Calculate overall aggregated scores
    if total_weight > 0:
        consolidated_sentiment["aggregated_scores"]["positive"] = total_positive / total_weight
        consolidated_sentiment["aggregated_scores"]["neutral"] = total_neutral / total_weight
        consolidated_sentiment["aggregated_scores"]["negative"] = total_negative / total_weight
        consolidated_sentiment["aggregated_scores"]["total_sources"] = len(all_sources)

    # Get top 3 sources by confidence and sentiment strength
    if all_sources:
        # Sort by confidence and absolute sentiment score
        sorted_sources = sorted(all_sources, key=lambda x: (x["confidence"], abs(x["sentiment_score"])), reverse=True)
        consolidated_sentiment["top_sources"] = sorted_sources[:3]

    # Assess data quality
    if len(all_sources) >= 5:
        consolidated_sentiment["data_quality"] = "HIGH"
    elif len(all_sources) >= 2:
        consolidated_sentiment["data_quality"] = "MEDIUM"
    elif len(all_sources) >= 1:
        consolidated_sentiment["data_quality"] = "LOW"
    else:
        consolidated_sentiment["data_quality"] = "INSUFFICIENT"

    return consolidated_sentiment


def consolidate_ticker_validation_data(crew_data_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """
    Consolidate ticker validation results from multiple crew outputs.

    Args:
        crew_data_map: Dictionary mapping crew names to their data

    Returns:
        Dictionary containing consolidated ticker validation

    """
    consolidated_validation = {
        "validated_tickers": [],
        "validated_etfs": [],
        "validated_cryptos": [],
        "validation_summary": {"total_symbols": 0, "valid_symbols": 0, "invalid_symbols": 0, "validation_rate": 0.0},
        "failed_validations": [],
        "consolidation_timestamp": datetime.now(),
    }

    # Get validation data from each crew
    crew_mappings = {
        "stock": ("validated_tickers", "validated_tickers"),
        "etf": ("validated_etfs", "validated_etfs"),
        "crypto": ("validated_symbols", "validated_cryptos"),
    }

    total_symbols = 0
    valid_symbols = 0

    for crew_name, (source_key, target_key) in crew_mappings.items():
        crew_data = crew_data_map.get(crew_name)
        if not crew_data:
            continue

        # Extract validation data
        validation_data = crew_data.get(source_key, [])
        if not validation_data:
            continue

        # Process validation results
        for validation in validation_data:
            if not isinstance(validation, dict):
                continue

            total_symbols += 1

            # Standardize validation format
            standardized_validation = {
                "symbol": validation.get("symbol", ""),
                "is_valid": validation.get("is_valid", False),
                "validation_source": validation.get("validation_source", f"{crew_name}_crew"),
                "validation_timestamp": validation.get("validation_timestamp", datetime.now().isoformat()),
                "crew_source": crew_name,
                "market": validation.get("market", ""),
                "sector": validation.get("sector", ""),
                "company_name": validation.get("company_name", validation.get("full_name", "")),
                "validation_errors": validation.get("validation_errors", []),
                "alternative_suggestions": validation.get("alternative_suggestions", []),
            }

            # Add to appropriate category
            cast(list, consolidated_validation[target_key]).append(standardized_validation)

            if standardized_validation["is_valid"]:
                valid_symbols += 1
            else:
                # Add to failed validations with recovery suggestions
                failed_validation = {
                    "symbol": standardized_validation["symbol"],
                    "crew": crew_name,
                    "errors": standardized_validation["validation_errors"],
                    "alternatives": standardized_validation["alternative_suggestions"],
                    "recovery_suggestions": [
                        f"Verify {standardized_validation['symbol']} symbol spelling",
                        f"Check if {standardized_validation['symbol']} is actively traded",
                        "Consider using alternative symbols if available",
                    ],
                }

                if standardized_validation["alternative_suggestions"]:
                    failed_validation["recovery_suggestions"].append(f"Try alternatives: {', '.join(standardized_validation['alternative_suggestions'][:3])}")

                cast(list, consolidated_validation["failed_validations"]).append(failed_validation)

    # Calculate validation summary
    consolidated_validation["validation_summary"] = {
        "total_symbols": total_symbols,
        "valid_symbols": valid_symbols,
        "invalid_symbols": total_symbols - valid_symbols,
        "validation_rate": (valid_symbols / total_symbols * 100) if total_symbols > 0 else 0.0,
    }

    return consolidated_validation


def generate_core_analysis_summary(consolidated_data: dict[str, Any], max_age_hours: int) -> dict[str, Any]:
    """
    Generate a summary of core analysis results for easy consumption.

    Args:
        consolidated_data: Consolidated crew data
        max_age_hours: Maximum acceptable age in hours

    Returns:
        Dictionary containing core analysis summary

    """
    summary = {
        "analysis_timestamp": datetime.now(),
        "data_freshness_hours": max_age_hours,
        "available_crews": list(consolidated_data.keys()),
        "total_crews": len(consolidated_data),
        "analysis_coverage": {},
        "key_insights": [],
        "data_quality_indicators": {},
        "cross_crew_correlations": {},
    }

    # Analyze coverage by crew
    for crew_name, crew_data in consolidated_data.items():
        if not isinstance(crew_data, dict):
            continue

        coverage = {
            "data_points": len(crew_data),
            "has_analysis": bool(crew_data.get("analysis", crew_data.get("market_analysis"))),
            "has_recommendations": bool(crew_data.get("recommendations", crew_data.get("investment_recommendations"))),
            "has_risk_assessment": bool(crew_data.get("risk_assessment", crew_data.get("risk_analysis"))),
            "has_technical_indicators": bool(crew_data.get("technical_analysis", crew_data.get("technical_indicators"))),
            "data_completeness": _calculate_data_completeness(crew_data),
        }

        summary["analysis_coverage"][crew_name] = coverage

        # Extract key insights
        insights = _extract_key_insights(crew_name, crew_data)
        cast(list, summary["key_insights"]).extend(insights)

    # Calculate overall data quality indicators
    analysis_coverage = cast(dict[str, Any], summary["analysis_coverage"])
    summary["data_quality_indicators"] = {
        "overall_completeness": sum(c["data_completeness"] for c in analysis_coverage.values()) / max(len(analysis_coverage), 1),
        "crews_with_analysis": sum(1 for c in analysis_coverage.values() if c["has_analysis"]),
        "crews_with_recommendations": sum(1 for c in analysis_coverage.values() if c["has_recommendations"]),
        "crews_with_risk_assessment": sum(1 for c in analysis_coverage.values() if c["has_risk_assessment"]),
        "total_data_points": sum(c["data_points"] for c in analysis_coverage.values()),
    }

    # Identify cross-crew correlations
    summary["cross_crew_correlations"] = _identify_cross_crew_correlations(consolidated_data)

    return summary


def _calculate_data_completeness(crew_data: dict[str, Any]) -> float:
    """Calculate data completeness score for crew data."""
    expected_fields = ["analysis", "recommendations", "risk_assessment", "technical_analysis", "market_data"]
    present_fields = sum(1 for field in expected_fields if crew_data.get(field))
    return present_fields / len(expected_fields)


def _extract_key_insights(crew_name: str, crew_data: dict[str, Any]) -> list[str]:
    """Extract key insights from crew data."""
    insights = []

    # Extract analysis insights
    if "analysis" in crew_data:
        analysis = crew_data["analysis"]
        if isinstance(analysis, str) and len(analysis) > 50:
            insights.append(f"{crew_name}: {analysis[:100]}...")
        elif isinstance(analysis, dict) and "summary" in analysis:
            insights.append(f"{crew_name}: {analysis['summary']}")

    # Extract recommendation insights
    if "recommendations" in crew_data:
        recommendations = crew_data["recommendations"]
        if isinstance(recommendations, list) and recommendations:
            insights.append(f"{crew_name}: {len(recommendations)} recommendations available")

    return insights


def _identify_cross_crew_correlations(consolidated_data: dict[str, Any]) -> dict[str, Any]:
    """Identify correlations between crew analyses."""
    correlations = {
        "common_symbols": [],
        "sentiment_alignment": {},
        "risk_consensus": {},
        "recommendation_overlap": {},
    }

    # Find common symbols across crews
    all_symbols = set()
    crew_symbols = {}

    for crew_name, crew_data in consolidated_data.items():
        symbols = set()
        if "symbols" in crew_data:
            symbols.update(crew_data["symbols"])
        if "tickers" in crew_data:
            symbols.update(crew_data["tickers"])

        crew_symbols[crew_name] = symbols
        all_symbols.update(symbols)

    # Find symbols that appear in multiple crews
    common_symbols = cast(list, correlations["common_symbols"])
    for symbol in all_symbols:
        crews_with_symbol = [crew for crew, symbols in crew_symbols.items() if symbol in symbols]
        if len(crews_with_symbol) > 1:
            common_symbols.append({"symbol": symbol, "crews": crews_with_symbol, "coverage": len(crews_with_symbol)})

    return correlations


def create_error_response_for_sentiment(error_message: str) -> dict[str, Any]:
    """
    Create standardized error response for sentiment consolidation failures.

    Args:
        error_message: The error message to include

    Returns:
        Dictionary containing error response for sentiment data

    """
    return {
        "aggregated_scores": {"positive": 0.0, "neutral": 0.0, "negative": 0.0, "total_sources": 0},
        "top_sources": [],
        "crew_sentiments": {},
        "data_quality": "ERROR",
        "consolidation_timestamp": datetime.now(),
        "error": error_message,
    }


def create_error_response_for_ticker_validation(error_message: str) -> dict[str, Any]:
    """
    Create standardized error response for ticker validation failures.

    Args:
        error_message: The error message to include

    Returns:
        Dictionary containing error response for ticker validation

    """
    return {
        "validated_tickers": [],
        "validated_etfs": [],
        "validated_cryptos": [],
        "validation_summary": {"total_symbols": 0, "valid_symbols": 0, "invalid_symbols": 0, "validation_rate": 0.0},
        "failed_validations": [],
        "consolidation_timestamp": datetime.now(),
        "error": error_message,
    }
