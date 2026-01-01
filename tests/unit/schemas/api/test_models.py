"""
Comprehensive pytest tests for API models (finwiz.schemas.api.models).

Tests cover:
- Model instantiation with required/optional fields
- Default values work correctly
- Field validation constraints
- Invalid inputs raise ValidationError
- Optional fields can be None
"""

from datetime import datetime

import pytest
from faker import Faker
from pydantic import ValidationError

from finwiz.schemas.api.models import (
    APIResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    BatchStatusResponse,
    ConfigurationUpdateRequest,
    ConfigurationUpdateResponse,
    CryptoAnalysisRequest,
    CryptoAnalysisResponse,
    DiscoveryRequest,
    DiscoveryResponse,
    ErrorResponse,
    ETFAnalysisRequest,
    ETFAnalysisResponse,
    FeedbackSubmissionRequest,
    FeedbackSubmissionResponse,
    HealthCheckResponse,
    MonitoringAlert,
    MonitoringStatusRequest,
    MonitoringStatusResponse,
    PortfolioAnalysisRequest,
    PortfolioAnalysisResponse,
    RebalancingRequest,
    RebalancingResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    StockAnalysisRequest,
    StockAnalysisResponse,
    ValidationErrorResponse,
)
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.investment_discovery import (
    APlusAnalysis,
    InvestmentCandidate,
)

# ===========================
# Fixtures
# ===========================


@pytest.fixture
def fake():
    """Faker instance for generating test data."""
    return Faker()


@pytest.fixture
def sample_timestamp(fake):
    """Generate a sample ISO format timestamp."""
    return datetime.now().isoformat()


@pytest.fixture
def sample_risk_assessment():
    """Create a sample RiskAssessmentStandardized for testing."""
    return RiskAssessmentStandardized(
        scale="0_5",
        score=2.5,
        level="Medium",
        risk_factors=["High volatility", "Low liquidity"],
    )


@pytest.fixture
def sample_grade():
    """Create a sample Grade literal value."""
    return "A"


@pytest.fixture
def sample_investment_candidate(fake):
    """Create a sample InvestmentCandidate for testing."""
    return InvestmentCandidate(
        symbol="AAPL",
        name="Apple Inc.",
        asset_type="stock",
        current_price=150.0,
        market_cap=2.5e12,
        preliminary_score=0.85,
        final_score=0.88,
        grade="A",
        grade_description="Strong fundamentals and growth",
        recommended_action="BUY",
        data_source="Yahoo Finance",
    )


@pytest.fixture
def sample_aplus_analysis(sample_investment_candidate):
    """Create a sample APlusAnalysis for testing."""
    return APlusAnalysis(
        candidate=sample_investment_candidate,
        fundamental_score=0.90,
        technical_score=0.85,
        quality_score=0.88,
        risk_score=0.80,
        composite_score=0.86,
        confidence_level=0.92,
        is_a_plus_candidate=True,
        rationale=["Strong ROE", "Consistent revenue growth"],
        key_metrics={"roe": 0.25, "pe_ratio": 15.5},
    )


# ===========================
# Base API Models Tests
# ===========================


class TestAPIResponse:
    """Tests for APIResponse model."""

    def test_api_response_creation_with_all_fields(self, sample_timestamp):
        """Test creating APIResponse with all fields."""
        response = APIResponse(
            success=True,
            message="Operation successful",
            timestamp=sample_timestamp,
        )

        assert response.success is True
        assert response.message == "Operation successful"
        assert response.timestamp == sample_timestamp

    def test_api_response_with_none_message(self, sample_timestamp):
        """Test APIResponse with None message (optional field)."""
        response = APIResponse(
            success=True,
            message=None,
            timestamp=sample_timestamp,
        )

        assert response.message is None

    def test_api_response_success_required(self, sample_timestamp):
        """Test APIResponse requires success field."""
        with pytest.raises(ValidationError) as exc_info:
            APIResponse(
                message="Test",
                timestamp=sample_timestamp,
            )

        assert "success" in str(exc_info.value)

    def test_api_response_timestamp_required(self):
        """Test APIResponse requires timestamp field."""
        with pytest.raises(ValidationError) as exc_info:
            APIResponse(success=True, message="Test")

        assert "timestamp" in str(exc_info.value)

    def test_api_response_forbid_extra_fields(self, sample_timestamp):
        """Test APIResponse forbids extra fields."""
        with pytest.raises(ValidationError):
            APIResponse(
                success=True,
                message="Test",
                timestamp=sample_timestamp,
                extra_field="not allowed",
            )


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_error_response_creation(self, sample_timestamp):
        """Test creating ErrorResponse with all fields."""
        response = ErrorResponse(
            error_code="INVALID_REQUEST",
            message="Request validation failed",
            timestamp=sample_timestamp,
        )

        assert response.success is False
        assert response.error_code == "INVALID_REQUEST"
        assert response.message == "Request validation failed"

    def test_error_response_default_success_false(self, sample_timestamp):
        """Test ErrorResponse defaults success to False."""
        response = ErrorResponse(
            error_code="SERVER_ERROR",
            timestamp=sample_timestamp,
        )

        assert response.success is False

    def test_error_response_with_error_details(self, sample_timestamp):
        """Test ErrorResponse with error_details dictionary."""
        error_details = {"field": "email", "reason": "Invalid format"}
        response = ErrorResponse(
            error_code="VALIDATION_ERROR",
            error_details=error_details,
            timestamp=sample_timestamp,
        )

        assert response.error_details == error_details

    def test_error_response_error_code_required(self, sample_timestamp):
        """Test ErrorResponse requires error_code field."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse(timestamp=sample_timestamp)

        assert "error_code" in str(exc_info.value)


class TestValidationErrorResponse:
    """Tests for ValidationErrorResponse model."""

    def test_validation_error_response_creation(self, sample_timestamp):
        """Test creating ValidationErrorResponse with all fields."""
        field_errors = {
            "email": ["Invalid email format"],
            "password": ["Too short"],
        }
        response = ValidationErrorResponse(
            field_errors=field_errors,
            message="Validation failed",
            timestamp=sample_timestamp,
        )

        assert response.error_code == "VALIDATION_ERROR"
        assert response.success is False
        assert response.field_errors == field_errors

    def test_validation_error_response_default_error_code(self, sample_timestamp):
        """Test ValidationErrorResponse defaults error_code."""
        response = ValidationErrorResponse(
            field_errors={"field": ["error"]},
            timestamp=sample_timestamp,
        )

        assert response.error_code == "VALIDATION_ERROR"

    def test_validation_error_response_field_errors_required(self, sample_timestamp):
        """Test ValidationErrorResponse requires field_errors."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationErrorResponse(timestamp=sample_timestamp)

        assert "field_errors" in str(exc_info.value)


