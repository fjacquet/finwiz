"""
Define the Report Crew for integrated financial analysis.

This module sets up specialized agents (Financial Integration
Analyst, Portfolio Allocator, Risk Manager) and their sequential
tasks. The crew exclusively consumes and analyzes recommendations
from Stock, ETF, and Crypto crews, creates an optimal portfolio
allocation within a specified budget (1000 CHF monthly),
assesses associated risks, and produces a detailed, evidence-based
investment report without conducting additional external research.
"""

import logging
import time
from pathlib import Path
from typing import Any

# Third-party imports
from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, output_json, output_pydantic, task
from crewai_tools import DirectoryReadTool, FileReadTool
from dotenv import load_dotenv

# Local application imports
from finwiz.integration.aplus_discovery_accessor import APlusDiscoveryAccessor
from finwiz.integration.backtesting_extractor import BacktestingDataExtractor
from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.data_availability_tracker import DataAvailabilityTracker
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.rebalancing.core import PortfolioConfiguration
from finwiz.schemas.report import ReporterInput
from finwiz.tools.file_conversion_tools import HtmlToPdfTool  # Added for PDF conversion
from finwiz.tools.rag_tools import get_rag_tools
from finwiz.utils.agent_validators import final_reporter
from finwiz.utils.logging_helpers import CrewLogger
from finwiz.utils.task_decorators import async_task, sync_task
from finwiz.validation.tool_restrictions import ReporterInputValidator, ToolRestrictionValidator

# from finwiz.tools.html_output_tool import HTMLOutputTool

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Get RAG tools for knowledge retrieval and storage
rag_tools = get_rag_tools(collection_suffix="report")

html_to_pdf_tool = HtmlToPdfTool()  # Tool instance for PDF conversion


