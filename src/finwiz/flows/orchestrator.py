#!/usr/bin/env python
"""
Flow orchestration logic for FinWiz application.

This module contains the FinwizFlow class that coordinates the complete
portfolio analysis workflow by delegating to focused orchestrator modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from crewai.flow import Flow, and_, listen, start

from finwiz.config.batch_prefetch_config import get_batch_prefetch_config
from finwiz.config.resilience_config import get_resilience_config
from finwiz.crew_factory import CrewFactory
from finwiz.flow_state import FinwizState, FlowStateManager
from finwiz.flows.orchestrator_registry import create_orchestrator
from finwiz.infrastructure.monitoring.litellm_callback import enable_token_monitoring
from finwiz.infrastructure.resilience.retry import create_retry_decorator
from finwiz.integration.accessor import CrewDataAccessor
from finwiz.integration.availability import DataAvailabilityTracker
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.orchestrators.error_handling.core_analysis_error_handler import CoreAnalysisErrorHandler
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OrchestratorDependencies:
    """Shared dependencies for all orchestrators."""

    crew_factory: CrewFactory
    integration_manager: CrewDataIntegrationManager
    error_handler: CoreAnalysisErrorHandler
    state_manager: FlowStateManager
    resilience_config: Any
    batch_prefetch_config: Any
    data_accessor: CrewDataAccessor
    availability_tracker: DataAvailabilityTracker
    retry_decorator: Any


class FinwizFlow(Flow[FinwizState]):
    """Main flow coordinating portfolio analysis via orchestrator delegation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the FinwizFlow instance with orchestrators."""
        enable_token_monitoring()
        logger.info("Token monitoring enabled for all LLM calls")
        logger.info("Initializing FinwizFlow with orchestrator delegation")

        self.deps = self._initialize_dependencies()
        logger.info("Orchestrator dependencies initialized")

        # Orchestrators are lazy-loaded via registry on first access
        self._orchestrators: dict[str, Any] = {}

        # Register main cache for metrics (CACHE-03)
        try:
            from finwiz.infrastructure.caching.manager import get_cache_manager
            from finwiz.infrastructure.caching.metrics_logger import get_cache_metrics_logger

            cache_metrics = get_cache_metrics_logger()
            cache_metrics.register_cache("main", get_cache_manager())
        except Exception as e:
            logger.debug(f"Cache metrics registration skipped: {e}")

        super().__init__(*args, **kwargs)

        if not hasattr(self, "state") or self.state is None:
            self.state = self.deps.state_manager.create_initial_state()  # type: ignore[misc]
            logger.info("Flow state initialized with session metadata")
        else:
            logger.info("Flow state already initialized by Flow framework")

    def _initialize_dependencies(self) -> OrchestratorDependencies:
        """
        Initialize shared dependencies for all orchestrators.

        Returns:
            OrchestratorDependencies: Dataclass containing all shared dependencies

        """
        # Initialize data integration system
        integration_manager = CrewDataIntegrationManager()
        data_accessor = CrewDataAccessor(integration_manager)
        logger.info("Data integration system initialized")

        # Initialize error handling system
        error_handler = CoreAnalysisErrorHandler(integration_manager)
        logger.info("Core analysis error handling system initialized")

        # Initialize flow state manager
        state_manager = FlowStateManager()
        logger.info("Flow state manager initialized")

        # Initialize crew factory
        crew_factory = CrewFactory(integration_manager, error_handler)
        logger.info("Crew factory initialized")

        # Initialize data availability tracker
        availability_tracker = DataAvailabilityTracker(
            stale_threshold_hours=168.0,  # 7 days
            logger=logger,
        )
        logger.info("Data availability tracker initialized")

        # Initialize resilience configuration
        resilience_config = get_resilience_config()
        logger.info(f"Resilience configuration loaded: max_retries={resilience_config.max_retries}, retry_base_delay={resilience_config.retry_base_delay}s")

        # Create retry decorator with resilience configuration
        retry_decorator = create_retry_decorator(resilience_config)
        logger.info("Retry decorator initialized with exponential backoff")

        # Initialize batch prefetch configuration
        batch_prefetch_config = get_batch_prefetch_config(log_config=True)
        logger.info("Batch prefetch configuration loaded and validated")

        return OrchestratorDependencies(
            crew_factory=crew_factory,
            integration_manager=integration_manager,
            error_handler=error_handler,
            state_manager=state_manager,
            resilience_config=resilience_config,
            batch_prefetch_config=batch_prefetch_config,
            data_accessor=data_accessor,
            availability_tracker=availability_tracker,
            retry_decorator=retry_decorator,
        )

    def _get_orch(self, name: str) -> Any:
        """Get or create an orchestrator by registry name."""
        if name not in self._orchestrators:
            self._orchestrators[name] = create_orchestrator(name, self.state, self.deps)
        return self._orchestrators[name]

    @property
    def error_handler_orch(self) -> Any:
        return self._get_orch("error_handler")

    @property
    def progress_orch(self) -> Any:
        return self._get_orch("progress")

    @property
    def utility_orch(self) -> Any:
        return self._get_orch("utility")

    @property
    def deep_analysis_orch(self) -> Any:
        return self._get_orch("deep_analysis")

    @property
    def alternatives_orch(self) -> Any:
        return self._get_orch("alternatives")

    @property
    def discovery_orch(self) -> Any:
        return self._get_orch("discovery")

    @property
    def validation_orch(self) -> Any:
        return self._get_orch("validation")

    @property
    def reporting_orch(self) -> Any:
        return self._get_orch("reporting")

    def _update_progress(self) -> None:
        """Delegate progress updates to ProgressTrackingOrchestrator."""
        total = self.state.holdings_processed + self.state.holdings_remaining
        self.progress_orch.update_progress(
            self.state.holdings_processed,
            total,
        )

    # Flow methods - delegate to orchestrators

    @start()
    async def run_sequential_workflow(self) -> dict[str, Any]:
        """
        Execute the complete workflow in sequential order.

        Workflow Phases:
            1. Data validation
            2. Portfolio review (loads holdings from CSV)
            3. Deep analysis (analyzes the loaded holdings)
            4. Discovery (if enabled)
            5. Alternative matching
            6. Reporting

        Returns:
            dict: Completion status

        """
        logger.info("Starting sequential workflow execution")

        # Phase 1: Data Validation
        logger.info("=" * 80)
        logger.info("PHASE 1: Data Integration Validation")
        logger.info("=" * 80)
        await self.validation_orch.validate_data_integration()

        # Phase 2: Portfolio Review (loads holdings from CSV FIRST)
        logger.info("=" * 80)
        logger.info("PHASE 2: Portfolio Review")
        logger.info("=" * 80)
        await self.validation_orch.check_portfolio()

        # Phase 3: Deep Analysis (analyzes the loaded holdings)
        logger.info("=" * 80)
        logger.info("PHASE 3: Deep Analysis")
        logger.info("=" * 80)
        await self.deep_analysis_orch.analyze_and_update_portfolio()

        # Phase 3.5: Stress Testing (if deep analysis ran)
        if self.state.deep_analysis_success:
            logger.info("=" * 80)
            logger.info("PHASE 3.5: Portfolio Stress Testing")
            logger.info("=" * 80)
            try:
                from finwiz.orchestrators.stress_test_orchestrator import StressTestOrchestrator

                stress_orch = StressTestOrchestrator(self.state)
                stress_results = stress_orch.run_stress_tests()
                self.state.stress_test_results = [r.model_dump() for r in stress_results]
                self.state.stress_test_count = len(stress_results)
                logger.info(f"Stress testing completed: {len(stress_results)} scenarios")
            except Exception as e:
                self.state.stress_test_error = str(e)
                logger.warning(f"Stress testing skipped: {e}")

        # Phase 4: Discovery (if enabled)
        # Toggle sources (either path works):
        #   1. state.discovery_enabled — populated from flow.kickoff(inputs={"discovery_enabled": True})
        #   2. INVESTMENT_DISCOVERY_ENABLED=true env var (forwarded by app_initializer.kickoff)
        import os

        discovery_data = {}
        discovery_enabled = self.state.discovery_enabled or (os.getenv("INVESTMENT_DISCOVERY_ENABLED", "false").lower() == "true")
        if discovery_enabled:
            logger.info("=" * 80)
            logger.info("PHASE 4: Investment Discovery")
            logger.info("=" * 80)
            self.discovery_orch.check_crypto()
            self.discovery_orch.check_stock()
            self.discovery_orch.check_etf()
            discovery_result = self.discovery_orch.check_investment_discovery()
            if discovery_result:
                discovery_data = discovery_result

        # Phase 5: Alternative Matching
        logger.info("=" * 80)
        logger.info("PHASE 5: Alternative Matching")
        logger.info("=" * 80)
        self.alternatives_orch.match_alternatives_after_discovery(discovery_data)

        # Phase 6: Reporting
        logger.info("=" * 80)
        logger.info("PHASE 6: Final Reporting")
        logger.info("=" * 80)
        self.validation_orch.pre_validate_reporter_input()
        self.reporting_orch.report()

        # Post-flow: Log cache metrics summary (CACHE-03)
        try:
            from finwiz.infrastructure.caching.metrics_logger import get_cache_metrics_logger

            cache_metrics = get_cache_metrics_logger()
            cache_metrics.log_summary()
        except Exception as e:
            logger.debug(f"Cache metrics logging skipped: {e}")

        # Post-flow: Log LLM cost summary (COST-01, COST-02)
        try:
            from finwiz.infrastructure.monitoring.litellm_callback import get_token_monitor

            monitor = get_token_monitor()
            if monitor:
                monitor.log_cost_summary()
                summary = monitor.get_cost_summary()
                self.state.llm_total_cost = summary["total_cost"]
                self.state.llm_crew_costs = {k: v["cost"] for k, v in summary["per_crew"].items()}
                self.state.llm_call_count = summary["call_count"]
                self.state.llm_cost_summary = summary
        except Exception as e:
            logger.debug(f"LLM cost summary skipped: {e}")

        logger.info("Sequential workflow completed")
        return {"status": "completed"}

    @listen("validate_data_integration")
    async def analyze_and_update_portfolio(self) -> dict[str, Any]:
        """Perform deep analysis and update portfolio review."""
        return await self.deep_analysis_orch.analyze_and_update_portfolio()

    @listen("analyze_and_update_portfolio")
    async def check_portfolio(self) -> dict[str, Any]:
        """Run portfolio keep-or-sell review."""
        return await self.validation_orch.check_portfolio()

    @listen("check_portfolio")
    def check_crypto(self) -> dict[str, Any]:
        """Initiate cryptocurrency discovery."""
        return self.discovery_orch.check_crypto()

    @listen("check_portfolio")
    def check_stock(self) -> dict[str, Any]:
        """Initiate stock discovery."""
        return self.discovery_orch.check_stock()

    @listen("check_portfolio")
    def check_etf(self) -> dict[str, Any]:
        """Initiate ETF discovery."""
        return self.discovery_orch.check_etf()

    @listen(and_("check_crypto", "check_stock", "check_etf"))
    def check_investment_discovery(self) -> dict[str, Any]:
        """Consolidate discovery results."""
        return self.discovery_orch.check_investment_discovery()

    @listen("check_investment_discovery")
    def match_alternatives_after_discovery(self, discovery_data: dict[str, Any]) -> dict[str, Any]:
        """Match alternatives from discovery results."""
        return self.alternatives_orch.match_alternatives_after_discovery(discovery_data)

    @listen("match_alternatives_after_discovery")
    def check_portfolio_rebalancing(self) -> dict[str, Any]:
        """Run portfolio rebalancing analysis."""
        return self.validation_orch.check_portfolio_rebalancing()

    @listen("check_portfolio_rebalancing")
    def pre_validate_reporter_input(self) -> dict[str, Any]:
        """Pre-validate reporter input data."""
        return self.validation_orch.pre_validate_reporter_input()

    @listen("pre_validate_reporter_input")
    def report(self) -> dict[str, Any]:
        """Generate consolidated report."""
        return self.reporting_orch.report()


def plot() -> None:
    """Initialize the FinWiz analysis flow and plot its structure."""
    logger.info("Plotting FinWiz analysis flow structure")
    flow = FinwizFlow()
    flow.plot()