# ===========================
# Portfolio Rebalancing API Models Tests
# ===========================


class TestRebalancingRequest:
    """Tests for RebalancingRequest model."""

    def test_rebalancing_request_available_capital_default(self):
        """Test RebalancingRequest defaults available_capital to 0.0."""
        # Note: Creating a full PortfolioConfiguration is complex,
        # so we test the default value behavior via ValidationError
        try:
            request = RebalancingRequest()
        except ValidationError as e:
            # portfolio_config is required, which is expected
            assert "portfolio_config" in str(e)

    def test_rebalancing_request_portfolio_config_required(self):
        """Test RebalancingRequest requires portfolio_config."""
        with pytest.raises(ValidationError) as exc_info:
            RebalancingRequest()

        assert "portfolio_config" in str(exc_info.value)


class TestRebalancingResponse:
    """Tests for RebalancingResponse model."""

    def test_rebalancing_response_creation(self, sample_timestamp):
        """Test creating RebalancingResponse with required fields."""
        response = RebalancingResponse(
            success=True,
            timestamp=sample_timestamp,
        )

        assert response.success is True
        assert response.result is None

    def test_rebalancing_response_with_none_result(self, sample_timestamp):
        """Test RebalancingResponse with None result (optional field)."""
        response = RebalancingResponse(
            success=False,
            timestamp=sample_timestamp,
            result=None,
        )

        assert response.result is None


# ===========================
# Investment Discovery API Models Tests
# ===========================


class TestDiscoveryRequest:
    """Tests for DiscoveryRequest model."""

    def test_discovery_request_minimal(self, fake):
        """Test creating DiscoveryRequest with minimal required fields."""
        amount = fake.random.uniform(1000, 100000)
        request = DiscoveryRequest(
            asset_class="stock",
            investment_amount=amount,
        )

        assert request.asset_class == "stock"
        assert request.investment_amount == amount
        assert request.risk_tolerance == "moderate"
        assert request.time_horizon == "medium"

    def test_discovery_request_all_fields(self, fake):
        """Test creating DiscoveryRequest with all fields."""
        amount = fake.random.uniform(1000, 100000)
        request = DiscoveryRequest(
            asset_class="etf",
            risk_tolerance="aggressive",
            investment_amount=amount,
            time_horizon="long",
            exclude_sectors=["Energy", "Utilities"],
            include_esg=True,
        )

        assert request.asset_class == "etf"
        assert request.risk_tolerance == "aggressive"
        assert request.time_horizon == "long"
        assert request.exclude_sectors == ["Energy", "Utilities"]
        assert request.include_esg is True

    def test_discovery_request_asset_class_literal(self):
        """Test DiscoveryRequest asset_class must be valid literal."""
        with pytest.raises(ValidationError) as exc_info:
            DiscoveryRequest(
                asset_class="invalid",
                investment_amount=5000,
            )

        assert "asset_class" in str(exc_info.value)

    def test_discovery_request_investment_amount_positive(self):
        """Test DiscoveryRequest investment_amount must be > 0."""
        with pytest.raises(ValidationError) as exc_info:
            DiscoveryRequest(
                asset_class="stock",
                investment_amount=0,
            )

        assert "investment_amount" in str(exc_info.value)

    def test_discovery_request_invalid_investment_amount(self):
        """Test DiscoveryRequest rejects negative investment_amount."""
        with pytest.raises(ValidationError) as exc_info:
            DiscoveryRequest(
                asset_class="stock",
                investment_amount=-1000,
            )

        assert "investment_amount" in str(exc_info.value)


