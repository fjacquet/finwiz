"""
Core Analysis Error Handler.

Provides comprehensive error handling and graceful degradation for core analysis crews.
Implements fallback strategies, cached data usage, and system resilience patterns.
"""

from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.tools.logger import get_logger
from finwiz.config.features.flags import FallbackStrategy, get_feature_flags


class CrewFailureType(str):
    """Types of crew failures."""

    INITIALIZATION_ERROR = "initialization_error"
    EXECUTION_ERROR = "execution_error"
    TIMEOUT_ERROR = "timeout_error"
    API_ERROR = "api_error"
    VALIDATION_ERROR = "validation_error"
    RESOURCE_ERROR = "resource_error"


class FallbackResponse(BaseModel):
    """Response from fallback strategy execution."""

    success: bool = Field(..., description="Whether fallback was successful")
    data: dict[str, Any] | None = Field(None, description="Fallback data if available")
    message: str = Field(..., description="Status message")
    degraded_functionality: list[str] = Field(default_factory=list, description="List of degraded features")
    cache_used: bool = Field(False, description="Whether cached data was used")
    fallback_strategy: str = Field(..., description="Strategy used for fallback")


class CrewErrorContext(BaseModel):
    """Context information for crew errors."""

    crew_name: str = Field(..., description="Name of the failed crew")
    error_type: str = Field(..., description="Type of error that occurred")
    error_message: str = Field(..., description="Error message")
    timestamp: datetime = Field(default_factory=datetime.now, description="When error occurred")
    retry_count: int = Field(0, description="Number of retries attempted")
    execution_time: float = Field(0.0, description="Time spent before failure")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Inputs that caused the error")


