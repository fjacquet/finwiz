# Portfolio Rebalancing API Reference

## Overview

This document provides comprehensive API documentation for the FinWiz Portfolio Rebalancing system. All classes, methods, and data models are documented with examples and usage patterns.

## Table of Contents

1. [Core Classes](#core-classes)
2. [Data Models](#data-models)
3. [Orchestrator API](#orchestrator-api)
4. [Analysis Components](#analysis-components)
5. [Optimization Engine](#optimization-engine)
6. [Utility Classes](#utility-classes)
7. [Error Handling](#error-handling)
8. [Examples](#examples)

## Core Classes

### PortfolioRebalancingOrchestrator

Main orchestrator class that coordinates the entire rebalancing workflow.

```python
class PortfolioRebalancingOrchestrator:
    """
    Main orchestrator for portfolio rebalancing operations.

    Coordinates price data retrieval, portfolio analysis, optimization,
    and report generation to provide comprehensive rebalancing recommendations.
    """
```

#### Constructor

```python
def __init__(
    self,
    price_service: Optional[PortfolioPriceService] = None,
    portfolio_analyzer: Optional[PortfolioAnalyzer] = None,
    rebalancing_engine: Optional[RebalancingEngine] = None,
    report_generator: Optional[HTMLReportGenerator] = None
) -> None:
    """
    Initialize the portfolio rebalancing orchestrator.

    Args:
        price_service: Service for retrieving current market prices
        portfolio_analyzer: Analyzer for portfolio composition and metrics
        rebalancing_engine: Engine for optimization and trade generation
        report_generator: Generator for HTML reports

    Note:
        If components are not provided, default instances will be created.
    """
```

#### Methods

##### rebalance_portfolio

```python
async def rebalance_portfolio(
    self,
    config: PortfolioConfiguration,
    portfolio_id: Optional[str] = None
) -> RebalancingResult:
    """
    Perform complete portfolio rebalancing analysis.

    Args:
        config: Portfolio configuration with holdings and targets
        portfolio_id: Optional identifier for tracking purposes

    Returns:
        RebalancingResult: Complete analysis with trade recommendations

    Raises:
        InsufficientPriceDataError: When price data cannot be retrieved
        PortfolioRebalancingError: When analysis fails
        OptimizationFailedError: When optimization cannot be completed

    Example:
        >>> config = PortfolioConfiguration(...)
        >>> result = await orchestrator.rebalance_portfolio(config)
        >>> print(f"Recommendation: {result.overall_recommendation}")
    """
```

##### analyze_current_portfolio

```python
async def analyze_current_portfolio(
    self,
    config: PortfolioConfiguration
) -> PortfolioAnalysis:
    """
    Analyze current portfolio without generating trade recommendations.

    Args:
        config: Portfolio configuration with current holdings

    Returns:
        PortfolioAnalysis: Current portfolio composition and metrics

    Example:
        >>> analysis = await orchestrator.analyze_current_portfolio(config)
        >>> print(f"Total value: ${analysis.total_value:,.2f}")
    """
```

##### generate_rebalancing_report

```python
async def generate_rebalancing_report(
    self,
    result: RebalancingResult,
    language: str = "en"
) -> str:
    """
    Generate HTML report from rebalancing result.

    Args:
        result: Rebalancing analysis result
        language: Report language ("en" or "fr")

    Returns:
        str: HTML report content

    Example:
        >>> html = await orchestrator.generate_rebalancing_report(result)
        >>> with open("report.html", "w") as f:
        ...     f.write(html)
    """
```

##### close

```python
async def close(self) -> None:
    """
    Clean up resources and close connections.

    Should be called when done with the orchestrator to ensure
    proper cleanup of network connections and other resources.

    Example:
        >>> await orchestrator.close()
    """
```

## Data Models

### PortfolioConfiguration

Main configuration class for portfolio rebalancing.

```python
class PortfolioConfiguration(BaseModel):
    """Portfolio rebalancing configuration."""

    # Required fields
    holdings: List[Holding] = Field(..., min_items=1)
    target_weights: Dict[str, float] = Field(...)

    # Optional configuration
    tolerance_bands: Dict[str, float] = Field(default_factory=dict)
    global_tolerance: float = Field(default=0.05, ge=0.001, le=0.5)
    available_capital: float = Field(default=0.0)
    transaction_cost_rate: float = Field(default=0.001, ge=0.0, le=0.1)
    min_trade_size: float = Field(default=0.01, ge=0.001)
    rebalancing_method: RebalancingMethod = Field(default=RebalancingMethod.MINIMIZE_TRADES)
```

#### Example Usage

```python
config = PortfolioConfiguration(
    holdings=[
        Holding(symbol="AAPL", shares=100.0, cost_basis=150.0),
        Holding(symbol="GOOGL", shares=10.0, cost_basis=2500.0),
    ],
    target_weights={
        "AAPL": 0.6,
        "GOOGL": 0.4,
    },
    tolerance_bands={
        "AAPL": 0.03,  # ±3%
        "GOOGL": 0.05, # ±5%
    },
    available_capital=5000.0,
    transaction_cost_rate=0.005,  # 0.5%
    rebalancing_method=RebalancingMethod.MINIMIZE_COSTS
)
```

### Holding

Represents an individual portfolio position.

```python
class Holding(BaseModel):
    """Individual portfolio holding."""

    symbol: str = Field(..., description="Stock ticker symbol")
    shares: float = Field(..., gt=0, description="Number of shares held")
    cost_basis: Optional[float] = Field(None, gt=0, description="Average cost per share")
    acquisition_date: Optional[datetime] = Field(None, description="Date acquired")
```

### RebalancingResult

Complete result of rebalancing analysis.

```python
class RebalancingResult(BaseModel):
    """Complete rebalancing analysis result."""

    # Metadata
    analysis_timestamp: datetime
    portfolio_id: Optional[str]

    # Analysis results
    current_portfolio: PortfolioAnalysis
    trade_recommendations: List[TradeRecommendation]
    projected_portfolio: PortfolioAnalysis

    # Cost and risk analysis
    cost_analysis: CostAnalysis
    current_risk_score: float = Field(..., ge=0, le=10)
    projected_risk_score: float = Field(..., ge=0, le=10)
    risk_improvement: float

    # Execution summary
    execution_summary: ExecutionSummary
    overall_recommendation: RebalancingRecommendation
    next_review_date: datetime

    # Alternative scenarios
    alternative_scenarios: List[AlternativeScenario] = Field(default_factory=list)
```

### TradeRecommendation

Individual trade recommendation.

```python
class TradeRecommendation(BaseModel):
    """Individual trade recommendation."""

    # Trade details
    symbol: str
    action: TradeAction  # BUY, SELL, HOLD
    quantity: float = Field(..., description="Number of shares to trade")
    current_price: float = Field(..., gt=0)

    # Financial impact
    trade_value: float
    estimated_commission: float = Field(..., ge=0)
    estimated_spread_cost: float = Field(..., ge=0)
    total_estimated_cost: float = Field(..., ge=0)

    # Portfolio impact
    current_weight: float = Field(..., ge=0, le=1)
    target_weight: float = Field(..., ge=0, le=1)
    weight_deviation: float
    projected_weight_after_trade: float = Field(..., ge=0, le=1)

    # Execution details
    priority: int = Field(..., ge=1, le=10)
    urgency: UrgencyLevel
    rationale: str = Field(..., min_length=10)

    # Optional considerations
    tax_implications: Optional[str] = None
    market_impact_warning: Optional[str] = None
```

## Orchestrator API

### Async Context Manager Support

```python
async with PortfolioRebalancingOrchestrator() as orchestrator:
    result = await orchestrator.rebalance_portfolio(config)
    # Automatic cleanup on exit
```

### Batch Processing

```python
async def rebalance_multiple_portfolios(
    self,
    configs: List[Tuple[PortfolioConfiguration, str]]
) -> List[RebalancingResult]:
    """
    Process multiple portfolios efficiently.

    Args:
        configs: List of (configuration, portfolio_id) tuples

    Returns:
        List[RebalancingResult]: Results for each portfolio
    """
```

## Analysis Components

### PortfolioAnalyzer

Analyzes portfolio composition and calculates metrics.

```python
class PortfolioAnalyzer:
    """Analyzes portfolio composition and calculates current weightings."""
```

#### Key Methods

##### calculate_current_weightings

```python
def calculate_current_weightings(
    self,
    holdings: List[Holding],
    prices: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate current portfolio weightings.

    Args:
        holdings: List of portfolio holdings
        prices: Current prices for each symbol

    Returns:
        Dict[str, float]: Symbol to weight mapping

    Raises:
        PortfolioAnalysisError: If calculation fails
        InsufficientDataError: If price data is missing
    """
```

##### identify_rebalancing_needs

```python
def identify_rebalancing_needs(
    self,
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
    tolerance_bands: Dict[str, float],
    global_tolerance: float = 0.05
) -> List[RebalancingNeed]:
    """
    Identify positions that need rebalancing.

    Args:
        current_weights: Current portfolio weights
        target_weights: Target portfolio weights
        tolerance_bands: Position-specific tolerances
        global_tolerance: Default tolerance for unspecified positions

    Returns:
        List[RebalancingNeed]: Positions requiring rebalancing
    """
```

##### calculate_portfolio_metrics

```python
def calculate_portfolio_metrics(
    self,
    holdings: List[Holding],
    prices: Dict[str, float]
) -> PortfolioMetrics:
    """
    Calculate comprehensive portfolio metrics.

    Args:
        holdings: Portfolio holdings
        prices: Current market prices

    Returns:
        PortfolioMetrics: Comprehensive portfolio metrics
    """
```

### CostAnalyzer

Analyzes transaction costs and cost-benefit ratios.

```python
class CostAnalyzer:
    """Analyzes transaction costs for rebalancing trades."""

    def calculate_trade_costs(
        self,
        trades: List[TradeRecommendation],
        cost_rate: float = 0.001
    ) -> CostAnalysis:
        """
        Calculate comprehensive cost analysis for trades.

        Args:
            trades: List of trade recommendations
            cost_rate: Transaction cost rate (default 0.1%)

        Returns:
            CostAnalysis: Detailed cost breakdown
        """
```

## Optimization Engine

### RebalancingEngine

Core optimization engine for generating trade recommendations.

```python
class RebalancingEngine:
    """Optimization engine for calculating optimal rebalancing trades."""
```

#### Key Methods

##### optimize_rebalancing_trades

```python
def optimize_rebalancing_trades(
    self,
    rebalancing_needs: List[RebalancingNeed],
    current_portfolio: PortfolioAnalysis,
    target_weights: Dict[str, float],
    prices: Dict[str, float],
    config: PortfolioConfiguration
) -> OptimizedTrades:
    """
    Generate optimized trade recommendations.

    Args:
        rebalancing_needs: Positions requiring rebalancing
        current_portfolio: Current portfolio analysis
        target_weights: Target allocation weights
        prices: Current market prices
        config: Portfolio configuration

    Returns:
        OptimizedTrades: Optimized trade recommendations

    Raises:
        OptimizationError: If optimization fails
    """
```

##### generate_enhanced_trade_recommendations

```python
async def generate_enhanced_trade_recommendations(
    self,
    rebalancing_needs: List[RebalancingNeed],
    current_portfolio: PortfolioAnalysis,
    target_weights: Dict[str, float],
    prices: Dict[str, float],
    config: PortfolioConfiguration
) -> Tuple[List[TradeRecommendation], List[str]]:
    """
    Generate enhanced trade recommendations with validation.

    Returns:
        Tuple containing:
        - List[TradeRecommendation]: Trade recommendations
        - List[str]: Validation errors or warnings
    """
```

### Optimization Strategies

#### MinimizeTradesStrategy

```python
class MinimizeTradesStrategy:
    """Strategy that minimizes the number of trades required."""

    def optimize(
        self,
        rebalancing_needs: List[RebalancingNeed],
        current_portfolio: PortfolioAnalysis,
        target_weights: Dict[str, float],
        prices: Dict[str, float],
        available_capital: float,
        constraints: List[OptimizationConstraint],
        config: PortfolioConfiguration
    ) -> OptimizedTrades:
        """Optimize to minimize number of trades."""
```

#### MinimizeCostsStrategy

```python
class MinimizeCostsStrategy:
    """Strategy that minimizes total transaction costs."""

    def optimize(self, ...) -> OptimizedTrades:
        """Optimize to minimize total costs."""
```

#### RiskAwareStrategy

```python
class RiskAwareStrategy:
    """Strategy that considers risk metrics and concentration limits."""

    def optimize(self, ...) -> OptimizedTrades:
        """Optimize considering risk factors."""
```

## Utility Classes

### PortfolioPriceService

Service for retrieving current market prices.

```python
class PortfolioPriceService:
    """Service for retrieving current market prices."""

    async def get_current_prices(
        self,
        symbols: List[str]
    ) -> Dict[str, PriceData]:
        """
        Get current prices for multiple symbols.

        Args:
            symbols: List of ticker symbols

        Returns:
            Dict[str, PriceData]: Symbol to price data mapping

        Raises:
            PriceDataError: If price retrieval fails
        """

    async def get_price_with_fallback(
        self,
        symbol: str
    ) -> PriceData:
        """
        Get price with fallback to alternative sources.

        Args:
            symbol: Ticker symbol

        Returns:
            PriceData: Price data with timestamp
        """
```

### RiskManager

Manages risk constraints and safeguards.

```python
class RiskManager:
    """Manages risk constraints and portfolio safeguards."""

    def validate_rebalancing_safety(
        self,
        trades: List[TradeRecommendation],
        current_portfolio: PortfolioAnalysis,
        config: PortfolioConfiguration
    ) -> Tuple[bool, List[str]]:
        """
        Validate that rebalancing is safe to execute.

        Returns:
            Tuple containing:
            - bool: Whether rebalancing is safe
            - List[str]: Risk warnings or violations
        """
```

## Error Handling

### Exception Hierarchy

```python
class PortfolioRebalancingError(Exception):
    """Base exception for portfolio rebalancing errors."""
    pass

class InsufficientPriceDataError(PortfolioRebalancingError):
    """Raised when price data cannot be retrieved."""

    def __init__(self, missing_symbols: List[str]):
        self.missing_symbols = missing_symbols
        super().__init__(f"Price data unavailable for: {', '.join(missing_symbols)}")

class OptimizationFailedError(PortfolioRebalancingError):
    """Raised when optimization cannot be completed."""
    pass

class PortfolioAnalysisError(PortfolioRebalancingError):
    """Raised when portfolio analysis fails."""
    pass
```

### Error Handling Patterns

```python
try:
    result = await orchestrator.rebalance_portfolio(config)
except InsufficientPriceDataError as e:
    print(f"Cannot get prices for: {e.missing_symbols}")
    # Handle missing price data
except OptimizationFailedError as e:
    print(f"Optimization failed: {e}")
    # Handle optimization failure
except PortfolioRebalancingError as e:
    print(f"Rebalancing error: {e}")
    # Handle general rebalancing errors
```

## Examples

### Basic Usage

```python
from finwiz.orchestrators.portfolio_rebalancing import PortfolioRebalancingOrchestrator
from finwiz.schemas.portfolio_rebalancing import PortfolioConfiguration, Holding

async def basic_rebalancing():
    # Create configuration
    config = PortfolioConfiguration(
        holdings=[
            Holding(symbol="AAPL", shares=100.0),
            Holding(symbol="GOOGL", shares=10.0),
        ],
        target_weights={"AAPL": 0.6, "GOOGL": 0.4}
    )

    # Run analysis
    orchestrator = PortfolioRebalancingOrchestrator()
    try:
        result = await orchestrator.rebalance_portfolio(config)

        # Print recommendations
        for trade in result.trade_recommendations:
            print(f"{trade.action} {trade.quantity} shares of {trade.symbol}")

    finally:
        await orchestrator.close()
```

### Advanced Configuration

```python
async def advanced_rebalancing():
    config = PortfolioConfiguration(
        holdings=[
            Holding(symbol="AAPL", shares=150.0, cost_basis=120.0),
            Holding(symbol="GOOGL", shares=25.0, cost_basis=2200.0),
            Holding(symbol="MSFT", shares=100.0, cost_basis=280.0),
        ],
        target_weights={"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.3},
        tolerance_bands={"AAPL": 0.03, "GOOGL": 0.05, "MSFT": 0.03},
        available_capital=5000.0,
        transaction_cost_rate=0.005,
        min_trade_size=500.0,
        rebalancing_method=RebalancingMethod.MINIMIZE_COSTS
    )

    orchestrator = PortfolioRebalancingOrchestrator()
    try:
        result = await orchestrator.rebalance_portfolio(
            config,
            portfolio_id="retirement-401k"
        )

        # Generate report
        html_report = await orchestrator.generate_rebalancing_report(result)

        # Save report
        with open("rebalancing_report.html", "w") as f:
            f.write(html_report)

        return result

    finally:
        await orchestrator.close()
```

### Batch Processing

```python
async def batch_rebalancing():
    configs = [
        (config1, "portfolio-1"),
        (config2, "portfolio-2"),
        (config3, "portfolio-3"),
    ]

    orchestrator = PortfolioRebalancingOrchestrator()
    try:
        results = []
        for config, portfolio_id in configs:
            result = await orchestrator.rebalance_portfolio(config, portfolio_id)
            results.append(result)

        return results

    finally:
        await orchestrator.close()
```

### Error Handling

```python
async def robust_rebalancing():
    orchestrator = PortfolioRebalancingOrchestrator()

    try:
        result = await orchestrator.rebalance_portfolio(config)
        return result

    except InsufficientPriceDataError as e:
        logger.error(f"Price data unavailable for: {e.missing_symbols}")
        # Retry with subset of symbols or use cached prices
        return None

    except OptimizationFailedError as e:
        logger.error(f"Optimization failed: {e}")
        # Fall back to simple rebalancing method
        config.rebalancing_method = RebalancingMethod.MINIMIZE_TRADES
        return await orchestrator.rebalance_portfolio(config)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None

    finally:
        await orchestrator.close()
```

## Type Hints and Validation

All API methods include comprehensive type hints and Pydantic validation:

```python
from typing import List, Dict, Optional, Tuple, Union
from pydantic import BaseModel, Field, validator

# All models use strict Pydantic validation
class ExampleModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    required_field: str = Field(..., min_length=1)
    optional_field: Optional[float] = Field(None, ge=0)

    @validator("required_field")
    def validate_required_field(cls, v: str) -> str:
        # Custom validation logic
        return v.upper()
```

This API reference provides complete documentation for all public interfaces in the portfolio rebalancing system, enabling developers to integrate and extend the functionality effectively.