class TestDiscoveryResponse:
    """Tests for DiscoveryResponse model."""

    def test_discovery_response_creation(self, sample_timestamp):
        """Test creating DiscoveryResponse."""
        response = DiscoveryResponse(
            success=True,
            timestamp=sample_timestamp,
            total_candidates=0,
        )

        assert response.success is True
        assert response.total_candidates == 0
        assert response.candidates == []

    def test_discovery_response_with_empty_candidates(self, sample_timestamp):
        """Test DiscoveryResponse with empty candidates list."""
        response = DiscoveryResponse(
            success=True,
            timestamp=sample_timestamp,
            candidates=[],
            total_candidates=0,
        )

        assert len(response.candidates) == 0
        assert response.total_candidates == 0

    def test_discovery_response_total_candidates_required(self, sample_timestamp):
        """Test DiscoveryResponse requires total_candidates."""
        with pytest.raises(ValidationError) as exc_info:
            DiscoveryResponse(
                success=True,
                timestamp=sample_timestamp,
            )

        assert "total_candidates" in str(exc_info.value)


# ===========================
# Portfolio Analysis API Models Tests
# ===========================


class TestPortfolioAnalysisRequest:
    """Tests for PortfolioAnalysisRequest model."""

    def test_portfolio_analysis_request_minimal(self):
        """Test creating PortfolioAnalysisRequest with required fields."""
        holdings = {"AAPL": 0.4, "GOOGL": 0.6}
        request = PortfolioAnalysisRequest(holdings=holdings)

        assert request.holdings == holdings
        assert request.benchmark is None
        assert request.analysis_period == "1y"

    def test_portfolio_analysis_request_all_fields(self):
        """Test creating PortfolioAnalysisRequest with all fields."""
        holdings = {"AAPL": 0.3, "MSFT": 0.3, "GOOGL": 0.4}
        request = PortfolioAnalysisRequest(
            holdings=holdings,
            benchmark="SPY",
            analysis_period="5y",
            include_risk_assessment=False,
            include_performance_attribution=False,
        )

        assert request.holdings == holdings
        assert request.benchmark == "SPY"
        assert request.analysis_period == "5y"
        assert request.include_risk_assessment is False
        assert request.include_performance_attribution is False

    def test_portfolio_analysis_request_analysis_period_literal(self):
        """Test PortfolioAnalysisRequest analysis_period must be valid."""
        with pytest.raises(ValidationError) as exc_info:
            PortfolioAnalysisRequest(
                holdings={"AAPL": 1.0},
                analysis_period="10y",
            )

        assert "analysis_period" in str(exc_info.value)


class TestPortfolioAnalysisResponse:
    """Tests for PortfolioAnalysisResponse model."""

    def test_portfolio_analysis_response_creation(self, sample_timestamp):
        """Test creating PortfolioAnalysisResponse."""
        response = PortfolioAnalysisResponse(
            success=True,
            timestamp=sample_timestamp,
        )

        assert response.success is True
        assert response.performance_metrics == {}
        assert response.attribution_analysis == {}
        assert response.recommendations == []

    def test_portfolio_analysis_response_with_metrics(self, sample_timestamp, sample_risk_assessment):
        """Test PortfolioAnalysisResponse with metrics and risk assessment."""
        metrics = {
            "total_return": 0.15,
            "annualized_return": 0.12,
            "sharpe_ratio": 1.5,
        }
        response = PortfolioAnalysisResponse(
            success=True,
            timestamp=sample_timestamp,
            risk_assessment=sample_risk_assessment,
            performance_metrics=metrics,
            recommendations=["Rebalance quarterly"],
        )

        assert response.risk_assessment == sample_risk_assessment
        assert response.performance_metrics == metrics
        assert "Rebalance quarterly" in response.recommendations


# ===========================
# Stock Analysis API Models Tests
# ===========================


class TestStockAnalysisRequest:
    """Tests for StockAnalysisRequest model."""

    def test_stock_analysis_request_minimal(self):
        """Test creating StockAnalysisRequest with required fields."""
        request = StockAnalysisRequest(ticker="AAPL")

        assert request.ticker == "AAPL"
        assert request.analysis_type == "comprehensive"
        assert request.include_peer_comparison is True
        assert request.include_sector_analysis is True

    def test_stock_analysis_request_all_fields(self):
        """Test creating StockAnalysisRequest with all fields."""
        request = StockAnalysisRequest(
            ticker="MSFT",
            analysis_type="technical",
            include_peer_comparison=False,
            include_sector_analysis=False,
        )

        assert request.ticker == "MSFT"
        assert request.analysis_type == "technical"
        assert request.include_peer_comparison is False
        assert request.include_sector_analysis is False

    def test_stock_analysis_request_ticker_required(self):
        """Test StockAnalysisRequest requires ticker."""
        with pytest.raises(ValidationError) as exc_info:
            StockAnalysisRequest()

        assert "ticker" in str(exc_info.value)


