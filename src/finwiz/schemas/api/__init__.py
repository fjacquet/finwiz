"""
API schemas for FinWiz FastAPI endpoints.

This module contains Pydantic models for API request/response handling.
"""

from .models import (
    # Base API models
    APIResponse,
    # Batch processing API
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    BatchStatusResponse,
    # Configuration API
    ConfigurationUpdateRequest,
    ConfigurationUpdateResponse,
    # Crypto analysis API
    CryptoAnalysisRequest,
    CryptoAnalysisResponse,
    # Investment discovery API
    DiscoveryRequest,
    DiscoveryResponse,
    ErrorResponse,
    # ETF analysis API
    ETFAnalysisRequest,
    ETFAnalysisResponse,
    # Feedback API
    FeedbackSubmissionRequest,
    FeedbackSubmissionResponse,
    # Health check API
    HealthCheckResponse,
    # Monitoring API
    MonitoringAlert,
    MonitoringStatusRequest,
    MonitoringStatusResponse,
    # Portfolio analysis API
    PortfolioAnalysisRequest,
    PortfolioAnalysisResponse,
    # Portfolio rebalancing API
    RebalancingRequest,
    RebalancingResponse,
    # Search API
    SearchRequest,
    SearchResponse,
    SearchResult,
    # Stock analysis API
    StockAnalysisRequest,
    StockAnalysisResponse,
    ValidationErrorResponse,
)

__all__ = [
    # Base API models
    "APIResponse",
    "ErrorResponse",
    "ValidationErrorResponse",
    # Portfolio rebalancing API
    "RebalancingRequest",
    "RebalancingResponse",
    # Investment discovery API
    "DiscoveryRequest",
    "DiscoveryResponse",
    # Portfolio analysis API
    "PortfolioAnalysisRequest",
    "PortfolioAnalysisResponse",
    # Stock analysis API
    "StockAnalysisRequest",
    "StockAnalysisResponse",
    # ETF analysis API
    "ETFAnalysisRequest",
    "ETFAnalysisResponse",
    # Crypto analysis API
    "CryptoAnalysisRequest",
    "CryptoAnalysisResponse",
    # Monitoring API
    "MonitoringAlert",
    "MonitoringStatusRequest",
    "MonitoringStatusResponse",
    # Feedback API
    "FeedbackSubmissionRequest",
    "FeedbackSubmissionResponse",
    # Batch processing API
    "BatchAnalysisRequest",
    "BatchAnalysisResponse",
    "BatchStatusResponse",
    # Health check API
    "HealthCheckResponse",
    # Configuration API
    "ConfigurationUpdateRequest",
    "ConfigurationUpdateResponse",
    # Search API
    "SearchRequest",
    "SearchResult",
    "SearchResponse",
]
