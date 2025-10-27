---
title: "Developer"
description: "Complete reference documentation for Developer"
category: "reference"
tags:
  - "reference"
date: "2025-10-26"
source: "portfolio_rebalancing/developer_guide.md"
---

# Portfolio Rebalancing Developer Guide

## Overview

This guide provides comprehensive information for developers who want to extend, modify, or integrate with the FinWiz Portfolio Rebalancing system. It covers architecture, extension points, testing strategies, and best practices.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Extension Points](#extension-points)
3. [Creating Custom Strategies](#creating-custom-strategies)
4. [Adding New Data Sources](#adding-new-data-sources)
5. [Custom Constraints](#custom-constraints)
6. [Testing Guidelines](#testing-guidelines)
7. [Performance Optimization](#performance-optimization)
8. [Integration Patterns](#integration-patterns)
9. [Deployment Considerations](#deployment-considerations)

## Architecture Overview

### System Components

The portfolio rebalancing system follows a modular architecture with clear separation of concerns:

```text
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Layer                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │        PortfolioRebalancingOrchestrator             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐  │
│  │ PortfolioPrice  │ │ PortfolioAnalyzer│ │ Rebalancing  │  │
│  │    Service      │ │                 │ │   Engine     │  │
│  └─────────────────┘ └─────────────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Strategy Layer                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐  │
│  │ MinimizeTrades  │ │ MinimizeCosts   │ │  RiskAware   │  │
│  │   Strategy      │ │   Strategy      │ │  Strategy    │  │
│  └─────────────────┘ └─────────────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐  │
│  │   Yahoo Finance │ │  Alpha Vantage  │ │    Cache     │  │
│  │      API        │ │      API        │ │   Manager    │  │
│  └─────────────────┘ └─────────────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```text
### Key Design Principles

1. **Dependency Injection**: All components accept dependencies through constructor injection
2. **Strategy Pattern**: Optimization algorithms are pluggable strategies
3. **Async/Await**: All I/O operations are asynchronous
4. **Pydantic Validation**: Strict data validation using Pydantic v2
5. **Error Handling**: Comprehensive error handling with custom exceptions
6. **Testability**: All components are easily mockable for testing

## Extension Points

### 1. Custom Optimization Strategies

The most common extension is adding new optimization strategies:

```pythonthon
from abc import ABC, abstractmethod
from finwiz.quantitative.rebalancing_engine import OptimizationStrategy

class CustomOptimizationStrategy(OptimizationStrategy):
    """Custom optimization strategy implementation."""

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
        """
        Implement custom optimization logic.

        Returns:
            OptimizedTrades: Optimized trade recommendations
        """
        # Your custom optimization logic here
        trades = self._generate_custom_trades(rebalancing_needs, prices, config)

        return OptimizedTrades(
            trades=trades,
            total_cost=self._calculate_total_cost(trades),
            capital_used=self._calculate_capital_used(trades),
            constraints_violated=[],
            optimization_score=self._calculate_optimization_score(trades),
            method_used="CUSTOM_METHOD"
        )

    def _generate_custom_trades(
        self,
        needs: List[RebalancingNeed],
        prices: Dict[str, float],
        config: PortfolioConfiguration
    ) -> List[TradeRecommendation]:
        """Generate trades using custom logic."""
        trades = []

        for need in needs:
            if need.exceeds_tolerance:
                trade = self._create_trade_recommendation(need, prices, config)
                trades.append(trade)

        return trades
```text
### 2. Custom Price Data Sources

Add new price data providers by implementing the price service interface:

```pythonthon
from finwiz.tools.portfolio_price_service import PriceDataProvider

class CustomPriceProvider(PriceDataProvider):
    """Custom price data provider implementation."""

    async def get_current_price(self, symbol: str) -> PriceData:
        """Get current price from custom source."""
        # Implement your price retrieval logic
        price = await self._fetch_price_from_custom_api(symbol)

        return PriceData(
            symbol=symbol,
            price=price,
            timestamp=datetime.now()
        )

    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, PriceData]:
        """Get multiple prices efficiently."""
        # Implement batch price retrieval
        prices = await self._fetch_multiple_prices(symbols)

        return {
            symbol: PriceData(symbol=symbol, price=price, timestamp=datetime.now())
            for symbol, price in prices.items()
        }

    async def _fetch_price_from_custom_api(self, symbol: str) -> float:
        """Fetch price from your custom API."""
        # Your API integration logic
        pass
```text
### 3. Custom Portfolio Analyzers

Extend portfolio analysis capabilities:

```pythonthon
from finwiz.quantitative.portfolio_analyzer import PortfolioAnalyzer

class EnhancedPortfolioAnalyzer(PortfolioAnalyzer):
    """Enhanced portfolio analyzer with additional metrics."""

    def calculate_enhanced_metrics(
        self,
        holdings: List[Holding],
        prices: Dict[str, float],
        market_data: Optional[Dict[str, Any]] = None
    ) -> EnhancedPortfolioMetrics:
        """Calculate additional portfolio metrics."""

        # Call parent method for base metrics
        base_metrics = self.calculate_portfolio_metrics(holdings, prices)

        # Add custom metrics
        sector_allocation = self._calculate_sector_allocation(holdings, market_data)
        correlation_matrix = self._calculate_correlation_matrix(holdings, market_data)
        var_analysis = self._calculate_value_at_risk(holdings, prices, market_data)

        return EnhancedPortfolioMetrics(
            **base_metrics.dict(),
            sector_allocation=sector_allocation,
            correlation_matrix=correlation_matrix,
            value_at_risk=var_analysis
        )
```text
### 4. Custom Report Generators

Create specialized report formats:

```pythonthon
from finwiz.tools.html_report_generator import HTMLReportGenerator

class CustomReportGenerator(HTMLReportGenerator):
    """Custom report generator with additional sections."""

    def generate_enhanced_report(
        self,
        result: RebalancingResult,
        custom_data: Dict[str, Any]
    ) -> str:
        """Generate report with custom sections."""

        # Clear existing sections
        self.clear_sections()

        # Add standard sections
        self._add_executive_summary(result)
        self._add_current_analysis(result)
        self._add_trade_recommendations(result)

        # Add custom sections
        self._add_sector_analysis(custom_data.get("sector_data"))
        self._add_risk_attribution(custom_data.get("risk_data"))
        self._add_performance_attribution(custom_data.get("performance_data"))

        return self.generate_html(
            title="Enhanced Portfolio Rebalancing Report",
            language="en"
        )

    def _add_sector_analysis(self, sector_data: Dict[str, Any]) -> None:
        """Add sector allocation analysis section."""
        if not sector_data:
            return

        html_content = self._render_sector_chart(sector_data)
        self.add_section("Sector Analysis", html_content)
```text
## Creating Custom Strategies

### Step-by-Step Strategy Creation

1. **Define Strategy Class**

```pythonthon
from finwiz.quantitative.rebalancing_engine import OptimizationStrategy
from finwiz.schemas.portfolio_rebalancing import *

class MomentumBasedStrategy(OptimizationStrategy):
    """Strategy that considers price momentum in rebalancing decisions."""

    def __init__(self, momentum_window: int = 30):
        self.momentum_window = momentum_window
```text
2. **Implement Core Optimization Logic**

```pythonthon
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
    """Optimize considering momentum factors."""

    # Get momentum data
    momentum_scores = self._calculate_momentum_scores(
        list(target_weights.keys())
    )

    # Adjust rebalancing needs based on momentum
    adjusted_needs = self._adjust_for_momentum(
        rebalancing_needs,
        momentum_scores
    )

    # Generate trades
    trades = self._generate_momentum_aware_trades(
        adjusted_needs,
        prices,
        config
    )

    # Validate constraints
    violations = self._check_constraints(trades, constraints)

    return OptimizedTrades(
        trades=trades,
        total_cost=sum(trade.total_estimated_cost for trade in trades),
        capital_used=sum(trade.trade_value for trade in trades if trade.action == TradeAction.BUY),
        constraints_violated=violations,
        optimization_score=self._calculate_momentum_score(trades, momentum_scores),
        method_used="MOMENTUM_BASED"
    )
```text
3. **Register Strategy with Engine**

```pythonthon
from finwiz.quantitative.rebalancing_engine import RebalancingEngine
from finwiz.schemas.portfolio_rebalancing import RebalancingMethod

# Extend the RebalancingMethod enum
class ExtendedRebalancingMethod(str, Enum):
    MINIMIZE_TRADES = "MINIMIZE_TRADES"
    MINIMIZE_COSTS = "MINIMIZE_COSTS"
    RISK_AWARE = "RISK_AWARE"
    MOMENTUM_BASED = "MOMENTUM_BASED"  # New method

# Register the strategy
class EnhancedRebalancingEngine(RebalancingEngine):
    def __init__(self):
        super().__init__()
        self.strategies[ExtendedRebalancingMethod.MOMENTUM_BASED] = MomentumBasedStrategy()
```text
### Strategy Testing

```pythonthon
import pytest
from unittest.mock import MagicMock

class TestMomentumBasedStrategy:
    """Test cases for momentum-based strategy."""

    def setup_method(self):
        self.strategy = MomentumBasedStrategy(momentum_window=30)

    def test_should_prioritize_high_momentum_stocks_when_optimizing(self):
        # Arrange
        rebalancing_needs = [
            RebalancingNeed(
                symbol="AAPL",
                current_weight=0.2,
                target_weight=0.3,
                deviation=-0.1,
                tolerance_band=0.05,
                exceeds_tolerance=True,
                urgency_score=0.5,
                recommended_action=TradeAction.BUY
            )
        ]

        # Mock momentum data
        with patch.object(self.strategy, '_calculate_momentum_scores') as mock_momentum:
            mock_momentum.return_value = {"AAPL": 0.8}  # High momentum

            # Act
            result = self.strategy.optimize(
                rebalancing_needs=rebalancing_needs,
                current_portfolio=mock_portfolio,
                target_weights={"AAPL": 0.3},
                prices={"AAPL": 150.0},
                available_capital=10000.0,
                constraints=[],
                config=mock_config
            )

            # Assert
            assert len(result.trades) > 0
            assert result.method_used == "MOMENTUM_BASED"
```text
## Adding New Data Sources

### Price Data Integration

1. **Create Provider Class**

```pythonthon
from finwiz.tools.portfolio_price_service import PriceDataProvider
import aiohttp

class AlphaVantagePriceProvider(PriceDataProvider):
    """Alpha Vantage price data provider."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"

    async def get_current_price(self, symbol: str) -> PriceData:
        """Get current price from Alpha Vantage."""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                data = await response.json()

                if "Global Quote" not in data:
                    raise PriceDataError(symbol, "Invalid response from Alpha Vantage")

                quote = data["Global Quote"]
                price = float(quote["05. price"])

                return PriceData(
                    symbol=symbol,
                    price=price,
                    timestamp=datetime.now()
                )
```text
2. **Register with Price Service**

```pythonthon
from finwiz.tools.portfolio_price_service import PortfolioPriceService

class EnhancedPriceService(PortfolioPriceService):
    """Enhanced price service with multiple providers."""

    def __init__(self):
        super().__init__()
        self.providers = [
            YahooFinancePriceProvider(),
            AlphaVantagePriceProvider(api_key=os.getenv("ALPHA_VANTAGE_API_KEY")),
            # Add more providers as needed
        ]

    async def get_price_with_fallback(self, symbol: str) -> PriceData:
        """Try multiple providers in sequence."""
        for provider in self.providers:
            try:
                return await provider.get_current_price(symbol)
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed for {symbol}: {e}")
                continue

        raise PriceDataError(symbol, "All price providers failed")
```text
### Market Data Integration

```pythonthon
class MarketDataProvider:
    """Provider for additional market data (sectors, fundamentals, etc.)."""

    async def get_sector_data(self, symbols: List[str]) -> Dict[str, str]:
        """Get sector information for symbols."""
        # Implementation for sector data retrieval
        pass

    async def get_fundamental_data(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """Get fundamental metrics for symbols."""
        # Implementation for fundamental data retrieval
        pass
```text
## Custom Constraints

### Creating Constraint Classes

```pythonthon
from finwiz.quantitative.rebalancing_engine import OptimizationConstraint

class SectorConcentrationConstraint(OptimizationConstraint):
    """Constraint to limit sector concentration."""

    def __init__(self, max_sector_weight: float = 0.3):
        super().__init__(
            name="sector_concentration",
            constraint_type="sector_limit",
            value=max_sector_weight,
            description=f"Maximum {max_sector_weight:.0%} in any sector"
        )
        self.max_sector_weight = max_sector_weight

    def validate(
        self,
        trades: List[TradeRecommendation],
        current_portfolio: PortfolioAnalysis,
        market_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate sector concentration constraint."""

        # Calculate projected sector weights after trades
        projected_sectors = self._calculate_projected_sectors(
            trades, current_portfolio, market_data
        )

        violations = []
        for sector, weight in projected_sectors.items():
            if weight > self.max_sector_weight:
                violations.append(
                    f"Sector {sector} would be {weight:.1%}, "
                    f"exceeds limit of {self.max_sector_weight:.1%}"
                )

        return len(violations) == 0, violations

class ESGConstraint(OptimizationConstraint):
    """Constraint based on ESG (Environmental, Social, Governance) scores."""

    def __init__(self, min_esg_score: float = 7.0):
        super().__init__(
            name="esg_constraint",
            constraint_type="esg_limit",
            value=min_esg_score,
            description=f"Minimum ESG score of {min_esg_score}"
        )
        self.min_esg_score = min_esg_score

    def validate(
        self,
        trades: List[TradeRecommendation],
        current_portfolio: PortfolioAnalysis,
        esg_data: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """Validate ESG constraint."""

        violations = []
        for trade in trades:
            if trade.action == TradeAction.BUY:
                esg_score = esg_data.get(trade.symbol, 0.0)
                if esg_score < self.min_esg_score:
                    violations.append(
                        f"{trade.symbol} ESG score {esg_score} "
                        f"below minimum {self.min_esg_score}"
                    )

        return len(violations) == 0, violations
```text
### Using Custom Constraints

```pythonthon
# Create constraints
sector_constraint = SectorConcentrationConstraint(max_sector_weight=0.25)
esg_constraint = ESGConstraint(min_esg_score=8.0)

# Add to configuration
config = PortfolioConfiguration(
    holdings=holdings,
    target_weights=target_weights,
    custom_constraints=[sector_constraint, esg_constraint]
)

# The rebalancing engine will automatically validate these constraints
result = await orchestrator.rebalance_portfolio(config)
```text
## Testing Guidelines

### Unit Testing Best Practices

1. **Mock External Dependencies**

```pythonthon
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

class TestPortfolioRebalancingOrchestrator:
    """Unit tests for portfolio rebalancing orchestrator."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mocked dependencies."""
        return {
            "price_service": AsyncMock(spec=PortfolioPriceService),
            "portfolio_analyzer": MagicMock(spec=PortfolioAnalyzer),
            "rebalancing_engine": MagicMock(spec=RebalancingEngine),
            "report_generator": MagicMock(spec=HTMLReportGenerator)
        }

    @pytest.mark.asyncio
    async def test_should_handle_successful_rebalancing(self, mock_dependencies):
        """Test successful rebalancing workflow."""
        # Arrange
        orchestrator = PortfolioRebalancingOrchestrator(**mock_dependencies)
        config = PortfolioConfiguration(...)

        # Mock successful responses
        mock_dependencies["price_service"].get_current_prices.return_value = {...}
        mock_dependencies["portfolio_analyzer"].analyze_current_portfolio.return_value = ...
        mock_dependencies["rebalancing_engine"].generate_enhanced_trade_recommendations.return_value = ([], [])

        # Act
        result = await orchestrator.rebalance_portfolio(config)

        # Assert
        assert result is not None
        mock_dependencies["price_service"].get_current_prices.assert_called_once()
```text
2. **Test Error Scenarios**

```pythonthon
@pytest.mark.asyncio
async def test_should_handle_price_data_failure(self, mock_dependencies):
    """Test handling of price data failures."""
    # Arrange
    orchestrator = PortfolioRebalancingOrchestrator(**mock_dependencies)
    config = PortfolioConfiguration(...)

    # Mock price service failure
    mock_dependencies["price_service"].get_current_prices.side_effect = Exception("API Error")

    # Act & Assert
    with pytest.raises(InsufficientPriceDataError):
        await orchestrator.rebalance_portfolio(config)
```text
3. **Property-Based Testing**

```pythonthon
from hypothesis import given, strategies as st

@given(
    shares=st.floats(min_value=0.1, max_value=10000.0),
    price=st.floats(min_value=0.01, max_value=10000.0),
    target_weight=st.floats(min_value=0.01, max_value=1.0)
)
def test_weight_calculation_properties(shares, price, target_weight):
    """Test weight calculation properties with random inputs."""
    holding = Holding(symbol="TEST", shares=shares)
    prices = {"TEST": price}

    analyzer = PortfolioAnalyzer()
    weights = analyzer.calculate_current_weightings([holding], prices)

    # Properties that should always hold
    assert 0 <= weights["TEST"] <= 1.0
    assert abs(sum(weights.values()) - 1.0) < 1e-10
```text
### Integration Testing

```pythonthon
@pytest.mark.integration
class TestPortfolioRebalancingIntegration:
    """Integration tests using real components."""

    @pytest.mark.asyncio
    async def test_end_to_end_rebalancing_workflow(self):
        """Test complete workflow with real components."""
        # Use real components with mocked external APIs
        with patch("finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool") as mock_yahoo:
            mock_yahoo.return_value._run.return_value = {"current_price": 150.0}

            orchestrator = PortfolioRebalancingOrchestrator()
            config = PortfolioConfiguration(...)

            result = await orchestrator.rebalance_portfolio(config)

            assert result is not None
            # Verify real component interactions
```text
### Performance Testing

```pythonthon
@pytest.mark.performance
class TestPortfolioRebalancingPerformance:
    """Performance tests for rebalancing system."""

    def test_large_portfolio_performance(self, benchmark):
        """Benchmark performance with large portfolios."""

        def create_large_portfolio():
            holdings = [Holding(symbol=f"STOCK{i:03d}", shares=100.0) for i in range(100)]
            target_weights = {f"STOCK{i:03d}": 0.01 for i in range(100)}
            return PortfolioConfiguration(holdings=holdings, target_weights=target_weights)

        # Benchmark configuration creation
        config = benchmark(create_large_portfolio)
        assert len(config.holdings) == 100

    @pytest.mark.asyncio
    async def test_concurrent_rebalancing_performance(self):
        """Test performance under concurrent load."""
        import asyncio
        import time

        configs = [create_test_config() for _ in range(10)]
        orchestrator = PortfolioRebalancingOrchestrator()

        start_time = time.time()

        tasks = [orchestrator.rebalance_portfolio(config) for config in configs]
        results = await asyncio.gather(*tasks)

        end_time = time.time()

        # Should complete within reasonable time
        assert (end_time - start_time) < 30.0  # 30 seconds for 10 portfolios
        assert len(results) == 10
```text
## Performance Optimization

### Caching Strategies

```pythonthon
from functools import lru_cache
import asyncio

class OptimizedPortfolioAnalyzer(PortfolioAnalyzer):
    """Portfolio analyzer with caching optimizations."""

    def __init__(self):
        super().__init__()
        self._price_cache = {}
        self._analysis_cache = {}

    @lru_cache(maxsize=1000)
    def _calculate_portfolio_hash(self, holdings_tuple: tuple, prices_tuple: tuple) -> str:
        """Calculate hash for caching portfolio analysis."""
        import hashlib
        content = str(holdings_tuple) + str(prices_tuple)
        return hashlib.md5(content.encode()).hexdigest()

    def calculate_current_weightings(
        self,
        holdings: List[Holding],
        prices: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate weightings with caching."""

        # Create cache key
        holdings_tuple = tuple((h.symbol, h.shares) for h in holdings)
        prices_tuple = tuple(sorted(prices.items()))
        cache_key = self._calculate_portfolio_hash(holdings_tuple, prices_tuple)

        # Check cache
        if cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]

        # Calculate and cache
        result = super().calculate_current_weightings(holdings, prices)
        self._analysis_cache[cache_key] = result

        return result
```text
### Async Optimization

```pythonthon
class AsyncOptimizedPriceService(PortfolioPriceService):
    """Price service optimized for concurrent requests."""

    async def get_current_prices(self, symbols: List[str]) -> Dict[str, PriceData]:
        """Get prices with optimal concurrency."""

        # Batch symbols into optimal groups
        batch_size = 10
        batches = [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]

        # Process batches concurrently
        tasks = [self._get_batch_prices(batch) for batch in batches]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        all_prices = {}
        for batch_result in batch_results:
            if isinstance(batch_result, dict):
                all_prices.update(batch_result)
            else:
                # Handle exceptions
                logger.warning(f"Batch failed: {batch_result}")

        return all_prices

    async def _get_batch_prices(self, symbols: List[str]) -> Dict[str, PriceData]:
        """Get prices for a batch of symbols."""
        # Implement efficient batch retrieval
        pass
```text
### Memory Optimization

```pythonthon
import gc
from typing import Generator

class MemoryOptimizedAnalyzer:
    """Analyzer optimized for large portfolios."""

    def analyze_large_portfolio_streaming(
        self,
        holdings: List[Holding],
        prices: Dict[str, float]
    ) -> Generator[PortfolioMetrics, None, None]:
        """Analyze large portfolio in streaming fashion."""

        batch_size = 100

        for i in range(0, len(holdings), batch_size):
            batch = holdings[i:i + batch_size]
            batch_prices = {h.symbol: prices[h.symbol] for h in batch if h.symbol in prices}

            # Process batch
            batch_metrics = self.calculate_portfolio_metrics(batch, batch_prices)
            yield batch_metrics

            # Force garbage collection
            gc.collect()
```text
## Integration Patterns

### Dependency Injection

```pythonthon
from typing import Protocol

class PriceServiceProtocol(Protocol):
    """Protocol for price service implementations."""

    async def get_current_prices(self, symbols: List[str]) -> Dict[str, PriceData]:
        ...

class RebalancingServiceFactory:
    """Factory for creating rebalancing services with dependency injection."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def create_orchestrator(
        self,
        price_service: Optional[PriceServiceProtocol] = None
    ) -> PortfolioRebalancingOrchestrator:
        """Create orchestrator with injected dependencies."""

        if price_service is None:
            price_service = self._create_price_service()

        portfolio_analyzer = self._create_analyzer()
        rebalancing_engine = self._create_engine()
        report_generator = self._create_report_generator()

        return PortfolioRebalancingOrchestrator(
            price_service=price_service,
            portfolio_analyzer=portfolio_analyzer,
            rebalancing_engine=rebalancing_engine,
            report_generator=report_generator
        )

    def _create_price_service(self) -> PriceServiceProtocol:
        """Create price service based on configuration."""
        provider_type = self.config.get("price_provider", "yahoo")

        if provider_type == "yahoo":
            return YahooFinancePriceService()
        elif provider_type == "alpha_vantage":
            return AlphaVantagePriceService(self.config["alpha_vantage_api_key"])
        else:
            raise ValueError(f"Unknown price provider: {provider_type}")
```text
### Event-Driven Architecture

```pythonthon
from typing import Callable, List
import asyncio

class RebalancingEventBus:
    """Event bus for rebalancing system events."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to events."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event_type: str, event_data: Any) -> None:
        """Publish event to subscribers."""
        if event_type in self._handlers:
            tasks = [handler(event_data) for handler in self._handlers[event_type]]
            await asyncio.gather(*tasks, return_exceptions=True)

class EventDrivenOrchestrator(PortfolioRebalancingOrchestrator):
    """Orchestrator with event publishing."""

    def __init__(self, event_bus: RebalancingEventBus, **kwargs):
        super().__init__(**kwargs)
        self.event_bus = event_bus

    async def rebalance_portfolio(
        self,
        config: PortfolioConfiguration,
        portfolio_id: Optional[str] = None
    ) -> RebalancingResult:
        """Rebalance with event publishing."""

        # Publish start event
        await self.event_bus.publish("rebalancing_started", {
            "portfolio_id": portfolio_id,
            "config": config
        })

        try:
            result = await super().rebalance_portfolio(config, portfolio_id)

            # Publish success event
            await self.event_bus.publish("rebalancing_completed", {
                "portfolio_id": portfolio_id,
                "result": result
            })

            return result

        except Exception as e:
            # Publish error event
            await self.event_bus.publish("rebalancing_failed", {
                "portfolio_id": portfolio_id,
                "error": str(e)
            })
            raise
```text
## Deployment Considerations

### Configuration Management

```pythonthon
from pydantic import BaseSettings

class RebalancingSettings(BaseSettings):
    """Configuration settings for rebalancing system."""

    # API Keys
    yahoo_finance_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None

    # Performance settings
    max_concurrent_requests: int = 10
    request_timeout: float = 30.0
    cache_ttl: int = 300  # 5 minutes

    # Default rebalancing parameters
    default_tolerance: float = 0.05
    default_transaction_cost_rate: float = 0.001
    default_min_trade_size: float = 100.0

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        env_prefix = "REBALANCING_"

# Usage
settings = RebalancingSettings()
orchestrator = PortfolioRebalancingOrchestrator(
    price_service=create_price_service(settings),
    # ... other components
)
```text
### Monitoring and Observability

```pythonthon
import logging
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)

            # Log success metrics
            duration = time.time() - start_time
            logging.info(f"{func.__name__} completed in {duration:.2f}s")

            return result

        except Exception as e:
            # Log error metrics
            duration = time.time() - start_time
            logging.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise

    return wrapper

class MonitoredOrchestrator(PortfolioRebalancingOrchestrator):
    """Orchestrator with monitoring."""

    @monitor_performance
    async def rebalance_portfolio(self, *args, **kwargs):
        return await super().rebalance_portfolio(*args, **kwargs)
```text
### Health Checks

```pythonthon
class RebalancingHealthCheck:
    """Health check for rebalancing system."""

    def __init__(self, orchestrator: PortfolioRebalancingOrchestrator):
        self.orchestrator = orchestrator

    async def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""

        health_status = {
            "status": "healthy",
            "checks": {},
            "timestamp": datetime.now().isoformat()
        }

        # Check price service
        try:
            test_price = await self.orchestrator.price_service.get_current_price("AAPL")
            health_status["checks"]["price_service"] = "healthy"
        except Exception as e:
            health_status["checks"]["price_service"] = f"unhealthy: {e}"
            health_status["status"] = "degraded"

        # Check analyzer
        try:
            test_holdings = [Holding(symbol="AAPL", shares=1.0)]
            test_prices = {"AAPL": 150.0}
            self.orchestrator.portfolio_analyzer.calculate_current_weightings(test_holdings, test_prices)
            health_status["checks"]["analyzer"] = "healthy"
        except Exception as e:
            health_status["checks"]["analyzer"] = f"unhealthy: {e}"
            health_status["status"] = "unhealthy"

        return health_status
```text
This developer guide provides comprehensive information for extending and integrating with the portfolio rebalancing system, enabling developers to customize the system for their specific needs while maintaining code quality and performance.