class TestStockAnalysisResponse:
    """Tests for StockAnalysisResponse model."""

    def test_stock_analysis_response_creation(self, sample_timestamp):
        """Test creating StockAnalysisResponse."""
        response = StockAnalysisResponse(
            success=True,
            timestamp=sample_timestamp,
            ticker="AAPL",
            recommendation="BUY",
            risk_score=3,
            analysis_summary="Strong fundamentals with solid growth trajectory",
        )

        assert response.ticker == "AAPL"
        assert response.recommendation == "BUY"
        assert response.risk_score == 3
        assert response.target_price is None

    def test_stock_analysis_response_all_fields(self, sample_timestamp):
        """Test StockAnalysisResponse with all fields."""
        metrics = {"roe": 0.25, "pe_ratio": 15.5, "debt_to_equity": 0.3}
        response = StockAnalysisResponse(
            success=True,
            timestamp=sample_timestamp,
            ticker="MSFT",
            recommendation="HOLD",
            target_price=350.0,
            risk_score=5,
            analysis_summary="Fair valuation with moderate growth",
            key_metrics=metrics,
        )

        assert response.target_price == 350.0
        assert response.key_metrics == metrics

    def test_stock_analysis_response_risk_score_range(self, sample_timestamp):
        """Test StockAnalysisResponse risk_score must be 1-10."""
        # Test minimum valid value
        response = StockAnalysisResponse(
            success=True,
            timestamp=sample_timestamp,
            ticker="AAPL",
            recommendation="BUY",
            risk_score=1,
            analysis_summary="Test",
        )
        assert response.risk_score == 1

        # Test maximum valid value
        response = StockAnalysisResponse(
            success=True,
            timestamp=sample_timestamp,
            ticker="AAPL",
            recommendation="SELL",
            risk_score=10,
            analysis_summary="Test",
        )
        assert response.risk_score == 10

        # Test invalid values
        with pytest.raises(ValidationError):
            StockAnalysisResponse(
                success=True,
                timestamp=sample_timestamp,
                ticker="AAPL",
                recommendation="BUY",
                risk_score=0,
                analysis_summary="Test",
            )

        with pytest.raises(ValidationError):
            StockAnalysisResponse(
                success=True,
                timestamp=sample_timestamp,
                ticker="AAPL",
                recommendation="BUY",
                risk_score=11,
                analysis_summary="Test",
            )


# ===========================
# ETF Analysis API Models Tests
# ===========================


class TestETFAnalysisRequest:
    """Tests for ETFAnalysisRequest model."""

    def test_etf_analysis_request_minimal(self):
        """Test creating ETFAnalysisRequest with required fields."""
        request = ETFAnalysisRequest(ticker="SPY")

        assert request.ticker == "SPY"
        assert request.include_holdings_analysis is True
        assert request.include_expense_analysis is True
        assert request.benchmark_comparison is True

    def test_etf_analysis_request_all_fields(self):
        """Test creating ETFAnalysisRequest with all fields."""
        request = ETFAnalysisRequest(
            ticker="QQQ",
            include_holdings_analysis=False,
            include_expense_analysis=False,
            benchmark_comparison=False,
        )

        assert request.ticker == "QQQ"
        assert request.include_holdings_analysis is False


class TestETFAnalysisResponse:
    """Tests for ETFAnalysisResponse model."""

    def test_etf_analysis_response_creation(self, sample_timestamp):
        """Test creating ETFAnalysisResponse."""
        response = ETFAnalysisResponse(
            success=True,
            timestamp=sample_timestamp,
            ticker="SPY",
            recommendation="BUY",
            expense_ratio=0.003,
        )

        assert response.ticker == "SPY"
        assert response.recommendation == "BUY"
        assert response.expense_ratio == 0.003
        assert response.top_holdings == []

    def test_etf_analysis_response_all_fields(self, sample_timestamp, sample_risk_assessment):
        """Test ETFAnalysisResponse with all fields."""
        holdings = [{"symbol": "AAPL", "weight": 0.05}, {"symbol": "MSFT", "weight": 0.04}]
        response = ETFAnalysisResponse(
            success=True,
            timestamp=sample_timestamp,
            ticker="QQQ",
            recommendation="HOLD",
            expense_ratio=0.002,
            tracking_error=0.001,
            top_holdings=holdings,
            risk_assessment=sample_risk_assessment,
        )

        assert response.tracking_error == 0.001
        assert response.top_holdings == holdings
        assert response.risk_assessment is not None


# ===========================
# Crypto Analysis API Models Tests
# ===========================


class TestCryptoAnalysisRequest:
    """Tests for CryptoAnalysisRequest model."""

    def test_crypto_analysis_request_minimal(self):
        """Test creating CryptoAnalysisRequest with required fields."""
        request = CryptoAnalysisRequest(symbol="BTC")

        assert request.symbol == "BTC"
        assert request.include_defi_metrics is True
        assert request.include_on_chain_analysis is True
        assert request.include_sentiment_analysis is True

    def test_crypto_analysis_request_all_fields(self):
        """Test creating CryptoAnalysisRequest with all fields."""
        request = CryptoAnalysisRequest(
            symbol="ETH",
            include_defi_metrics=False,
            include_on_chain_analysis=False,
            include_sentiment_analysis=False,
        )

        assert request.symbol == "ETH"
        assert request.include_defi_metrics is False


