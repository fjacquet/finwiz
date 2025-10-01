"""
Test quantitative backtesting integration backward compatibility.

This module tests that quantitative backtesting integration continues to work
after the core analysis restoration.
"""

import os

import pytest


class TestQuantitativeBackwardCompatibility:
    """Test quantitative backtesting backward compatibility."""

    def test_quantitative_tools_importable(self):
        """Test that quantitative analysis tools remain importable."""
        try:
            from finwiz.tools.backtesting_tool import BacktestingTool
            from finwiz.tools.portfolio_analysis_tool import PortfolioAnalysisTool
            from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool

            # Verify tools can be imported
            assert QuantitativeAnalysisTool is not None
            assert BacktestingTool is not None
            assert PortfolioAnalysisTool is not None

        except ImportError as e:
            pytest.fail(f"Quantitative tool import failed: {e}")

    def test_quantitative_modules_importable(self):
        """Test that quantitative modules remain importable."""
        try:
            from finwiz.quantitative.performance import PerformanceAnalyzer
            from finwiz.quantitative.portfolio_analyzer import PortfolioAnalyzer
            from finwiz.quantitative.risk_manager import RiskManager
            from finwiz.quantitative.technical import TechnicalAnalysisEngine

            # Verify modules can be imported
            assert PerformanceAnalyzer is not None
            assert RiskManager is not None
            assert PortfolioAnalyzer is not None
            assert TechnicalAnalysisEngine is not None

        except ImportError as e:
            pytest.fail(f"Quantitative module import failed: {e}")

    def test_quantitative_tool_instantiation(self, mocker):
        """Test that quantitative tools can be instantiated."""
        try:
            from finwiz.tools.backtesting_tool import BacktestingTool
            from finwiz.tools.portfolio_analysis_tool import PortfolioAnalysisTool
            from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool

            # Mock environment variables to avoid configuration errors
            mocker.patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "test-key",
                    "SERPER_API_KEY": "test-key",
                    "FIRECRAWL_API_KEY": "test-key",
                    "ALPHA_VANTAGE_API_KEY": "test-key",
                },
            )

            # Should be able to create tool instances
            quant_tool = QuantitativeAnalysisTool()
            backtest_tool = BacktestingTool()
            portfolio_tool = PortfolioAnalysisTool()

            # Verify tools have expected methods
            assert hasattr(quant_tool, "_run")
            assert hasattr(backtest_tool, "_run")
            assert hasattr(portfolio_tool, "_run")

            # Verify tools are callable
            assert callable(quant_tool._run)
            assert callable(backtest_tool._run)
            assert callable(portfolio_tool._run)

        except Exception as e:
            pytest.fail(f"Quantitative tool instantiation failed: {e}")

    def test_quantitative_schemas_importable(self):
        """Test that quantitative schemas remain importable."""
        try:
            from finwiz.schemas.quantitative import BacktestResult, PerformanceMetrics, PortfolioAnalysis, RiskMetrics

            # Verify schemas can be imported
            assert BacktestResult is not None
            assert PerformanceMetrics is not None
            assert RiskMetrics is not None
            assert PortfolioAnalysis is not None

        except ImportError as e:
            pytest.fail(f"Quantitative schema import failed: {e}")

    def test_quantitative_engine_instantiation(self):
        """Test that quantitative engines can be instantiated."""
        try:
            from finwiz.quantitative.backtesting import BacktestEngine
            from finwiz.quantitative.performance import PerformanceAnalyzer
            from finwiz.quantitative.risk_manager import RiskManager

            # Should be able to create engine instances
            backtest_engine = BacktestEngine()
            performance_analyzer = PerformanceAnalyzer()
            risk_manager = RiskManager()

            # Verify engines have expected methods
            assert hasattr(backtest_engine, "run_backtest")
            assert hasattr(performance_analyzer, "calculate_metrics")
            assert hasattr(risk_manager, "assess_risk")

        except Exception as e:
            pytest.fail(f"Quantitative engine instantiation failed: {e}")

    def test_quantitative_integration_with_crews(self):
        """Test that quantitative tools can be used by crews."""
        try:
            # Test that crews can import and use quantitative tools
            from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool

            # Verify that quantitative tools are available for crew use
            quant_tool = QuantitativeAnalysisTool()
            assert hasattr(quant_tool, "name")
            assert hasattr(quant_tool, "description")
            assert hasattr(quant_tool, "_run")

            # Verify tool has expected properties for CrewAI integration
            assert isinstance(quant_tool.name, str)
            assert isinstance(quant_tool.description, str)
            assert callable(quant_tool._run)

        except Exception as e:
            pytest.fail(f"Quantitative integration with crews failed: {e}")

    def test_portfolio_analysis_backward_compatibility(self):
        """Test that portfolio analysis maintains backward compatibility."""
        try:
            from finwiz.quantitative.portfolio_analyzer import PortfolioAnalyzer
            from finwiz.tools.portfolio_analysis_tool import PortfolioAnalysisTool

            # Test that portfolio analyzer maintains expected interface
            analyzer = PortfolioAnalyzer()
            tool = PortfolioAnalysisTool()

            # Verify expected methods exist
            assert hasattr(analyzer, "analyze_portfolio")
            assert hasattr(tool, "_run")

            # Verify methods are callable
            assert callable(analyzer.analyze_portfolio)
            assert callable(tool._run)

        except Exception as e:
            pytest.fail(f"Portfolio analysis backward compatibility failed: {e}")

    def test_risk_assessment_integration(self):
        """Test that risk assessment tools integrate properly."""
        try:
            from finwiz.quantitative.risk_manager import RiskManager
            from finwiz.tools.risk_assessment_tool import RiskAssessmentTool

            # Test that risk tools maintain expected interface
            risk_manager = RiskManager()
            risk_tool = RiskAssessmentTool()

            # Verify expected methods exist
            assert hasattr(risk_manager, "assess_risk")
            assert hasattr(risk_tool, "_run")

            # Verify methods are callable
            assert callable(risk_manager.assess_risk)
            assert callable(risk_tool._run)

        except Exception as e:
            pytest.fail(f"Risk assessment integration failed: {e}")

    def test_backtesting_framework_compatibility(self):
        """Test that backtesting framework maintains compatibility."""
        try:
            from finwiz.quantitative.backtesting import BacktestEngine
            from finwiz.tools.backtesting_tool import BacktestingTool

            # Test that backtesting maintains expected interface
            engine = BacktestEngine()
            tool = BacktestingTool()

            # Verify expected methods exist
            assert hasattr(engine, "run_backtest")
            assert hasattr(tool, "_run")

            # Verify methods are callable
            assert callable(engine.run_backtest)
            assert callable(tool._run)

        except Exception as e:
            pytest.fail(f"Backtesting framework compatibility failed: {e}")

    def test_performance_metrics_compatibility(self):
        """Test that performance metrics maintain compatibility."""
        try:
            from finwiz.quantitative.performance import PerformanceAnalyzer
            from finwiz.schemas.quantitative import PerformanceMetrics

            # Test that performance analysis maintains expected interface
            analyzer = PerformanceAnalyzer()

            # Verify expected methods exist
            assert hasattr(analyzer, "calculate_metrics")
            assert hasattr(analyzer, "calculate_sharpe_ratio")
            assert hasattr(analyzer, "calculate_max_drawdown")

            # Verify schema exists and has expected structure
            assert hasattr(PerformanceMetrics, "__annotations__")

        except Exception as e:
            pytest.fail(f"Performance metrics compatibility failed: {e}")

    def test_quantitative_data_integration(self):
        """Test that quantitative analysis integrates with data systems."""
        try:
            from finwiz.integration.manager import CrewDataIntegrationManager
            from finwiz.quantitative.data import DataProvider

            # Test that data integration works with quantitative systems
            data_provider = DataProvider()
            integration_manager = CrewDataIntegrationManager()

            # Verify expected methods exist
            assert hasattr(data_provider, "get_historical_data")
            assert hasattr(integration_manager, "store_crew_output")

            # Verify methods are callable
            assert callable(data_provider.get_historical_data)
            assert callable(integration_manager.store_crew_output)

        except Exception as e:
            pytest.fail(f"Quantitative data integration failed: {e}")
