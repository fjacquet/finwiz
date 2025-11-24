"""
Unit tests for performance analysis and portfolio optimization functionality.

Tests cover:
- Performance metrics calculations (Sharpe ratio, maximum drawdown, returns)
- Portfolio optimization using PyPortfolioOpt
- Performance visualization and reporting
- Risk-adjusted return analysis and benchmarking
"""

from pytest import approx
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from finwiz.quantitative.config import BacktestConfig
from finwiz.quantitative.performance import (
    PerformanceAnalyzer,
    get_performance_analyzer,
)
from finwiz.quantitative.performance_benchmarks import (
    PerformanceReport,
    PortfolioOptimizationResult,
)
from finwiz.quantitative.performance_metrics import PerformanceMetrics


class TestPerformanceAnalyzer:
    """Test suite for PerformanceAnalyzer class."""

    @pytest.fixture
    def sample_returns(self):
        """Generate sample return data for testing."""
        np.random.seed(42)
        dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
        returns = pd.Series(
            np.random.normal(0.001, 0.02, len(dates)),  # 0.1% daily return, 2% volatility
            index=dates,
            name="returns",
        )
        return returns

    @pytest.fixture
    def sample_benchmark_returns(self):
        """Generate sample benchmark return data for testing."""
        np.random.seed(123)
        dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
        returns = pd.Series(
            np.random.normal(0.0008, 0.015, len(dates)),  # 0.08% daily return, 1.5% volatility
            index=dates,
            name="benchmark_returns",
        )
        return returns

    @pytest.fixture
    def sample_price_data(self):
        """Generate sample price data for portfolio optimization testing."""
        np.random.seed(42)
        dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")

        # Generate correlated price series for 4 assets
        n_assets = 4
        n_days = len(dates)

        # Create correlation matrix
        correlation = np.array([[1.0, 0.3, 0.2, 0.1], [0.3, 1.0, 0.4, 0.2], [0.2, 0.4, 1.0, 0.3], [0.1, 0.2, 0.3, 1.0]])

        # Generate returns using multivariate normal
        returns = np.random.multivariate_normal(
            mean=[0.001, 0.0008, 0.0012, 0.0006],  # Different expected returns
            cov=correlation * 0.0004,  # Scale correlation to reasonable volatility
            size=n_days,
        )

        # Convert to prices starting from 100
        prices = np.zeros((n_days, n_assets))
        prices[0] = [100, 100, 100, 100]

        for i in range(1, n_days):
            prices[i] = prices[i - 1] * (1 + returns[i])

        price_df = pd.DataFrame(prices, index=dates, columns=["AAPL", "MSFT", "GOOGL", "AMZN"])

        return price_df

    @pytest.fixture
    def sample_trades(self):
        """Generate sample trade data for testing."""
        trades = pd.DataFrame(
            {
                "date": pd.date_range(start="2023-01-01", periods=10, freq="10D"),
                "symbol": ["AAPL"] * 10,
                "quantity": [100, -50, 75, -100, 200, -150, 50, -25, 100, -200],
                "price": [150, 155, 148, 160, 145, 170, 165, 168, 172, 175],
                "pnl": [500, -250, 375, -1000, 1000, -750, 250, -125, 400, -600],
            }
        )
        return trades

    @pytest.fixture
    def performance_analyzer(self):
        """Create PerformanceAnalyzer instance for testing."""
        config = BacktestConfig(initial_capital=100000.0, risk_free_rate=0.02, commission_pct=0.001)
        return PerformanceAnalyzer(config)

    def test_performance_analyzer_initialization(self):
        """Test PerformanceAnalyzer initialization."""
        analyzer = PerformanceAnalyzer()
        assert analyzer.config is not None
        assert analyzer.logger is not None

        # Test with custom config
        custom_config = BacktestConfig(risk_free_rate=0.03)
        analyzer_custom = PerformanceAnalyzer(custom_config)
        assert analyzer_custom.config.risk_free_rate == approx(0.03)

    def test_calculate_performance_metrics_basic(self, performance_analyzer, sample_returns):
        """Test basic performance metrics calculation."""
        metrics = performance_analyzer.metrics_calculator.calculate_performance_metrics(sample_returns)

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.total_return is not None
        assert metrics.annualized_return is not None
        assert metrics.sharpe_ratio is not None
        assert metrics.max_drawdown is not None
        assert metrics.volatility is not None
        assert metrics.max_drawdown_duration >= 0

    def test_calculate_performance_metrics_with_trades(self, performance_analyzer, sample_returns, sample_trades):
        """Test performance metrics calculation with trade data."""
        metrics = performance_analyzer.metrics_calculator.calculate_performance_metrics(sample_returns, sample_trades)

        assert metrics.win_rate is not None
        assert metrics.profit_factor is not None
        assert metrics.avg_win is not None
        assert metrics.avg_loss is not None
        assert 0 <= metrics.win_rate <= 100  # win_rate is a percentage (0-100)

    def test_calculate_max_drawdown(self, performance_analyzer):
        """Test maximum drawdown calculation."""
        # Create returns with known drawdown
        returns = pd.Series([0.1, -0.05, -0.1, -0.05, 0.15, 0.05, -0.2, 0.1])

        max_dd, duration = performance_analyzer.metrics_calculator.calculate_max_drawdown(returns)

        assert max_dd < 0  # Drawdown should be negative
        assert duration > 0  # Duration should be positive
        assert isinstance(max_dd, float)
        assert isinstance(duration, int)

    def test_calculate_downside_deviation(self, performance_analyzer):
        """Test downside deviation calculation."""
        returns = pd.Series([0.1, -0.05, 0.02, -0.1, 0.08, -0.03, 0.05, -0.08])

        downside_dev = performance_analyzer.metrics_calculator.calculate_downside_deviation(returns)

        assert downside_dev >= 0
        assert isinstance(downside_dev, float)

        # Test with target return
        downside_dev_target = performance_analyzer.metrics_calculator.calculate_downside_deviation(returns, target_return=0.01)
        assert downside_dev_target >= 0

    def test_analyze_performance_strategy_only(self, performance_analyzer, sample_returns):
        """Test performance analysis with strategy returns only."""
        report = performance_analyzer.analyze_performance(returns=sample_returns, strategy_name="Test Strategy")

        assert isinstance(report, PerformanceReport)
        assert report.strategy_name == "Test Strategy"
        assert report.strategy_metrics is not None
        assert report.benchmark_metrics is None
        assert report.relative_performance is None
        assert "dates" in report.equity_curve_data
        assert "strategy_equity" in report.equity_curve_data

    def test_analyze_performance_with_benchmark(self, performance_analyzer, sample_returns, sample_benchmark_returns):
        """Test performance analysis with benchmark comparison."""
        report = performance_analyzer.analyze_performance(
            returns=sample_returns,
            benchmark_returns=sample_benchmark_returns,
            strategy_name="Test Strategy",
            benchmark_name="Test Benchmark",
        )

        assert report.benchmark_name == "Test Benchmark"
        assert report.benchmark_metrics is not None
        assert report.relative_performance is not None
        assert "excess_return" in report.relative_performance
        assert "relative_sharpe" in report.relative_performance
        assert "benchmark_equity" in report.equity_curve_data

    def test_calculate_relative_performance(self, performance_analyzer):
        """Test relative performance calculation."""
        strategy_metrics = PerformanceMetrics(
            total_return=0.15,
            annualized_return=0.12,
            daily_return_mean=0.001,
            daily_return_std=0.02,
            sharpe_ratio=1.5,
            sortino_ratio=1.8,
            calmar_ratio=0.8,
            max_drawdown=-0.1,
            max_drawdown_duration=30,
            volatility=0.2,
            downside_deviation=0.15,
            var_95=-0.03,
            cvar_95=-0.05,
            skewness=0.1,
            kurtosis=3.2,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            total_days=365,
            trading_days=252,
        )

        benchmark_metrics = PerformanceMetrics(
            total_return=0.10,
            annualized_return=0.08,
            daily_return_mean=0.0008,
            daily_return_std=0.015,
            sharpe_ratio=1.2,
            sortino_ratio=1.4,
            calmar_ratio=0.6,
            max_drawdown=-0.08,
            max_drawdown_duration=25,
            volatility=0.18,
            downside_deviation=0.12,
            var_95=-0.025,
            cvar_95=-0.04,
            skewness=0.05,
            kurtosis=3.0,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            total_days=365,
            trading_days=252,
        )

        relative_perf = performance_analyzer.metrics_calculator.calculate_relative_performance(strategy_metrics, benchmark_metrics)

        assert "excess_return" in relative_perf
        assert "relative_sharpe" in relative_perf
        assert relative_perf["excess_return"] == pytest.approx(0.04, rel=1e-2)  # 0.12 - 0.08
        assert relative_perf["relative_sharpe"] == pytest.approx(0.3, rel=1e-2)  # 1.5 - 1.2

    def test_optimize_portfolio_max_sharpe_mock_available(self, performance_analyzer, sample_price_data, mocker):
        """Test portfolio optimization with max Sharpe method when PyPortfolioOpt is available."""
        # Mock PyPortfolioOpt components
        mocker.patch("finwiz.quantitative.performance_benchmarks.PYPFOPT_AVAILABLE", True)
        mock_expected_returns = mocker.patch("finwiz.quantitative.performance_benchmarks.expected_returns")
        mock_risk_models = mocker.patch("finwiz.quantitative.performance_benchmarks.risk_models")
        mock_ef_class = mocker.patch("finwiz.quantitative.performance_benchmarks.EfficientFrontier")

        # Configure mocks
        mock_expected_returns.mean_historical_return.return_value = pd.Series([0.12, 0.10, 0.11, 0.09], index=["AAPL", "MSFT", "GOOGL", "AMZN"])
        mock_risk_models.sample_cov.return_value = pd.DataFrame(
            [[0.04, 0.02, 0.01, 0.01], [0.02, 0.03, 0.01, 0.01], [0.01, 0.01, 0.02, 0.01], [0.01, 0.01, 0.01, 0.025]],
            index=["AAPL", "MSFT", "GOOGL", "AMZN"],
            columns=["AAPL", "MSFT", "GOOGL", "AMZN"],
        )

        mock_ef = mocker.MagicMock()
        mock_ef_class.return_value = mock_ef
        mock_ef.max_sharpe.return_value = {"AAPL": 0.4, "MSFT": 0.3, "GOOGL": 0.2, "AMZN": 0.1}
        mock_ef.clean_weights.return_value = {"AAPL": 0.4, "MSFT": 0.3, "GOOGL": 0.2, "AMZN": 0.1}
        mock_ef.portfolio_performance.return_value = (0.105, 0.18, 0.50)

        # Test optimization
        result = performance_analyzer.optimize_portfolio(price_data=sample_price_data, optimization_method="max_sharpe")

        # Verify result structure
        assert isinstance(result, PortfolioOptimizationResult)
        assert result.optimal_weights is not None
        assert len(result.optimal_weights) == 4
        assert result.sharpe_ratio is not None

    def test_optimize_portfolio_pypfopt_unavailable(self, performance_analyzer, sample_price_data, mocker):
        """Test portfolio optimization when PyPortfolioOpt is not available."""
        mocker.patch("finwiz.quantitative.performance_benchmarks.PYPFOPT_AVAILABLE", False)
        with pytest.raises(ValueError, match="PyPortfolioOpt is not available"):
            performance_analyzer.optimize_portfolio(sample_price_data)

    def test_optimize_portfolio_invalid_method(self, performance_analyzer, sample_price_data, mocker):
        """Test portfolio optimization with invalid method."""
        mocker.patch("finwiz.quantitative.performance_benchmarks.PYPFOPT_AVAILABLE", True)
        with pytest.raises(ValueError, match="Unknown optimization method"):
            performance_analyzer.optimize_portfolio(sample_price_data, optimization_method="invalid_method")

    def test_optimize_portfolio_empty_data(self, performance_analyzer, mocker):
        """Test portfolio optimization with empty price data."""
        empty_data = pd.DataFrame()

        mocker.patch("finwiz.quantitative.performance_benchmarks.PYPFOPT_AVAILABLE", True)
        with pytest.raises(ValueError, match="At least 2 assets are required"):
            performance_analyzer.optimize_portfolio(empty_data)

    def test_generate_equity_curve_data(self, performance_analyzer, sample_returns, sample_benchmark_returns):
        """Test equity curve data generation."""
        data = performance_analyzer.metrics_calculator.generate_equity_curve_data(sample_returns, sample_benchmark_returns)

        assert "dates" in data
        assert "strategy_equity" in data
        assert "benchmark_equity" in data
        assert len(data["dates"]) == len(sample_returns)
        assert len(data["strategy_equity"]) == len(sample_returns)
        assert len(data["benchmark_equity"]) == len(sample_benchmark_returns)

    def test_generate_drawdown_data(self, performance_analyzer, sample_returns):
        """Test drawdown data generation."""
        data = performance_analyzer.metrics_calculator.generate_drawdown_data(sample_returns)

        assert "dates" in data
        assert "drawdown" in data
        assert len(data["dates"]) == len(sample_returns)
        assert len(data["drawdown"]) == len(sample_returns)
        assert all(dd <= 0 for dd in data["drawdown"])  # Drawdowns should be negative or zero

    def test_generate_returns_distribution_data(self, performance_analyzer, sample_returns, sample_benchmark_returns):
        """Test returns distribution data generation."""
        data = performance_analyzer.metrics_calculator.generate_returns_distribution_data(sample_returns, sample_benchmark_returns)

        assert "strategy_returns" in data
        assert "benchmark_returns" in data
        assert len(data["strategy_returns"]) == len(sample_returns)
        assert len(data["benchmark_returns"]) == len(sample_benchmark_returns)

    def test_generate_performance_visualization_mock_available(self, performance_analyzer, sample_returns, mocker):
        """Test performance visualization generation when Plotly is mocked as available."""
        # Mock Plotly components
        mocker.patch("finwiz.quantitative.performance_benchmarks.PLOTLY_AVAILABLE", True)
        mock_go = mocker.patch("finwiz.quantitative.performance_benchmarks.go")
        mock_make_subplots = mocker.patch("finwiz.quantitative.performance_benchmarks.make_subplots")

        # Configure mocks
        mock_fig = mocker.MagicMock()
        mock_make_subplots.return_value = mock_fig

        # Create a mock performance report
        report = performance_analyzer.analyze_performance(sample_returns, strategy_name="Test")

        # Test visualization generation
        fig = performance_analyzer.generate_performance_visualization(report)

        # Verify figure was created
        assert fig is not None
        mock_make_subplots.assert_called_once()

    def test_generate_performance_visualization_plotly_unavailable(self, performance_analyzer, sample_returns, mocker):
        """Test performance visualization when Plotly is not available."""
        mocker.patch("finwiz.quantitative.performance_benchmarks.PLOTLY_AVAILABLE", False)
        report = performance_analyzer.analyze_performance(sample_returns, strategy_name="Test")

        # When Plotly is unavailable, the method returns None and logs a warning
        result = performance_analyzer.generate_performance_visualization(report)
        assert result is None

    def test_generate_optimization_visualization_mock_available(self, performance_analyzer, mocker):
        """Test optimization visualization generation when Plotly is available."""
        # Mock Plotly components
        mocker.patch("finwiz.quantitative.performance_benchmarks.PLOTLY_AVAILABLE", True)

        # Create a proper mock for go.Pie that returns a dict-like object
        mock_pie_trace = {"type": "pie", "labels": [], "values": []}
        mock_go = mocker.patch("finwiz.quantitative.performance_benchmarks.go")
        mock_go.Pie.return_value = mock_pie_trace

        # Mock Figure class
        mock_fig = mocker.MagicMock()
        mock_go.Figure.return_value = mock_fig

        # Create optimization result
        optimization_result = PortfolioOptimizationResult(
            optimal_weights={"AAPL": 0.4, "MSFT": 0.3, "GOOGL": 0.2, "AMZN": 0.1},
            expected_return=0.10,
            volatility=0.15,
            sharpe_ratio=0.6,
        )

        # Generate visualization
        fig = performance_analyzer.generate_optimization_visualization(optimization_result)

        # Verify figure was created
        assert fig is not None

    def test_generate_optimization_visualization_plotly_unavailable(self, performance_analyzer, mocker):
        """Test optimization visualization when Plotly is not available."""
        mocker.patch("finwiz.quantitative.performance_benchmarks.PLOTLY_AVAILABLE", False)
        optimization_result = PortfolioOptimizationResult(
            optimal_weights={"AAPL": 0.4, "MSFT": 0.3, "GOOGL": 0.2, "AMZN": 0.1},
            expected_return=0.10,
            volatility=0.15,
            sharpe_ratio=0.6,
        )

        # When Plotly is unavailable, the method returns None and logs a warning
        result = performance_analyzer.generate_optimization_visualization(optimization_result)
        assert result is None

    def test_get_performance_analyzer_factory(self):
        """Test the factory function for creating PerformanceAnalyzer instances."""
        analyzer = get_performance_analyzer()
        assert isinstance(analyzer, PerformanceAnalyzer)

        # Test with custom config
        custom_config = BacktestConfig(risk_free_rate=0.03)
        analyzer_custom = get_performance_analyzer(custom_config)
        assert analyzer_custom.config.risk_free_rate == approx(0.03)