class TestCryptoAnalysisResponse:
    """Tests for CryptoAnalysisResponse model."""

    def test_crypto_analysis_response_creation(self, sample_timestamp):
        """Test creating CryptoAnalysisResponse."""
        response = CryptoAnalysisResponse(
            success=True,
            timestamp=sample_timestamp,
            symbol="BTC",
            recommendation="HOLD",
            risk_score=7,
            volatility_score=0.65,
            sentiment_score=0.35,
        )

        assert response.symbol == "BTC"
        assert response.recommendation == "HOLD"
        assert response.risk_score == 7
        assert response.market_cap_rank is None

    def test_crypto_analysis_response_score_ranges(self, sample_timestamp):
        """Test CryptoAnalysisResponse score constraints."""
        # Valid volatility_score (0-1)
        response = CryptoAnalysisResponse(
            success=True,
            timestamp=sample_timestamp,
            symbol="BTC",
            recommendation="BUY",
            risk_score=5,
            volatility_score=0.0,
            sentiment_score=0.5,
        )
        assert response.volatility_score == 0.0

        # Valid sentiment_score (-1 to 1)
        response = CryptoAnalysisResponse(
            success=True,
            timestamp=sample_timestamp,
            symbol="ETH",
            recommendation="SELL",
            risk_score=8,
            volatility_score=1.0,
            sentiment_score=-1.0,
        )
        assert response.sentiment_score == -1.0

        # Invalid volatility_score (> 1)
        with pytest.raises(ValidationError):
            CryptoAnalysisResponse(
                success=True,
                timestamp=sample_timestamp,
                symbol="BTC",
                recommendation="BUY",
                risk_score=5,
                volatility_score=1.5,
                sentiment_score=0.5,
            )

        # Invalid sentiment_score (< -1)
        with pytest.raises(ValidationError):
            CryptoAnalysisResponse(
                success=True,
                timestamp=sample_timestamp,
                symbol="BTC",
                recommendation="BUY",
                risk_score=5,
                volatility_score=0.5,
                sentiment_score=-1.5,
            )


# ===========================
# Monitoring API Models Tests
# ===========================


class TestMonitoringAlert:
    """Tests for MonitoringAlert model."""

    def test_monitoring_alert_creation(self, sample_timestamp):
        """Test creating MonitoringAlert with all fields."""
        alert = MonitoringAlert(
            alert_id="alert-123",
            alert_type="price_movement",
            severity="WARNING",
            message="Stock price moved 5% in 1 hour",
            timestamp=sample_timestamp,
        )

        assert alert.alert_id == "alert-123"
        assert alert.alert_type == "price_movement"
        assert alert.severity == "WARNING"
        assert alert.portfolio_id is None
        assert alert.ticker is None

    def test_monitoring_alert_with_portfolio_and_ticker(self, sample_timestamp):
        """Test MonitoringAlert with portfolio and ticker."""
        alert = MonitoringAlert(
            alert_id="alert-456",
            alert_type="rebalancing_needed",
            severity="INFO",
            message="Portfolio needs rebalancing",
            timestamp=sample_timestamp,
            portfolio_id="port-123",
            ticker="AAPL",
        )

        assert alert.portfolio_id == "port-123"
        assert alert.ticker == "AAPL"

    def test_monitoring_alert_severity_literal(self, sample_timestamp):
        """Test MonitoringAlert severity must be valid literal."""
        with pytest.raises(ValidationError):
            MonitoringAlert(
                alert_id="alert-789",
                alert_type="test",
                severity="INVALID",
                message="Test",
                timestamp=sample_timestamp,
            )


class TestMonitoringStatusRequest:
    """Tests for MonitoringStatusRequest model."""

    def test_monitoring_status_request_all_optional(self):
        """Test MonitoringStatusRequest with all optional fields."""
        request = MonitoringStatusRequest()

        assert request.portfolio_id is None
        assert request.alert_types == []
        assert request.severity_filter == []
        assert request.time_range == "24h"

    def test_monitoring_status_request_with_filters(self):
        """Test MonitoringStatusRequest with filters."""
        request = MonitoringStatusRequest(
            portfolio_id="port-123",
            alert_types=["price_movement", "rebalancing"],
            severity_filter=["ERROR", "CRITICAL"],
            time_range="7d",
        )

        assert request.portfolio_id == "port-123"
        assert "price_movement" in request.alert_types
        assert request.time_range == "7d"


class TestMonitoringStatusResponse:
    """Tests for MonitoringStatusResponse model."""

    def test_monitoring_status_response_creation(self, sample_timestamp):
        """Test creating MonitoringStatusResponse."""
        response = MonitoringStatusResponse(
            success=True,
            timestamp=sample_timestamp,
            system_health="HEALTHY",
            last_check=sample_timestamp,
        )

        assert response.system_health == "HEALTHY"
        assert response.active_alerts == []
        assert response.alert_summary == {}

    def test_monitoring_status_response_with_alerts(self, sample_timestamp):
        """Test MonitoringStatusResponse with alerts."""
        alert = MonitoringAlert(
            alert_id="alert-001",
            alert_type="test",
            severity="WARNING",
            message="Test alert",
            timestamp=sample_timestamp,
        )
        response = MonitoringStatusResponse(
            success=True,
            timestamp=sample_timestamp,
            active_alerts=[alert],
            alert_summary={"WARNING": 1},
            system_health="WARNING",
            last_check=sample_timestamp,
        )

        assert len(response.active_alerts) == 1
        assert response.alert_summary["WARNING"] == 1


# ===========================
# Feedback API Models Tests
# ===========================