class CoreAnalysisErrorHandler:
    """
    Handles errors in core analysis crews with graceful degradation.

    Provides fallback strategies including cached data usage, reduced functionality,
    and system resilience patterns to ensure the system continues operating
    even when individual crews fail.
    """

    def __init__(self, integration_manager: CrewDataIntegrationManager) -> None:
        """
        Initialize the error handler.

        Args:
            integration_manager: Data integration manager for accessing cached data

        """
        self.integration_manager = integration_manager
        self.feature_flags = get_feature_flags()
        self.logger = get_logger(__name__)

        # Initialize fallback strategies
        self.fallback_strategies = self._initialize_fallback_strategies()

        # Track error history for circuit breaker patterns
        self.error_history: dict[str, list[CrewErrorContext]] = {}

        # Cache acceptable age for fallback data (in hours)
        self.fallback_cache_max_age = 72  # 3 days for emergency fallback

        self.logger.info("CoreAnalysisErrorHandler initialized")

    def _initialize_fallback_strategies(self) -> dict[str, dict[str, Any]]:
        """Initialize fallback strategies for each crew type."""
        return {
            "stock": {
                "alternative_sources": ["yahoo_finance", "alpha_vantage"],
                "cached_data_acceptable": True,
                "reduced_functionality": ["basic_metrics", "price_data"],
                "default_recommendation": "HOLD",
                "default_risk_score": 5,
                "emergency_message": "Stock analysis temporarily unavailable - using cached data",
            },
            "etf": {
                "alternative_sources": ["yahoo_finance", "morningstar"],
                "cached_data_acceptable": True,
                "reduced_functionality": ["basic_info", "expense_ratio"],
                "default_recommendation": "HOLD",
                "default_risk_score": 4,
                "emergency_message": "ETF analysis temporarily unavailable - using cached data",
            },
            "crypto": {
                "alternative_sources": ["coinmarketcap", "kraken"],
                "cached_data_acceptable": True,
                "reduced_functionality": ["price_data", "market_cap"],
                "default_recommendation": "HOLD",
                "default_risk_score": 8,
                "emergency_message": "Crypto analysis temporarily unavailable - using cached data",
            },
        }

    def handle_crew_failure(self, crew_name: str, error: Exception, inputs: dict[str, Any], execution_time: float = 0.0) -> FallbackResponse:
        """
        Handle crew failure with appropriate fallback strategy.

        Args:
            crew_name: Name of the failed crew
            error: Exception that caused the failure
            inputs: Inputs that were passed to the crew
            execution_time: Time spent before failure

        Returns:
            FallbackResponse with fallback data and status

        """
        # Create error context
        error_context = CrewErrorContext(
            crew_name=crew_name,
            error_type=self._classify_error(error),
            error_message=str(error),
            execution_time=execution_time,
            inputs=inputs,
        )

        # Log the error
        self.logger.error(
            f"Crew failure detected: {crew_name}",
            extra={
                "crew_name": crew_name,
                "error_type": error_context.error_type,
                "error_message": error_context.error_message,
                "execution_time": execution_time,
            },
            exc_info=True,
        )

        # Record error for circuit breaker tracking
        self._record_error(error_context)

        # Get fallback strategy from feature flags
        fallback_strategy = self.feature_flags.get_fallback_strategy(f"{crew_name}_analysis")

        # Execute appropriate fallback strategy
        if fallback_strategy == FallbackStrategy.CACHED_ONLY:
            return self._try_cached_data_fallback(crew_name, error_context)
        elif fallback_strategy == FallbackStrategy.REDUCED_FUNCTIONALITY:
            return self._try_reduced_functionality_fallback(crew_name, error_context)
        elif fallback_strategy == FallbackStrategy.DEFAULT_VALUES:
            return self._try_default_values_fallback(crew_name, error_context)
        elif fallback_strategy == FallbackStrategy.RETRY_WITH_BACKOFF:
            return self._try_retry_fallback(crew_name, error_context)
        else:
            return self._try_disable_fallback(crew_name, error_context)

    def _classify_error(self, error: Exception) -> str:
        """Classify the type of error for appropriate handling."""
        error_message = str(error).lower()

        if "timeout" in error_message or "timed out" in error_message:
            return CrewFailureType.TIMEOUT_ERROR
        elif "api" in error_message or "http" in error_message or "request" in error_message:
            return CrewFailureType.API_ERROR
        elif "validation" in error_message or "schema" in error_message:
            return CrewFailureType.VALIDATION_ERROR
        elif "memory" in error_message or "resource" in error_message:
            return CrewFailureType.RESOURCE_ERROR
        elif "initialization" in error_message or "import" in error_message:
            return CrewFailureType.INITIALIZATION_ERROR
        else:
            return CrewFailureType.EXECUTION_ERROR

    def _record_error(self, error_context: CrewErrorContext) -> None:
        """Record error for circuit breaker and analytics."""
        crew_name = error_context.crew_name

        if crew_name not in self.error_history:
            self.error_history[crew_name] = []

        self.error_history[crew_name].append(error_context)

        # Keep only recent errors (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.error_history[crew_name] = [ctx for ctx in self.error_history[crew_name] if ctx.timestamp > cutoff_time]

        # Record failure in feature flags for circuit breaker
        self.feature_flags.record_failure(f"{crew_name}_analysis")

    def _try_cached_data_fallback(self, crew_name: str, error_context: CrewErrorContext) -> FallbackResponse:
        """Try to use cached data as fallback."""
        self.logger.info(f"Attempting cached data fallback for {crew_name}")

        try:
            # Try to get cached data from integration manager
            cached_data = self.integration_manager.get_cached_crew_output(crew_name)

            if cached_data and self._is_cache_acceptable(cached_data, crew_name):
                self.logger.info(f"Using cached data for {crew_name} crew")

                # Enhance cached data with fallback metadata
                enhanced_data = self._enhance_cached_data(cached_data, error_context)

                return FallbackResponse(
                    success=True,
                    data=enhanced_data,
                    message=f"Using cached {crew_name} analysis due to crew failure",
                    degraded_functionality=["stale_data", "no_real_time_updates"],
                    cache_used=True,
                    fallback_strategy="cached_data",
                )
            else:
                self.logger.warning(f"No acceptable cached data for {crew_name}")
                return self._try_reduced_functionality_fallback(crew_name, error_context)

        except Exception as e:
            self.logger.error(f"Cached data fallback failed for {crew_name}: {e}")
            return self._try_default_values_fallback(crew_name, error_context)

    def _try_reduced_functionality_fallback(self, crew_name: str, error_context: CrewErrorContext) -> FallbackResponse:
        """Try reduced functionality fallback."""
        self.logger.info(f"Attempting reduced functionality fallback for {crew_name}")

        try:
            strategy = self.fallback_strategies.get(crew_name, {})
            reduced_features = strategy.get("reduced_functionality", [])

            # Create minimal analysis data
            fallback_data = {
                "crew_type": crew_name,
                "analysis_timestamp": datetime.now().isoformat(),
                "fallback_mode": True,
                "available_features": reduced_features,
                "ai_recommendation": strategy.get("default_recommendation", "HOLD"),
                "ai_reasoning": f"Analysis temporarily unavailable for {crew_name}. Using fallback recommendation.",
                "confidence_score": 0.3,  # Low confidence for fallback
                "risk_score": strategy.get("default_risk_score", 5),
                "risk_factors": [f"{crew_name} analysis unavailable", "Using fallback data"],
                "data_sources": ["fallback_system"],
                "validation_status": "fallback_mode",
                "error_context": {
                    "original_error": error_context.error_message,
                    "error_type": error_context.error_type,
                    "fallback_reason": "reduced_functionality",
                },
            }

            return FallbackResponse(
                success=True,
                data=fallback_data,
                message=f"Using reduced functionality for {crew_name} analysis",
                degraded_functionality=["limited_analysis", "low_confidence", "basic_metrics_only"],
                cache_used=False,
                fallback_strategy="reduced_functionality",
            )

        except Exception as e:
            self.logger.error(f"Reduced functionality fallback failed for {crew_name}: {e}")
            return self._try_default_values_fallback(crew_name, error_context)

    def _try_default_values_fallback(self, crew_name: str, error_context: CrewErrorContext) -> FallbackResponse:
        """Try default values fallback."""
        self.logger.info(f"Using default values fallback for {crew_name}")

        try:
            strategy = self.fallback_strategies.get(crew_name, {})

            # Create default analysis data
            default_data = {
                "crew_type": crew_name,
                "analysis_timestamp": datetime.now().isoformat(),
                "fallback_mode": True,
                "ai_recommendation": strategy.get("default_recommendation", "HOLD"),
                "ai_reasoning": strategy.get("emergency_message", f"{crew_name} analysis unavailable"),
                "confidence_score": 0.1,  # Very low confidence for defaults
                "risk_score": strategy.get("default_risk_score", 5),
                "risk_factors": [f"{crew_name} analysis failed", "Using default values"],
                "current_price": None,
                "price_target": None,
                "data_sources": ["default_values"],
                "validation_status": "default_fallback",
                "error_context": {
                    "original_error": error_context.error_message,
                    "error_type": error_context.error_type,
                    "fallback_reason": "default_values",
                },
            }

            return FallbackResponse(
                success=True,
                data=default_data,
                message=f"Using default values for {crew_name} analysis",
                degraded_functionality=["no_analysis", "default_values_only", "minimal_data"],
                cache_used=False,
                fallback_strategy="default_values",
            )

        except Exception as e:
            self.logger.error(f"Default values fallback failed for {crew_name}: {e}")
            return self._try_disable_fallback(crew_name, error_context)

    def _try_retry_fallback(self, crew_name: str, error_context: CrewErrorContext) -> FallbackResponse:
        """Try retry with backoff fallback (not implemented in this task)."""
        self.logger.info(f"Retry fallback not implemented for {crew_name}, using cached data")
        return self._try_cached_data_fallback(crew_name, error_context)

    def _try_disable_fallback(self, crew_name: str, error_context: CrewErrorContext) -> FallbackResponse:
        """Disable crew completely."""
        self.logger.warning(f"Disabling {crew_name} crew due to failure")

        return FallbackResponse(
            success=False,
            data=None,
            message=f"{crew_name} analysis disabled due to failure",
            degraded_functionality=["crew_disabled", "no_analysis"],
            cache_used=False,
            fallback_strategy="disable",
        )

    def _is_cache_acceptable(self, cached_data: dict[str, Any], crew_name: str) -> bool:
        """Check if cached data is acceptable for fallback use."""
        try:
            # Check if data has metadata
            metadata = cached_data.get("metadata", {})
            if not metadata:
                return False

            # Check data age
            stored_at_str = metadata.get("storage_timestamp")
            if stored_at_str:
                stored_at = datetime.fromisoformat(stored_at_str.replace("Z", "+00:00"))
                age_hours = (datetime.now() - stored_at).total_seconds() / 3600

                if age_hours > self.fallback_cache_max_age:
                    self.logger.warning(f"Cached data too old for {crew_name}: {age_hours:.1f}h")
                    return False

            # Check if data has essential fields
            essential_fields = ["raw_output", "tasks_output"]
            if not any(field in cached_data for field in essential_fields):
                self.logger.warning(f"Cached data missing essential fields for {crew_name}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking cache acceptability for {crew_name}: {e}")
            return False

    def _enhance_cached_data(self, cached_data: dict[str, Any], error_context: CrewErrorContext) -> dict[str, Any]:
        """Enhance cached data with fallback metadata."""
        enhanced_data = cached_data.copy()

        # Add fallback metadata
        if "metadata" not in enhanced_data:
            enhanced_data["metadata"] = {}

        enhanced_data["metadata"]["fallback_mode"] = True
        enhanced_data["metadata"]["fallback_timestamp"] = datetime.now().isoformat()
        enhanced_data["metadata"]["original_error"] = error_context.error_message
        enhanced_data["metadata"]["error_type"] = error_context.error_type
        enhanced_data["metadata"]["fallback_reason"] = "crew_failure"

        # Add warning to raw output if present
        if "raw_output" in enhanced_data:
            warning_prefix = f"[FALLBACK MODE] Using cached data due to {error_context.crew_name} crew failure. "
            enhanced_data["raw_output"] = warning_prefix + str(enhanced_data["raw_output"])

        return enhanced_data

    def get_error_summary(self, crew_name: str) -> dict[str, Any]:
        """Get error summary for a specific crew."""
        if crew_name not in self.error_history:
            return {"crew_name": crew_name, "error_count": 0, "recent_errors": []}

        errors = self.error_history[crew_name]
        recent_errors = errors[-5:]  # Last 5 errors

        return {
            "crew_name": crew_name,
            "error_count": len(errors),
            "recent_errors": [
                {
                    "error_type": err.error_type,
                    "error_message": err.error_message,
                    "timestamp": err.timestamp.isoformat(),
                    "execution_time": err.execution_time,
                }
                for err in recent_errors
            ],
            "most_common_error": self._get_most_common_error_type(errors),
            "error_rate": len(errors) / 24.0,  # Errors per hour over last 24h
        }

    def _get_most_common_error_type(self, errors: list[CrewErrorContext]) -> str:
        """Get the most common error type from error list."""
        if not errors:
            return "none"

        error_counts = {}
        for error in errors:
            error_type = error.error_type
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        return max(error_counts.items(), key=lambda x: x[1])[0]

    def get_system_health_status(self) -> dict[str, Any]:
        """Get overall system health status for core analysis crews."""
        crew_names = ["stock", "etf", "crypto"]
        health_status = {
            "overall_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "crew_status": {},
            "total_errors_24h": 0,
            "degraded_crews": [],
        }

        total_errors = 0
        degraded_crews = []

        for crew_name in crew_names:
            crew_errors = self.error_history.get(crew_name, [])
            error_count = len(crew_errors)
            total_errors += error_count

            crew_health = "healthy"
            if error_count > 10:  # More than 10 errors in 24h
                crew_health = "degraded"
                degraded_crews.append(crew_name)
            elif error_count > 20:  # More than 20 errors in 24h
                crew_health = "critical"

            health_status["crew_status"][crew_name] = {
                "status": crew_health,
                "error_count_24h": error_count,
                "last_error": crew_errors[-1].timestamp.isoformat() if crew_errors else None,
            }

        health_status["total_errors_24h"] = total_errors
        health_status["degraded_crews"] = degraded_crews

        # Determine overall status
        if any(status["status"] == "critical" for status in health_status["crew_status"].values()):
            health_status["overall_status"] = "critical"
        elif len(degraded_crews) >= 1:  # Changed from >= 2 to >= 1
            health_status["overall_status"] = "degraded"

        return health_status