class TestPerformanceMetrics:
    """Test suite for PerformanceMetrics model."""

    def test_performance_metrics_validation(self):
        """Test PerformanceMetrics model validation."""
        metrics = PerformanceMetrics(
            total_return=0.15,
            annualized_return=0.12,
            sharpe_ratio=1.5,
            sortino_ratio=1.8,
            calmar_ratio=0.8,
            max_drawdown=-0.1,
            max_drawdown_duration=30,
            volatility=0.2,
            downside_deviation=0.15,
            var_95=-0.03,
            cvar_95=-0.05,
            skewness=0.1,
            kurtosis=3.2,
        )

        assert metrics.total_return == approx(0.15)
        assert metrics.sharpe_ratio == approx(1.5)
        assert metrics.max_drawdown == approx(-0.1)
        assert metrics.max_drawdown_duration == 30


class TestPortfolioOptimizationResult:
    """Test suite for PortfolioOptimizationResult model."""

    def test_portfolio_optimization_result_validation(self):
        """Test PortfolioOptimizationResult model validation."""
        result = PortfolioOptimizationResult(
            optimal_weights={"AAPL": 0.4, "MSFT": 0.3, "GOOGL": 0.2, "AMZN": 0.1},
            expected_return=0.10,
            volatility=0.15,
            sharpe_ratio=0.6,
        )

        assert len(result.optimal_weights) == 4
        assert sum(result.optimal_weights.values()) == pytest.approx(1.0, rel=1e-2)
        assert result.expected_return == approx(0.10)