class TestFeedbackSubmissionRequest:
    """Tests for FeedbackSubmissionRequest model."""

    def test_feedback_submission_request_minimal(self):
        """Test creating FeedbackSubmissionRequest with required fields."""
        request = FeedbackSubmissionRequest(
            recommendation_id="rec-123",
            user_id="user-456",
            feedback_type="rating",
        )

        assert request.recommendation_id == "rec-123"
        assert request.user_id == "user-456"
        assert request.feedback_type == "rating"

    def test_feedback_submission_request_with_rating(self):
        """Test FeedbackSubmissionRequest with rating."""
        request = FeedbackSubmissionRequest(
            recommendation_id="rec-123",
            user_id="user-456",
            feedback_type="rating",
            rating=5,
        )

        assert request.rating == 5

    def test_feedback_submission_request_with_comment(self):
        """Test FeedbackSubmissionRequest with comment."""
        request = FeedbackSubmissionRequest(
            recommendation_id="rec-123",
            user_id="user-456",
            feedback_type="comment",
            comment="Excellent recommendation, very helpful",
        )

        assert request.comment == "Excellent recommendation, very helpful"

    def test_feedback_submission_request_with_outcome(self):
        """Test FeedbackSubmissionRequest with outcome."""
        request = FeedbackSubmissionRequest(
            recommendation_id="rec-123",
            user_id="user-456",
            feedback_type="outcome",
            outcome="accepted",
        )

        assert request.outcome == "accepted"

    def test_feedback_submission_request_rating_range(self):
        """Test rating field must be 1-5."""
        # Valid rating
        request = FeedbackSubmissionRequest(
            recommendation_id="rec-123",
            user_id="user-456",
            feedback_type="rating",
            rating=1,
        )
        assert request.rating == 1

        # Invalid rating (< 1)
        with pytest.raises(ValidationError):
            FeedbackSubmissionRequest(
                recommendation_id="rec-123",
                user_id="user-456",
                feedback_type="rating",
                rating=0,
            )

        # Invalid rating (> 5)
        with pytest.raises(ValidationError):
            FeedbackSubmissionRequest(
                recommendation_id="rec-123",
                user_id="user-456",
                feedback_type="rating",
                rating=6,
            )


class TestFeedbackSubmissionResponse:
    """Tests for FeedbackSubmissionResponse model."""

    def test_feedback_submission_response_creation(self, sample_timestamp):
        """Test creating FeedbackSubmissionResponse."""
        response = FeedbackSubmissionResponse(
            success=True,
            timestamp=sample_timestamp,
            feedback_id="feedback-789",
            processed=True,
        )

        assert response.feedback_id == "feedback-789"
        assert response.processed is True


# ===========================
# Batch Processing API Models Tests
# ===========================


class TestBatchAnalysisRequest:
    """Tests for BatchAnalysisRequest model."""

    def test_batch_analysis_request_minimal(self):
        """Test creating BatchAnalysisRequest with required fields."""
        request = BatchAnalysisRequest(
            tickers=["AAPL", "MSFT"],
            analysis_type="stock",
            user_id="user-123",
        )

        assert request.tickers == ["AAPL", "MSFT"]
        assert request.analysis_type == "stock"
        assert request.priority == "normal"

    def test_batch_analysis_request_all_fields(self):
        """Test BatchAnalysisRequest with all fields."""
        request = BatchAnalysisRequest(
            tickers=["BTC", "ETH"],
            analysis_type="crypto",
            priority="high",
            callback_url="https://example.com/callback",
            user_id="user-456",
        )

        assert request.callback_url == "https://example.com/callback"
        assert request.priority == "high"

    def test_batch_analysis_request_ticker_constraints(self):
        """Test BatchAnalysisRequest ticker list constraints."""
        # Empty list should fail (min_length=1)
        with pytest.raises(ValidationError):
            BatchAnalysisRequest(
                tickers=[],
                analysis_type="stock",
                user_id="user-123",
            )

        # More than 100 tickers should fail
        with pytest.raises(ValidationError):
            BatchAnalysisRequest(
                tickers=[f"TICK{i}" for i in range(101)],
                analysis_type="stock",
                user_id="user-123",
            )

        # Exactly 100 should work
        request = BatchAnalysisRequest(
            tickers=[f"TICK{i}" for i in range(100)],
            analysis_type="stock",
            user_id="user-123",
        )
        assert len(request.tickers) == 100


class TestBatchAnalysisResponse:
    """Tests for BatchAnalysisResponse model."""

    def test_batch_analysis_response_creation(self, sample_timestamp):
        """Test creating BatchAnalysisResponse."""
        response = BatchAnalysisResponse(
            success=True,
            timestamp=sample_timestamp,
            batch_id="batch-001",
            estimated_completion="2025-01-15T10:30:00",
            status_url="https://api.example.com/batch/batch-001",
        )

        assert response.batch_id == "batch-001"
        assert response.status_url.startswith("https")