@CrewBase
class ReportCrew:
    """
    ReportCrew - Expert Financial Integration Team.

    Specialized in analyzing recommendations exclusively from Stock, ETF,
    and Crypto crews without conducting additional external research.
    Creates detailed, evidence-based investment plans with a fixed budget.
    The team focuses on creating optimal portfolio allocations across
    asset classes while maintaining rigorous risk management protocols.
    """

    agents: list[BaseAgent]
    tasks: list[Task]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize report crew with validators and data integration."""
        import yaml

        # Get the directory of this file
        current_dir = Path(__file__).parent

        # Load configuration files
        with open(current_dir / "config" / "agents.yaml") as f:
            self.agents_config = yaml.safe_load(f)

        with open(current_dir / "config" / "tasks.yaml") as f:
            self.tasks_config = yaml.safe_load(f)

        # Make Pydantic models available for CrewAI resolution BEFORE super().__init__()
        # Use both @output_json and @output_pydantic decorators for JSON-first architecture
        self.ReporterInput = output_pydantic(output_json(ReporterInput))
        self.PortfolioConfiguration = output_pydantic(output_json(PortfolioConfiguration))
        self.RiskAssessmentStandardized = output_pydantic(output_json(RiskAssessmentStandardized))

        super().__init__(*args, **kwargs)

        self.tool_validator = ToolRestrictionValidator()
        self.input_validator = ReporterInputValidator()

        # Initialize data integration components
        self.output_dir = Path("output")
        self.integration_manager = CrewDataIntegrationManager(self.output_dir)
        self.data_accessor = CrewDataAccessor(self.integration_manager)
        
        # Initialize A+ discovery accessor
        self.discovery_accessor = APlusDiscoveryAccessor(output_dir=self.output_dir)
        
        # Initialize backtesting data extractor
        self.backtesting_extractor = BacktestingDataExtractor(logger=logger)
        
        # Initialize data availability tracker
        self.availability_tracker = DataAvailabilityTracker(
            stale_threshold_hours=168.0,  # 7 days
            logger=logger
        )

        # Initialize tools with data availability checking
        self._initialize_tools()

        # Initialize structured logger
        self.crew_logger = CrewLogger("ReportCrew")

    def _initialize_tools(self) -> None:
        """Initialize tools with data availability checking and graceful degradation."""
        try:
            # Check data availability before setting up tools
            availability_report = self.data_accessor.check_data_availability()

            # Log data availability status
            logger.info(
                f"Data availability check: {availability_report.overall_status.value}",
                extra={
                    "stock_available": availability_report.stock_available,
                    "etf_available": availability_report.etf_available,
                    "crypto_available": availability_report.crypto_available,
                    "discovery_available": availability_report.discovery_available,
                    "portfolio_available": availability_report.portfolio_available,
                },
            )

            # Set up tools based on data availability
            self.tools = [*rag_tools]  # Always include RAG tools

            # Add directory tools only for available data
            if availability_report.stock_available:
                self.tools.append(DirectoryReadTool(directory="output/stock"))
            if availability_report.etf_available:
                self.tools.append(DirectoryReadTool(directory="output/etf"))
            if availability_report.crypto_available:
                self.tools.append(DirectoryReadTool(directory="output/crypto"))
            if availability_report.portfolio_available:
                self.tools.append(DirectoryReadTool(directory="output/portfolio"))
            if availability_report.discovery_available:
                self.tools.append(DirectoryReadTool(directory="output/discovery"))

            # Always add schema tools for contract-aware reading
            self.tools.extend(
                [
                    DirectoryReadTool(directory="docs/schemas"),
                    DirectoryReadTool(directory="docs/schemas/examples"),
                    FileReadTool(file_path="docs/schemas/ReporterInput.schema.json"),
                    FileReadTool(file_path="docs/schemas/examples/reporter_input.example.json"),
                    FileReadTool(file_path="docs/schemas/APlusDiscoveryResult.schema.json"),
                    FileReadTool(file_path="docs/schemas/OptimizationResult.schema.json"),
                    FileReadTool(file_path="docs/schemas/ValidationResult.schema.json"),
                ]
            )

            # Log warnings for missing data
            if availability_report.missing_data:
                logger.warning(
                    f"Missing data for crews: {', '.join(availability_report.missing_data)}. "
                    "Report generation will proceed with available data."
                )

            # Log stale data warnings
            if availability_report.stale_data:
                stale_warnings = self.data_accessor.get_stale_data_warnings()
                for warning in stale_warnings:
                    logger.warning(warning)

        except Exception as e:
            logger.error(f"Failed to initialize tools with data integration: {str(e)}", exc_info=True)
            # Fallback to basic tools
            self.tools = [
                *rag_tools,
                DirectoryReadTool(directory="output/crypto"),
                DirectoryReadTool(directory="output/etf"),
                DirectoryReadTool(directory="output/stock"),
                DirectoryReadTool(directory="output/portfolio"),
                DirectoryReadTool(directory="output/discovery"),
                DirectoryReadTool(directory="docs/schemas"),
                DirectoryReadTool(directory="docs/schemas/examples"),
                FileReadTool(file_path="docs/schemas/ReporterInput.schema.json"),
                FileReadTool(file_path="docs/schemas/examples/reporter_input.example.json"),
                FileReadTool(file_path="docs/schemas/APlusDiscoveryResult.schema.json"),
                FileReadTool(file_path="docs/schemas/OptimizationResult.schema.json"),
                FileReadTool(file_path="docs/schemas/ValidationResult.schema.json"),
            ]

    def get_integrated_data_context(self, max_age_hours: int = 24) -> dict[str, Any]:
        """
        Get integrated data context for report generation.

        Args:
            max_age_hours: Maximum acceptable age in hours for data

        Returns:
            Dictionary containing consolidated data and metadata

        """
        try:
            # Clear previous tracking
            self.availability_tracker.clear_tracked_sources()
            
            # Get consolidated reporter input with all integrated data
            integrated_data = self.data_accessor.get_consolidated_reporter_input(max_age_hours)

            # Track crew data availability
            availability_report = self.data_accessor.check_data_availability(max_age_hours)
            
            # Track stock crew data
            if availability_report.stock_available:
                self.availability_tracker.track_data_source(
                    source="stock_crew",
                    status="available",
                    age_hours=availability_report.stock_age_hours,
                    record_count=len(integrated_data.get("stock_analysis_data", []))
                )
            else:
                self.availability_tracker.track_data_source(
                    source="stock_crew",
                    status="unavailable",
                    error_message="Stock crew data not found"
                )
            
            # Track ETF crew data
            if availability_report.etf_available:
                self.availability_tracker.track_data_source(
                    source="etf_crew",
                    status="available",
                    age_hours=availability_report.etf_age_hours,
                    record_count=len(integrated_data.get("etf_analysis_data", []))
                )
            else:
                self.availability_tracker.track_data_source(
                    source="etf_crew",
                    status="unavailable",
                    error_message="ETF crew data not found"
                )
            
            # Track crypto crew data
            if availability_report.crypto_available:
                self.availability_tracker.track_data_source(
                    source="crypto_crew",
                    status="available",
                    age_hours=availability_report.crypto_age_hours,
                    record_count=len(integrated_data.get("crypto_analysis_data", []))
                )
            else:
                self.availability_tracker.track_data_source(
                    source="crypto_crew",
                    status="unavailable",
                    error_message="Crypto crew data not found"
                )
            
            # Track portfolio data
            if availability_report.portfolio_available:
                self.availability_tracker.track_data_source(
                    source="portfolio_review",
                    status="available",
                    age_hours=availability_report.portfolio_age_hours,
                    record_count=len(integrated_data.get("portfolio_review", {}).get("holdings", []))
                )
            else:
                self.availability_tracker.track_data_source(
                    source="portfolio_review",
                    status="unavailable",
                    error_message="Portfolio review data not found"
                )

            # Add data availability information
            integrated_data["data_availability_report"] = availability_report

            # Add stale data warnings
            integrated_data["stale_data_warnings"] = self.data_accessor.get_stale_data_warnings(max_age_hours)
            
            # Add A+ discovery data with proper status handling
            discovery_status = self._get_discovery_status()
            integrated_data["discovery_status"] = discovery_status
            
            if discovery_status["has_results"]:
                # Load discovery results
                discovery_results = self.discovery_accessor.load_discovery_results()
                if discovery_results:
                    integrated_data["aplus_discovery_results"] = discovery_results
                    integrated_data["aplus_opportunities_summary"] = self.discovery_accessor.get_opportunities_summary()
                    
                    # Track discovery data as available
                    self.availability_tracker.track_data_source(
                        source="aplus_discovery",
                        status="available",
                        record_count=len(discovery_results.get('opportunities', []))
                    )
                    
                    logger.info(f"Loaded A+ discovery results: {len(discovery_results.get('opportunities', []))} opportunities found")
                else:
                    integrated_data["aplus_discovery_results"] = None
                    integrated_data["aplus_opportunities_summary"] = "No A+ opportunities found in current analysis"
                    
                    # Track discovery as available but with no opportunities
                    self.availability_tracker.track_data_source(
                        source="aplus_discovery",
                        status="available",
                        record_count=0
                    )
                    
                    logger.info("Discovery results exist but no opportunities found")
            else:
                integrated_data["aplus_discovery_results"] = None
                integrated_data["aplus_opportunities_summary"] = discovery_status["message"]
                
                # Track discovery as unavailable
                self.availability_tracker.track_data_source(
                    source="aplus_discovery",
                    status="unavailable",
                    error_message=discovery_status["message"]
                )
                
                logger.info(f"A+ discovery not available: {discovery_status['message']}")
            
            # Add backtesting data with proper status handling
            backtesting_data = self._extract_backtesting_data()
            integrated_data["backtesting_status"] = {
                "has_data": backtesting_data["has_backtesting_data"],
                "message": backtesting_data["message"],
                "status": backtesting_data["status"]
            }
            
            if backtesting_data["has_backtesting_data"]:
                integrated_data["backtesting_data"] = backtesting_data["backtesting_by_candidate"]
                integrated_data["backtesting_summary"] = backtesting_data.get("summary")
                
                # Track backtesting data as available
                self.availability_tracker.track_data_source(
                    source="backtesting",
                    status="available",
                    record_count=backtesting_data.get("total_candidates", 0)
                )
                
                logger.info(f"Loaded backtesting data for {backtesting_data['total_candidates']} candidates")
            else:
                integrated_data["backtesting_data"] = None
                integrated_data["backtesting_summary"] = None
                
                # Track backtesting as unavailable
                self.availability_tracker.track_data_source(
                    source="backtesting",
                    status="unavailable",
                    error_message=backtesting_data["message"]
                )
                
                logger.info(f"Backtesting data not available: {backtesting_data['message']}")
            
            # Generate data availability summary
            availability_summary = self.availability_tracker.get_availability_summary()
            integrated_data["data_availability_summary"] = availability_summary.model_dump()
            integrated_data["data_availability_summary_formatted"] = self.availability_tracker.format_summary_for_report(availability_summary)
            
            logger.info(
                "Integrated data context prepared for report generation",
                extra={
                    "total_sources": availability_summary.total_sources,
                    "available_sources": availability_summary.available_sources,
                    "unavailable_sources": availability_summary.unavailable_sources,
                    "stale_sources": availability_summary.stale_sources
                }
            )
            
            return integrated_data

        except Exception as e:
            logger.error(f"Failed to get integrated data context: {str(e)}", exc_info=True)
            
            # Track error in availability tracker
            self.availability_tracker.track_data_source(
                source="data_integration",
                status="unavailable",
                error_message=f"Data integration failed: {str(e)}"
            )
            
            # Generate error summary
            error_summary = self.availability_tracker.get_availability_summary()
            
            return {
                "error": f"Data integration failed: {str(e)}",
                "fallback_mode": True,
                "data_availability_report": None,
                "stale_data_warnings": [f"Data integration error: {str(e)}"],
                "discovery_status": {
                    "has_results": False,
                    "message": f"Discovery data unavailable due to error: {str(e)}"
                },
                "data_availability_summary": error_summary.model_dump(),
                "data_availability_summary_formatted": self.availability_tracker.format_summary_for_report(error_summary)
            }
    
    def _get_discovery_status(self) -> dict[str, Any]:
        """
        Get A+ discovery status with clear messaging.
        
        Returns:
            Dictionary with discovery status information
        """
        has_results = self.discovery_accessor.has_discovery_results()
        
        if has_results:
            return {
                "has_results": True,
                "message": "A+ discovery results available",
                "status": "available"
            }
        else:
            return {
                "has_results": False,
                "message": "A+ discovery not run - use --discovery flag to enable discovery analysis",
                "status": "not_run"
            }
    
    def _safe_get_metric(self, vr_data: dict[str, Any], key: str) -> float | None:
        """
        Safely extract a metric from validation result dict.
        
        Args:
            vr_data: Validation result dictionary
            key: Key to extract
            
        Returns:
            Float value or None if not available or invalid
        """
        value = vr_data.get(key)
        if value is None:
            return None
        
        # Check for string placeholders
        if isinstance(value, str):
            return None
        
        try:
            float_value = float(value)
            # Check for reasonable range
            if not (-1e10 < float_value < 1e10):
                return None
            return float_value
        except (ValueError, TypeError):
            return None
    
    def _calculate_calmar_from_dict(self, vr_data: dict[str, Any]) -> float | None:
        """Calculate Calmar ratio from validation result dict."""
        # Try to get annualized return from validation details
        annualized_return = None
        validation_details = vr_data.get("validation_details", [])
        if validation_details:
            returns = [d.get("annualized_return") for d in validation_details if d.get("annualized_return") is not None]
            if returns:
                annualized_return = sum(returns) / len(returns)
        
        # If not in details, try direct field
        if annualized_return is None:
            annualized_return = self._safe_get_metric(vr_data, "annualized_return")
        
        max_dd = self._safe_get_metric(vr_data, "average_max_drawdown")
        
        if annualized_return is None or max_dd is None:
            return None
        
        abs_max_dd = abs(max_dd)
        if abs_max_dd == 0:
            return None
        
        return annualized_return / abs_max_dd
    
    def _extract_total_trades_from_dict(self, vr_data: dict[str, Any]) -> int | None:
        """Extract total trades from validation result dict."""
        validation_details = vr_data.get("validation_details", [])
        if not validation_details:
            return None
        
        trades = [d.get("total_trades", 0) for d in validation_details if "total_trades" in d]
        return sum(trades) if trades else None
    
    def _extract_backtesting_data(self) -> dict[str, Any]:
        """
        Extract backtesting data from discovery results using the backtesting extractor.
        
        Returns:
            Dictionary with backtesting data and status
        """
        try:
            # Check if discovery results exist
            if not self.discovery_accessor.has_discovery_results():
                logger.info("No discovery results available for backtesting extraction")
                return {
                    "has_backtesting_data": False,
                    "message": "Backtesting data not available - discovery not run",
                    "status": "not_available"
                }
            
            # Load discovery results
            discovery_results = self.discovery_accessor.load_discovery_results()
            if not discovery_results:
                logger.info("Discovery results exist but could not be loaded")
                return {
                    "has_backtesting_data": False,
                    "message": "Backtesting data not available - discovery results could not be loaded",
                    "status": "not_available"
                }
            
            # Extract validation results from discovery data
            validation_results = discovery_results.get("validation_results", [])
            if not validation_results:
                logger.info("No validation results found in discovery data")
                return {
                    "has_backtesting_data": False,
                    "message": "Backtesting data not available - no validation results in discovery",
                    "status": "not_available"
                }
            
            # Extract backtesting metrics for each candidate
            backtesting_by_candidate = {}
            all_metrics = []
            
            for vr_data in validation_results:
                try:
                    # Work directly with dict data - don't try to convert to ValidationResult
                    # as it may not have all required fields
                    symbol = vr_data.get("symbol", "UNKNOWN")
                    
                    # Extract annualized return from validation details if not in top level
                    annualized_return = self._safe_get_metric(vr_data, "annualized_return")
                    if annualized_return is None:
                        validation_details = vr_data.get("validation_details", [])
                        if validation_details:
                            returns = [d.get("annualized_return") for d in validation_details if d.get("annualized_return") is not None]
                            if returns:
                                annualized_return = sum(returns) / len(returns)
                    
                    # Extract win rate from validation details if not in top level
                    win_rate = self._safe_get_metric(vr_data, "win_rate")
                    if win_rate is None:
                        validation_details = vr_data.get("validation_details", [])
                        if validation_details:
                            rates = [d.get("win_rate") for d in validation_details if d.get("win_rate") is not None]
                            if rates:
                                win_rate = sum(rates) / len(rates)
                    
                    # Extract metrics directly from the dict
                    metrics_dict = {
                        "annualized_return": annualized_return,
                        "sharpe_ratio": self._safe_get_metric(vr_data, "average_sharpe_ratio"),
                        "sortino_ratio": self._safe_get_metric(vr_data, "average_sortino_ratio"),
                        "calmar_ratio": self._calculate_calmar_from_dict(vr_data),
                        "max_drawdown": self._safe_get_metric(vr_data, "average_max_drawdown"),
                        "win_rate": win_rate,
                        "backtest_period_years": vr_data.get("backtest_period_years"),
                        "total_trades": self._extract_total_trades_from_dict(vr_data)
                    }
                    
                    # Create BacktestingMetrics from the extracted data
                    from finwiz.integration.backtesting_extractor import BacktestingMetrics
                    metrics = BacktestingMetrics(**metrics_dict)
                    
                    if metrics:
                        backtesting_by_candidate[symbol] = {
                            "metrics": metrics.model_dump(),
                            "formatted_display": self.backtesting_extractor.format_for_display(metrics),
                            "available_metrics": self.backtesting_extractor.get_available_metrics(metrics)
                        }
                        all_metrics.append(metrics)
                        logger.info(f"Extracted backtesting metrics for {symbol}")
                except Exception as e:
                    logger.error(f"Failed to extract backtesting metrics for validation result: {e}")
                    continue
            
            # Generate summary if we have metrics
            summary = None
            if all_metrics:
                # Convert BacktestingMetrics to ValidationResult for summary
                # For now, we'll create a simple summary from the metrics we have
                summary_data = {
                    "total_candidates_tested": len(all_metrics),
                    "candidates_with_data": len([m for m in all_metrics if m.annualized_return is not None]),
                    "average_annualized_return": sum(m.annualized_return for m in all_metrics if m.annualized_return is not None) / len([m for m in all_metrics if m.annualized_return is not None]) if any(m.annualized_return is not None for m in all_metrics) else None,
                    "average_sharpe_ratio": sum(m.sharpe_ratio for m in all_metrics if m.sharpe_ratio is not None) / len([m for m in all_metrics if m.sharpe_ratio is not None]) if any(m.sharpe_ratio is not None for m in all_metrics) else None,
                    "average_max_drawdown": sum(m.max_drawdown for m in all_metrics if m.max_drawdown is not None) / len([m for m in all_metrics if m.max_drawdown is not None]) if any(m.max_drawdown is not None for m in all_metrics) else None,
                }
            
            if backtesting_by_candidate:
                logger.info(f"Successfully extracted backtesting data for {len(backtesting_by_candidate)} candidates")
                return {
                    "has_backtesting_data": True,
                    "message": f"Backtesting data available for {len(backtesting_by_candidate)} candidates",
                    "status": "available",
                    "backtesting_by_candidate": backtesting_by_candidate,
                    "summary": summary_data if summary else None,
                    "total_candidates": len(backtesting_by_candidate)
                }
            else:
                logger.warning("No backtesting metrics could be extracted from validation results")
                return {
                    "has_backtesting_data": False,
                    "message": "Backtesting data not available - metrics could not be extracted",
                    "status": "not_available"
                }
                
        except Exception as e:
            logger.error(f"Failed to extract backtesting data: {e}", exc_info=True)
            return {
                "has_backtesting_data": False,
                "message": f"Backtesting data extraction failed: {str(e)}",
                "status": "error"
            }

    @agent
    def financial_integration_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["financial_integration_analyst"],
            verbose=True,
            reasoning=False,
            tools=self.tools,
        )

    @agent
    def portfolio_allocator(self) -> Agent:
        """Agent that proposes optimal cross-asset portfolio allocations."""
        return Agent(
            config=self.agents_config["portfolio_allocator"],
            verbose=True,
            tools=self.tools,
            reasoning=False,
        )

    @agent
    def risk_manager(self) -> Agent:
        """Agent that identifies and mitigates portfolio and market risks."""
        return Agent(
            config=self.agents_config["risk_manager"],
            verbose=True,
            tools=self.tools,
            reasoning=False,
        )

    @final_reporter
    @agent
    def investment_reporter(self) -> Agent:
        """Define the final reporter with no tools; format the consolidated HTML report."""
        return Agent(
            config=self.agents_config["investment_reporter"],
            verbose=True,
            # Per FinWiz policy: final reporter must have NO tools; it only consumes upstream
            # context and formats the final HTML report.
            tools=[],
        )

    # @final_reporter
    # @agent
    # def translator(self) -> Agent:
    #     """Create translator agent that converts English reports to French while preserving layout."""
    #     return Agent(
    #         config=self.agents_config["translator"],
    #         tools=[],  # No tools - only consumes upstream HTML context
    #         verbose=True,
    #     )

    @async_task
    @task
    def comprehensive_financial_integration_task(self) -> Task:
        """Integrate Stock/ETF/Crypto analyses into a unified narrative."""
        return Task(
            config=self.tasks_config["comprehensive_financial_integration_task"],
            verbose=True,
        )

    @async_task
    @task
    def optimal_portfolio_allocation_task(self) -> Task:
        """Derive optimal asset allocation based on goals and constraints."""
        return Task(
            config=self.tasks_config["optimal_portfolio_allocation_task"],
            verbose=True,
        )

    @async_task
    @task
    def risk_assessment_mitigation_task(self) -> Task:
        """Assess key risks and propose mitigation strategies."""
        return Task(
            config=self.tasks_config["risk_assessment_mitigation_task"],
            verbose=True,
        )

    @sync_task
    @task
    def comprehensive_investment_report_task(self) -> Task:
        """Compile the comprehensive HTML investment report."""
        return Task(
            config=self.tasks_config["comprehensive_investment_report_task"],
            verbose=True,
        )

    # @sync_task
    # @task
    # def translation_task(self) -> Task:
    #     """Task to translate the English report to French while preserving layout."""
    #     return Task(
    #         config=self.tasks_config["translation_task"],
    #     )

    @crew
    def crew(self) -> Crew:
        """
        Create a specialized financial integration crew.

        This crew analyzes recommendations exclusively from Stock, ETF, and Crypto
        Crews without conducting additional external research, creates an optimal
        portfolio allocation within a 1000 CHF monthly budget, assesses investment
        risks, and produces a comprehensive investment report with actionable
        recommendations backed by verifiable evidence. Uses a sequential workflow.
        """
        # Get all agents for validation and crew creation
        agents = [
            self.financial_integration_analyst(),
            self.portfolio_allocator(),
            self.risk_manager(),
            self.investment_reporter(),
            # self.translator(),
        ]

        tasks = [
            self.comprehensive_financial_integration_task(),
            self.optimal_portfolio_allocation_task(),
            self.risk_assessment_mitigation_task(),
            self.comprehensive_investment_report_task(),
            # self.translation_task(),
        ]

        # Validate tool restrictions before creating crew
        try:
            self.tool_validator.validate_crew_compliance(agents)
            logger.info("Tool restriction validation passed for ReportCrew")
        except Exception as e:
            logger.error(f"Tool restriction validation failed: {e}")
            raise

        # Create crew with integrated data context
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            allow_delegation=False,
            allow_termination=True,
            respect_context_window=True,
            max_retries=10,
            max_rpm=20,
        )

        return crew

    def kickoff(self, inputs: dict[str, Any] | None = None, max_age_hours: int = 24) -> Any:
        """
        Execute the crew with integrated data context.

        Args:
            inputs: Additional inputs for crew execution
            max_age_hours: Maximum acceptable age in hours for data

        Returns:
            Crew execution result

        """
        # Log execution start
        self.crew_logger.log_start(inputs or {})
        start_time = time.time()

        try:
            # Prepare integrated context
            integrated_context = self.prepare_crew_context(max_age_hours)

            # Merge with provided inputs
            if inputs:
                integrated_context.update(inputs)

            # Log additional context about data status
            logger.info(
                "ReportCrew executing with integrated data",
                extra={
                    "max_age_hours": max_age_hours,
                    "has_integrated_context": "error" not in integrated_context,
                    "fallback_mode": integrated_context.get("fallback_mode", False),
                },
            )

            # Execute crew with integrated context
            crew_instance = self.crew()
            result = crew_instance.kickoff(inputs=integrated_context)

            # Log completion
            duration = time.time() - start_time
            self.crew_logger.log_complete(duration)
            return result

        except Exception as e:
            self.crew_logger.log_error(e)
            raise

    def validate_reporter_input(self, context: dict[str, Any]) -> None:
        """
        Validate that reporter receives proper upstream context.

        Args:
            context: The context data being passed to the reporter

        """
        self.input_validator.validate_reporter_context(context)

    def prepare_crew_context(self, max_age_hours: int = 24) -> dict[str, Any]:
        """
        Prepare integrated context for crew execution.

        Args:
            max_age_hours: Maximum acceptable age in hours for data

        Returns:
            Dictionary containing all integrated data and metadata for crew execution

        """
        try:
            # Get integrated data context
            integrated_context = self.get_integrated_data_context(max_age_hours)

            # Validate the integrated context
            self.validate_reporter_input(integrated_context)

            # CRITICAL: Extract and validate tickers to prevent hallucination
            validated_tickers = self._extract_validated_tickers(integrated_context)

            if not validated_tickers or len(validated_tickers) < 3:
                error_msg = (
                    f"Cannot generate report: Insufficient validated tickers. "
                    f"Found {len(validated_tickers)} ticker(s): {validated_tickers}. "
                    f"Need at least 3 validated tickers for a diversified portfolio report. "
                    f"This prevents hallucination of fake ticker symbols."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Add validated tickers to context for agents to use
            integrated_context["validated_tickers_list"] = validated_tickers
            integrated_context["ticker_count"] = len(validated_tickers)

            logger.info(
                f"Validated {len(validated_tickers)} tickers for report generation", extra={"validated_tickers": validated_tickers}
            )

            # Add execution metadata
            integrated_context["execution_metadata"] = {
                "max_age_hours": max_age_hours,
                "integration_manager_initialized": self.integration_manager is not None,
                "data_accessor_initialized": self.data_accessor is not None,
                "tools_count": len(self.tools),
                "validated_ticker_count": len(validated_tickers),
            }

            logger.info("Crew context prepared with integrated data and validated tickers")
            return integrated_context

        except Exception as e:
            logger.error(f"Failed to prepare crew context: {str(e)}", exc_info=True)
            # Return minimal context for graceful degradation
            return {
                "error": f"Context preparation failed: {str(e)}",
                "fallback_mode": True,
                "execution_metadata": {
                    "max_age_hours": max_age_hours,
                    "integration_manager_initialized": False,
                    "data_accessor_initialized": False,
                    "tools_count": len(self.tools) if hasattr(self, "tools") else 0,
                },
            }

    def _extract_validated_tickers(self, context: dict[str, Any]) -> list[str]:
        """
        Extract validated tickers from upstream crew data.

        This method prevents hallucination by extracting only real tickers
        that were validated by upstream crews (stock, ETF, crypto).

        Args:
            context: Integrated data context from all crews

        Returns:
            List of validated ticker symbols

        """
        tickers = set()

        # Extract from stock data
        stock_data = context.get("stock_analysis_data", {})
        if isinstance(stock_data, dict):
            for task in stock_data.get("tasks_output", []):
                if isinstance(task, dict):
                    pydantic = task.get("pydantic", {})
                    if isinstance(pydantic, dict) and "ticker" in pydantic:
                        ticker = pydantic["ticker"]
                        if ticker and isinstance(ticker, str):
                            tickers.add(ticker.upper())

        # Extract from ETF data
        etf_data = context.get("etf_analysis_data", {})
        if isinstance(etf_data, dict):
            for task in etf_data.get("tasks_output", []):
                if isinstance(task, dict):
                    pydantic = task.get("pydantic", {})
                    if isinstance(pydantic, dict) and "ticker" in pydantic:
                        ticker = pydantic["ticker"]
                        if ticker and isinstance(ticker, str):
                            tickers.add(ticker.upper())

        # Extract from crypto data
        crypto_data = context.get("crypto_analysis_data", {})
        if isinstance(crypto_data, dict):
            for task in crypto_data.get("tasks_output", []):
                if isinstance(task, dict):
                    pydantic = task.get("pydantic", {})
                    if isinstance(pydantic, dict):
                        # Crypto might use 'symbol' instead of 'ticker'
                        symbol = pydantic.get("symbol") or pydantic.get("ticker")
                        if symbol and isinstance(symbol, str):
                            tickers.add(symbol.upper())

        # Also check for consolidated ticker validation results
        ticker_validation = context.get("ticker_validation", {})
        if isinstance(ticker_validation, dict):
            validated = ticker_validation.get("validated_tickers", [])
            if isinstance(validated, list):
                for ticker in validated:
                    if ticker and isinstance(ticker, str):
                        tickers.add(ticker.upper())

        validated_list = sorted(list(tickers))

        logger.info(f"Extracted {len(validated_list)} validated tickers from upstream data", extra={"tickers": validated_list})

        return validated_list

    def _validate_task_output(self, task_output: str, validated_tickers: list[str]) -> None:
        """
        Validate that task output only contains validated tickers.

        This prevents hallucination by checking for common fake tickers
        and ensuring all mentioned tickers are in the validated list.

        Args:
            task_output: The output text from a task
            validated_tickers: List of validated ticker symbols

        Raises:
            ValueError: If hallucinated tickers are detected

        """
        # Common hallucinated ticker patterns
        hallucinated_patterns = ["ABC", "XYZ", "LMN", "TEST", "EXAMPLE", "SAMPLE", "TICKER", "STOCK", "ETF", "CRYPTO"]

        # Convert validated tickers to uppercase for comparison
        validated_upper = [t.upper() for t in validated_tickers]

        # Check for hallucinated patterns
        for pattern in hallucinated_patterns:
            if pattern in validated_upper:
                # Skip if it's actually a valid ticker
                continue

            # Check if pattern appears as a standalone word (not part of another word)
            import re

            if re.search(rf"\b{pattern}\b", task_output):
                error_msg = (
                    f"Task output contains hallucinated ticker '{pattern}' "
                    f"which is not in validated_tickers: {validated_tickers}. "
                    f"This indicates the agent is inventing fake ticker symbols."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

        # Check for fake company names that often accompany hallucinated tickers
        fake_company_patterns = [
            "Alpha Beta Corp",
            "Lumina Networks",
            "Xylon Holdings",
            "Example Corp",
            "Sample Inc",
            "Test Company",
        ]

        for fake_company in fake_company_patterns:
            if fake_company in task_output:
                error_msg = (
                    f"Task output contains fake company name '{fake_company}'. "
                    f"This indicates the agent is hallucinating company information."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

        logger.debug("Task output validation passed - no hallucinated tickers detected")