class TestPerformanceReport:
    """Test suite for PerformanceReport model."""

    def test_performance_report_validation(self):
        """Test PerformanceReport model validation."""
        metrics = PerformanceMetrics(
            total_return=0.15,
            annualized_return=0.12,
            daily_return_mean=0.001,
            daily_return_std=0.02,
            sharpe_ratio=1.5,
            sortino_ratio=1.8,
            calmar_ratio=0.8,
            max_drawdown=-0.1,
            max_drawdown_duration=30,
            volatility=0.2,
            downside_deviation=0.15,
            var_95=-0.03,
            cvar_95=-0.05,
            skewness=0.1,
            kurtosis=3.2,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            total_days=365,
            trading_days=252,
        )

        report = PerformanceReport(
            strategy_metrics=metrics,
            strategy_name="Test Strategy",
            analysis_period="2023-01-01 to 2023-12-31",
            total_observations=365,
        )

        assert report.strategy_name == "Test Strategy"
        assert report.strategy_metrics == metrics
        assert report.analysis_period == "2023-01-01 to 2023-12-31"


class TestPerformanceAnalysisIntegration:
    """Integration tests for performance analysis components."""

    @pytest.fixture
    def realistic_returns(self):
        """Generate realistic return data for integration testing."""
        np.random.seed(42)
        dates = pd.date_range(start="2022-01-01", end="2023-12-31", freq="D")

        # Generate returns with some realistic patterns
        base_return = 0.0008  # ~20% annual return
        volatility = 0.015  # ~24% annual volatility

        returns = []
        for i in range(len(dates)):
            # Add some momentum and mean reversion
            if i == 0:
                ret = np.random.normal(base_return, volatility)
            else:
                momentum = 0.1 * returns[i - 1] if i > 0 else 0
                mean_reversion = -0.05 * (sum(returns[-5:]) / 5 if i >= 5 else 0)
                ret = np.random.normal(base_return + momentum + mean_reversion, volatility)
            returns.append(ret)

        return pd.Series(returns, index=dates, name="returns")

    def test_end_to_end_performance_analysis(self, realistic_returns):
        """Test complete performance analysis workflow."""
        analyzer = PerformanceAnalyzer()

        # Perform analysis
        report = analyzer.analyze_performance(returns=realistic_returns, strategy_name="Realistic Strategy Test")

        # Verify report structure
        assert isinstance(report, PerformanceReport)
        assert report.strategy_name == "Realistic Strategy Test"

        # Verify metrics are reasonable
        metrics = report.strategy_metrics
        assert -1 < metrics.total_return < 2  # Reasonable total return range
        assert -1 < metrics.annualized_return < 1  # Reasonable annual return range
        assert 0 < metrics.volatility < 1  # Reasonable volatility range
        assert metrics.max_drawdown <= 0  # Drawdown should be negative
        # Note: trading_days field was removed from PerformanceMetrics schema

        # Verify visualization data
        assert "dates" in report.equity_curve_data
        assert "strategy_equity" in report.equity_curve_data
        assert len(report.equity_curve_data["dates"]) == len(realistic_returns)

    def test_end_to_end_portfolio_optimization(self, mocker):
        """Test complete portfolio optimization workflow."""
        # Generate sample price data
        np.random.seed(42)
        dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")

        # Create price data for 3 assets with different characteristics
        price_data = pd.DataFrame(index=dates)

        # Asset 1: High return, high volatility
        returns_1 = np.random.normal(0.0012, 0.025, len(dates))
        price_data["TECH"] = 100 * (1 + pd.Series(returns_1, index=dates)).cumprod()

        # Asset 2: Medium return, medium volatility
        returns_2 = np.random.normal(0.0008, 0.018, len(dates))
        price_data["GROWTH"] = 100 * (1 + pd.Series(returns_2, index=dates)).cumprod()

        # Asset 3: Low return, low volatility
        returns_3 = np.random.normal(0.0004, 0.012, len(dates))
        price_data["BOND"] = 100 * (1 + pd.Series(returns_3, index=dates)).cumprod()

        analyzer = PerformanceAnalyzer()

        # Mock the optimization components
        mocker.patch("finwiz.quantitative.performance_benchmarks.PYPFOPT_AVAILABLE", True)
        mock_expected_returns = mocker.patch("finwiz.quantitative.performance_benchmarks.expected_returns")
        mock_risk_models = mocker.patch("finwiz.quantitative.performance_benchmarks.risk_models")
        mock_ef_class = mocker.patch("finwiz.quantitative.performance_benchmarks.EfficientFrontier")

        # Mock DiscreteAllocation to avoid solver issues
        mock_da_class = mocker.patch("finwiz.quantitative.performance_benchmarks.DiscreteAllocation")
        mock_da = mocker.MagicMock()
        mock_da_class.return_value = mock_da
        mock_da.lp_portfolio.return_value = ({"TECH": 50, "GROWTH": 30, "BOND": 20}, 0.0)

        mock_expected_returns.mean_historical_return.return_value = pd.Series([0.12, 0.08, 0.04], index=["TECH", "GROWTH", "BOND"])
        mock_risk_models.sample_cov.return_value = pd.DataFrame(
            [[0.04, 0.02, 0.01], [0.02, 0.03, 0.01], [0.01, 0.01, 0.02]],
            index=["TECH", "GROWTH", "BOND"],
            columns=["TECH", "GROWTH", "BOND"],
        )

        mock_ef = mocker.MagicMock()
        mock_ef_class.return_value = mock_ef
        mock_ef.max_sharpe.return_value = {"TECH": 0.5, "GROWTH": 0.3, "BOND": 0.2}
        mock_ef.clean_weights.return_value = {"TECH": 0.5, "GROWTH": 0.3, "BOND": 0.2}
        mock_ef.portfolio_performance.return_value = (0.095, 0.18, 0.42)

        # Perform optimization
        result = analyzer.optimize_portfolio(price_data=price_data, optimization_method="max_sharpe", total_portfolio_value=100000)

        # Verify optimization result
        assert isinstance(result, PortfolioOptimizationResult)
        # Note: optimization_method field doesn't exist in schema
        assert len(result.optimal_weights) == 3
        assert all(asset in result.optimal_weights for asset in ["TECH", "GROWTH", "BOND"])
        assert 0.09 < result.expected_return < 0.10
        assert 0.17 < result.volatility < 0.19
        assert result.sharpe_ratio > 0