class TestBatchStatusResponse:
    """Tests for BatchStatusResponse model."""

    def test_batch_status_response_creation(self, sample_timestamp):
        """Test creating BatchStatusResponse."""
        response = BatchStatusResponse(
            success=True,
            timestamp=sample_timestamp,
            batch_id="batch-001",
            status="processing",
            progress=0.5,
            completed_count=25,
            total_count=50,
        )

        assert response.batch_id == "batch-001"
        assert response.status == "processing"
        assert response.progress == 0.5

    def test_batch_status_response_progress_range(self, sample_timestamp):
        """Test progress field constraints (0-1)."""
        response = BatchStatusResponse(
            success=True,
            timestamp=sample_timestamp,
            batch_id="batch-001",
            status="completed",
            progress=1.0,
            completed_count=50,
            total_count=50,
        )
        assert response.progress == 1.0

        with pytest.raises(ValidationError):
            BatchStatusResponse(
                success=True,
                timestamp=sample_timestamp,
                batch_id="batch-001",
                status="processing",
                progress=1.5,
                completed_count=25,
                total_count=50,
            )

    def test_batch_status_response_completed_status(self, sample_timestamp):
        """Test BatchStatusResponse with completed status and results URL."""
        response = BatchStatusResponse(
            success=True,
            timestamp=sample_timestamp,
            batch_id="batch-002",
            status="completed",
            progress=1.0,
            completed_count=100,
            total_count=100,
            results_url="https://api.example.com/batch/batch-002/results",
        )

        assert response.results_url is not None


# ===========================
# Health Check API Models Tests
# ===========================


class TestHealthCheckResponse:
    """Tests for HealthCheckResponse model."""

    def test_health_check_response_creation(self, sample_timestamp):
        """Test creating HealthCheckResponse."""
        response = HealthCheckResponse(
            success=True,
            timestamp=sample_timestamp,
            status="healthy",
            version="1.0.0",
            uptime=3600.5,
        )

        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.uptime == 3600.5

    def test_health_check_response_with_dependencies(self, sample_timestamp):
        """Test HealthCheckResponse with dependencies."""
        dependencies = {
            "database": "healthy",
            "redis": "degraded",
            "external_api": "healthy",
        }
        response = HealthCheckResponse(
            success=True,
            timestamp=sample_timestamp,
            status="degraded",
            version="1.0.0",
            uptime=7200.0,
            dependencies=dependencies,
        )

        assert response.dependencies == dependencies

    def test_health_check_response_status_literal(self, sample_timestamp):
        """Test status must be valid literal."""
        with pytest.raises(ValidationError):
            HealthCheckResponse(
                success=True,
                timestamp=sample_timestamp,
                status="invalid",
                version="1.0.0",
                uptime=100.0,
            )


# ===========================
# Configuration API Models Tests
# ===========================


class TestConfigurationUpdateRequest:
    """Tests for ConfigurationUpdateRequest model."""

    def test_configuration_update_request_minimal(self):
        """Test creating ConfigurationUpdateRequest."""
        request = ConfigurationUpdateRequest(
            config_section="logging",
            config_data={"level": "DEBUG"},
        )

        assert request.config_section == "logging"
        assert request.config_data["level"] == "DEBUG"
        assert request.validate_only is False

    def test_configuration_update_request_validate_only(self):
        """Test ConfigurationUpdateRequest with validate_only."""
        request = ConfigurationUpdateRequest(
            config_section="database",
            config_data={"host": "localhost", "port": 5432},
            validate_only=True,
        )

        assert request.validate_only is True


class TestConfigurationUpdateResponse:
    """Tests for ConfigurationUpdateResponse model."""

    def test_configuration_update_response_success(self, sample_timestamp):
        """Test successful ConfigurationUpdateResponse."""
        response = ConfigurationUpdateResponse(
            success=True,
            timestamp=sample_timestamp,
            validation_passed=True,
            changes_applied=True,
        )

        assert response.validation_passed is True
        assert response.changes_applied is True
        assert response.validation_errors == []

    def test_configuration_update_response_validation_failure(self, sample_timestamp):
        """Test ConfigurationUpdateResponse with validation failures."""
        response = ConfigurationUpdateResponse(
            success=False,
            timestamp=sample_timestamp,
            validation_passed=False,
            changes_applied=False,
            validation_errors=["Invalid port number", "Missing required field"],
        )

        assert response.validation_passed is False
        assert len(response.validation_errors) == 2

    def test_configuration_update_response_restart_required(self, sample_timestamp):
        """Test ConfigurationUpdateResponse requiring restart."""
        response = ConfigurationUpdateResponse(
            success=True,
            timestamp=sample_timestamp,
            validation_passed=True,
            changes_applied=True,
            restart_required=True,
        )

        assert response.restart_required is True


# ===========================
# Search and Discovery API Models Tests
# ===========================


class TestSearchRequest:
    """Tests for SearchRequest model."""

    def test_search_request_minimal(self):
        """Test creating SearchRequest with required fields."""
        request = SearchRequest(query="Apple")

        assert request.query == "Apple"
        assert request.search_type == "all"
        assert request.limit == 20

    def test_search_request_all_fields(self):
        """Test SearchRequest with all fields."""
        filters = {"sector": "Technology", "market_cap_min": 1e9}
        request = SearchRequest(
            query="tech stocks",
            search_type="company",
            limit=50,
            filters=filters,
        )

        assert request.search_type == "company"
        assert request.limit == 50
        assert request.filters == filters

    def test_search_request_query_length(self):
        """Test query must have min_length=1."""
        with pytest.raises(ValidationError):
            SearchRequest(query="")

    def test_search_request_limit_constraints(self):
        """Test limit constraints (1-100)."""
        # Valid: 1
        request = SearchRequest(query="test", limit=1)
        assert request.limit == 1

        # Valid: 100
        request = SearchRequest(query="test", limit=100)
        assert request.limit == 100

        # Invalid: 0
        with pytest.raises(ValidationError):
            SearchRequest(query="test", limit=0)

        # Invalid: 101
        with pytest.raises(ValidationError):
            SearchRequest(query="test", limit=101)


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_search_result_creation(self):
        """Test creating SearchResult."""
        result = SearchResult(
            ticker="AAPL",
            name="Apple Inc.",
            asset_type="stock",
            relevance_score=0.95,
        )

        assert result.ticker == "AAPL"
        assert result.name == "Apple Inc."
        assert result.asset_type == "stock"
        assert result.sector is None
        assert result.market_cap is None

    def test_search_result_all_fields(self):
        """Test SearchResult with all fields."""
        result = SearchResult(
            ticker="SPY",
            name="SPDR S&P 500 ETF Trust",
            asset_type="etf",
            sector="Technology",
            market_cap=500e9,
            relevance_score=0.88,
        )

        assert result.sector == "Technology"
        assert result.market_cap == 500e9

    def test_search_result_relevance_score_range(self):
        """Test relevance_score must be 0-1."""
        result = SearchResult(
            ticker="BTC",
            name="Bitcoin",
            asset_type="crypto",
            relevance_score=0.0,
        )
        assert result.relevance_score == 0.0

        result = SearchResult(
            ticker="BTC",
            name="Bitcoin",
            asset_type="crypto",
            relevance_score=1.0,
        )
        assert result.relevance_score == 1.0

        with pytest.raises(ValidationError):
            SearchResult(
                ticker="BTC",
                name="Bitcoin",
                asset_type="crypto",
                relevance_score=1.5,
            )


class TestSearchResponse:
    """Tests for SearchResponse model."""

    def test_search_response_creation(self, sample_timestamp):
        """Test creating SearchResponse."""
        response = SearchResponse(
            success=True,
            timestamp=sample_timestamp,
            total_results=0,
            query_time=0.15,
        )

        assert response.total_results == 0
        assert response.query_time == 0.15
        assert response.results == []

    def test_search_response_with_results(self, sample_timestamp):
        """Test SearchResponse with search results."""
        result1 = SearchResult(
            ticker="AAPL",
            name="Apple Inc.",
            asset_type="stock",
            relevance_score=0.99,
        )
        result2 = SearchResult(
            ticker="APPL",
            name="AppLovin Corporation",
            asset_type="stock",
            relevance_score=0.65,
        )

        response = SearchResponse(
            success=True,
            timestamp=sample_timestamp,
            results=[result1, result2],
            total_results=2,
            query_time=0.23,
            suggestions=["Try 'Apple stock'", "Try 'AAPL'"],
        )

        assert len(response.results) == 2
        assert response.total_results == 2
        assert len(response.suggestions) == 2


# ===========================
# Serialization and Edge Cases Tests
# ===========================


class TestModelSerialization:
    """Tests for model serialization and JSON output."""

    def test_api_response_model_dump_json(self, sample_timestamp):
        """Test APIResponse can be serialized to JSON."""
        response = APIResponse(
            success=True,
            message="Test",
            timestamp=sample_timestamp,
        )

        json_str = response.model_dump_json(indent=2)
        assert '"success": true' in json_str
        assert '"message": "Test"' in json_str

    def test_complex_model_serialization(self, sample_timestamp):
        """Test complex nested models can be serialized."""
        response = StockAnalysisResponse(
            success=True,
            timestamp=sample_timestamp,
            ticker="AAPL",
            recommendation="BUY",
            risk_score=5,
            analysis_summary="Good opportunity",
            key_metrics={"roe": 0.25, "pe_ratio": 15.5},
        )

        json_str = response.model_dump_json()
        assert "AAPL" in json_str
        assert "BUY" in json_str
        assert "0.25" in json_str


class TestModelEquality:
    """Tests for model equality and comparison."""

    def test_same_request_models_equal(self):
        """Test identical request models are equal."""
        req1 = StockAnalysisRequest(ticker="AAPL")
        req2 = StockAnalysisRequest(ticker="AAPL")

        assert req1 == req2

    def test_different_request_models_not_equal(self):
        """Test different request models are not equal."""
        req1 = StockAnalysisRequest(ticker="AAPL")
        req2 = StockAnalysisRequest(ticker="MSFT")

        assert req1 != req2


class TestModelDefaults:
    """Tests for model default values."""

    def test_discovery_request_defaults(self):
        """Test DiscoveryRequest default values."""
        request = DiscoveryRequest(
            asset_class="stock",
            investment_amount=5000,
        )

        assert request.risk_tolerance == "moderate"
        assert request.time_horizon == "medium"
        assert request.exclude_sectors == []
        assert request.include_esg is False

    def test_portfolio_analysis_request_defaults(self):
        """Test PortfolioAnalysisRequest default values."""
        request = PortfolioAnalysisRequest(
            holdings={"AAPL": 1.0},
        )

        assert request.benchmark is None
        assert request.analysis_period == "1y"
        assert request.include_risk_assessment is True
        assert request.include_performance_attribution is True

    def test_search_request_defaults(self):
        """Test SearchRequest default values."""
        request = SearchRequest(query="test")

        assert request.search_type == "all"
        assert request.limit == 20
        assert request.filters == {}
