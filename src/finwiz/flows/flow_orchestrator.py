#!/usr/bin/env python
"""
Flow orchestration logic for FinWiz application.

This module contains the FinwizFlow class that coordinates the complete
portfolio analysis workflow by delegating to focused orchestrator modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from finwiz.orchestrators.alternatives_matching_orchestrator import AlternativesMatchingOrchestrator
    from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator
    from finwiz.orchestrators.discovery_orchestrator import DiscoveryOrchestrator
    from finwiz.orchestrators.error_handling_orchestrator import ErrorHandlingOrchestrator
    from finwiz.orchestrators.progress_tracking_orchestrator import ProgressTrackingOrchestrator
    from finwiz.orchestrators.reporting_orchestrator import ReportingOrchestrator
    from finwiz.orchestrators.utility_orchestrator import UtilityOrchestrator
    from finwiz.orchestrators.validation_orchestrator import ValidationOrchestrator

from crewai.flow import Flow, and_, listen, start
from crewai.flow.persistence import persist

from finwiz.config.batch_prefetch_config import get_batch_prefetch_config
from finwiz.config.resilience_config import get_resilience_config
from finwiz.crew_factory import CrewFactory
from finwiz.flow_state import FinwizState, FlowStateManager
from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.data_availability_tracker import DataAvailabilityTracker
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.tools.logger import get_logger
from finwiz.utils.core_analysis_error_handler import CoreAnalysisErrorHandler
from finwiz.utils.retry_handler import create_retry_decorator

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
    cache_service: Any = None
    cache_enabled: bool = False


@persist()
class FinwizFlow(Flow[FinwizState]):
    """
    Main orchestrator for the financial analysis workflow.

    This flow coordinates the complete portfolio analysis workflow by delegating
    to focused orchestrator modules for improved maintainability and testability.

    Architecture:
        The Flow delegates to focused orchestrator modules, each with a single
        responsibility:

        - ErrorHandlingOrchestrator: Crew execution error handling
        - ProgressTrackingOrchestrator: Progress calculation and metrics
        - UtilityOrchestrator: Data parsing and validation utilities
        - DeepAnalysisOrchestrator: Deep analysis execution and result creation
        - AlternativesMatchingOrchestrator: A+ alternative matching
        - DiscoveryOrchestrator: Discovery crew execution and consolidation
        - ValidationOrchestrator: Input validation and data availability
        - ReportingOrchestrator: Report consolidation and HTML generation

    Workflow Phases:
        1. Data Validation: validate_data_integration()
        2. Portfolio Review: check_portfolio()
        3. Deep Analysis: analyze_and_update_portfolio()
        4. Discovery: check_crypto(), check_stock(), check_etf()
        5. Alternative Matching: match_alternatives_after_discovery()
        6. Rebalancing: check_portfolio_rebalancing()
        7. Pre-validation: pre_validate_reporter_input()
        8. Final Report: report()

    State Management:
        Uses structured Pydantic state (FinwizState) for type safety and
        validation.

    Example:
        >>> flow = FinwizFlow()
        >>> result = flow.kickoff()
        >>> final_state = flow.state
        >>> print(f"Analysis complete: {final_state.final_report_path}")

    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the FinwizFlow instance with orchestrators."""
        logger.info("Initializing FinwizFlow with orchestrator delegation")

        # Initialize dependencies FIRST (before super().__init__())
        # This is required because Flow framework may access properties during initialization
        self.deps = self._initialize_dependencies()
        logger.info("Orchestrator dependencies initialized")

        # Initialize orchestrators (lazy loading via properties) BEFORE super().__init__()
        self._error_handler_orch: ErrorHandlingOrchestrator | None = None
        self._progress_orch: ProgressTrackingOrchestrator | None = None
        self._utility_orch: UtilityOrchestrator | None = None
        self._deep_analysis_orch: DeepAnalysisOrchestrator | None = None
        self._alternatives_orch: AlternativesMatchingOrchestrator | None = None
        self._discovery_orch: DiscoveryOrchestrator | None = None
        self._validation_orch: ValidationOrchestrator | None = None
        self._reporting_orch: ReportingOrchestrator | None = None

        super().__init__(*args, **kwargs)

        # Initialize structured state
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

        # Initialize Supabase cache service
        cache_service = None
        cache_enabled = False
        try:
            from finwiz.supabase.client import SupabaseClient
            from finwiz.supabase.repositories.analysis_repository import AnalysisRepository
            from finwiz.supabase.services.cache_service import CacheService

            supabase_client = SupabaseClient(
                failure_threshold=3,
                recovery_timeout=300,  # 5 minutes
            )
            analysis_repository = AnalysisRepository(supabase_client)
            cache_service = CacheService(analysis_repository, supabase_client)
            logger.info("Supabase cache service created (connectivity test pending)")
        except Exception as e:
            logger.warning(f"Supabase cache service initialization failed: {e}")
            logger.info("Continuing without Supabase caching (graceful degradation)")

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
            cache_service=cache_service,
            cache_enabled=cache_enabled,
        )

    # Lazy loading properties for orchestrators

    @property
    def error_handler_orch(self):
        """Lazy load error handling orchestrator."""
        if self._error_handler_orch is None:
            from finwiz.orchestrators.error_handling_orchestrator import ErrorHandlingOrchestrator

            self._error_handler_orch = ErrorHandlingOrchestrator(
                state=self.state,
                crew_factory=self.deps.crew_factory,
                integration_manager=self.deps.integration_manager,
                error_handler=self.deps.error_handler,
            )
        return self._error_handler_orch

    @property
    def progress_orch(self):
        """Lazy load progress tracking orchestrator."""
        if self._progress_orch is None:
            from finwiz.orchestrators.progress_tracking_orchestrator import ProgressTrackingOrchestrator

            self._progress_orch = ProgressTrackingOrchestrator(
                state=self.state,
            )
        return self._progress_orch

    @property
    def utility_orch(self):
        """Lazy load utility orchestrator."""
        if self._utility_orch is None:
            from finwiz.orchestrators.utility_orchestrator import UtilityOrchestrator

            self._utility_orch = UtilityOrchestrator(
                state=self.state,
            )
        return self._utility_orch

    @property
    def deep_analysis_orch(self):
        """Lazy load deep analysis orchestrator."""
        if self._deep_analysis_orch is None:
            from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator

            self._deep_analysis_orch = DeepAnalysisOrchestrator(
                state=self.state,
                crew_factory=self.deps.crew_factory,
                integration_manager=self.deps.integration_manager,
                error_handler=self.deps.error_handler,
                batch_prefetch_config=self.deps.batch_prefetch_config,
                cache_service=self.deps.cache_service,
                cache_enabled=self.deps.cache_enabled,
            )
        return self._deep_analysis_orch

    @property
    def alternatives_orch(self):
        """Lazy load alternatives matching orchestrator."""
        if self._alternatives_orch is None:
            from finwiz.orchestrators.alternatives_matching_orchestrator import AlternativesMatchingOrchestrator

            self._alternatives_orch = AlternativesMatchingOrchestrator(
                state=self.state,
                crew_factory=self.deps.crew_factory,
                integration_manager=self.deps.integration_manager,
                error_handler=self.deps.error_handler,
            )
        return self._alternatives_orch

    @property
    def discovery_orch(self):
        """Lazy load discovery orchestrator."""
        if self._discovery_orch is None:
            from finwiz.orchestrators.discovery_orchestrator import DiscoveryOrchestrator

            self._discovery_orch = DiscoveryOrchestrator(
                state=self.state,
                availability_tracker=self.deps.availability_tracker,
            )
        return self._discovery_orch

    @property
    def validation_orch(self):
        """Lazy load validation orchestrator."""
        if self._validation_orch is None:
            from finwiz.orchestrators.validation_orchestrator import ValidationOrchestrator

            self._validation_orch = ValidationOrchestrator(
                state=self.state,
                data_accessor=self.deps.data_accessor,
                integration_manager=self.deps.integration_manager,
                cache_service=self.deps.cache_service,
            )
        return self._validation_orch

    @property
    def reporting_orch(self):
        """Lazy load reporting orchestrator."""
        if self._reporting_orch is None:
            from finwiz.orchestrators.reporting_orchestrator import ReportingOrchestrator

            self._reporting_orch = ReportingOrchestrator(
                state=self.state,
                integration_manager=self.deps.integration_manager,
            )
        return self._reporting_orch

    # Convenience properties for direct access to dependencies

    @property
    def cache_enabled(self) -> bool:
        """Access cache_enabled from deps."""
        return self.deps.cache_enabled

    @property
    def cache_service(self):
        """Access cache_service from deps."""
        return self.deps.cache_service

    @property
    def integration_manager(self):
        """Access integration_manager from deps."""
        return self.deps.integration_manager

    @property
    def data_accessor(self):
        """Access data_accessor from deps."""
        return self.deps.data_accessor

    @property
    def error_handler(self):
        """Access error_handler from deps."""
        return self.deps.error_handler

    @property
    def state_manager(self):
        """Access state_manager from deps."""
        return self.deps.state_manager

    @property
    def crew_factory(self):
        """Access crew_factory from deps."""
        return self.deps.crew_factory

    @property
    def availability_tracker(self):
        """Access availability_tracker from deps."""
        return self.deps.availability_tracker

    @property
    def resilience_config(self):
        """Access resilience_config from deps."""
        return self.deps.resilience_config

    @property
    def batch_prefetch_config(self):
        """Access batch_prefetch_config from deps."""
        return self.deps.batch_prefetch_config

    @property
    def retry_decorator(self):
        """Access retry_decorator from deps."""
        return self.deps.retry_decorator

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

        # Phase 4: Discovery (if enabled)
        import os

        discovery_data = {}
        if os.getenv("INVESTMENT_DISCOVERY_ENABLED", "false").lower() == "true":
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

        logger.info("Sequential workflow completed")
        return {"status": "completed"}

    @listen("validate_data_integration")
    async def analyze_and_update_portfolio(self) -> dict[str, Any]:
        """
        Perform deep analysis and update portfolio review.

        Delegates to DeepAnalysisOrchestrator.

        Returns:
            dict: Consolidated analysis results with alternatives

        """
        result: dict[str, Any] = await self.deep_analysis_orch.analyze_and_update_portfolio()
        return result

    @listen("analyze_and_update_portfolio")
    async def check_portfolio(self) -> dict[str, Any]:
        """
        Run portfolio keep-or-sell review.

        Delegates to ValidationOrchestrator.

        Returns:
            dict: Portfolio review results with decisions

        """
        result: dict[str, Any] = await self.validation_orch.check_portfolio()
        return result

    @listen("check_portfolio")
    def check_crypto(self) -> dict[str, Any]:
        """
        Initiate cryptocurrency discovery.

        Delegates to DiscoveryOrchestrator.

        Returns:
            dict: Crypto discovery results

        """
        result: dict[str, Any] = self.discovery_orch.check_crypto()
        return result

    @listen("check_portfolio")
    def check_stock(self) -> dict[str, Any]:
        """
        Initiate stock discovery.

        Delegates to DiscoveryOrchestrator.

        Returns:
            dict: Stock discovery results

        """
        result: dict[str, Any] = self.discovery_orch.check_stock()
        return result

    @listen("check_portfolio")
    def check_etf(self) -> dict[str, Any]:
        """
        Initiate ETF discovery.

        Delegates to DiscoveryOrchestrator.

        Returns:
            dict: ETF discovery results

        """
        result: dict[str, Any] = self.discovery_orch.check_etf()
        return result

    @listen(and_("check_crypto", "check_stock", "check_etf"))
    def check_investment_discovery(self) -> dict[str, Any]:
        """
        Consolidate discovery results.

        Delegates to DiscoveryOrchestrator.

        Returns:
            dict: Consolidated discovery results

        """
        result: dict[str, Any] = self.discovery_orch.check_investment_discovery()
        return result

    @listen("check_investment_discovery")
    def match_alternatives_after_discovery(self, discovery_data: dict[str, Any]) -> dict[str, Any]:
        """
        Match alternatives from discovery results.

        Delegates to AlternativesMatchingOrchestrator.

        Args:
            discovery_data: Discovery results from upstream

        Returns:
            dict: Alternative matching results

        """
        result: dict[str, Any] = self.alternatives_orch.match_alternatives_after_discovery(discovery_data)
        return result

    @listen("match_alternatives_after_discovery")
    def check_portfolio_rebalancing(self) -> dict[str, Any]:
        """
        Run portfolio rebalancing analysis.

        Delegates to ValidationOrchestrator.

        Returns:
            dict: Rebalancing analysis results

        """
        result: dict[str, Any] = self.validation_orch.check_portfolio_rebalancing()
        return result

    @listen("check_portfolio_rebalancing")
    def pre_validate_reporter_input(self) -> dict[str, Any]:
        """
        Pre-validate reporter input data.

        Delegates to ValidationOrchestrator.

        Returns:
            dict: Validation results with consolidated data

        """
        result: dict[str, Any] = self.validation_orch.pre_validate_reporter_input()
        return result

    @listen("pre_validate_reporter_input")
    def report(self) -> dict[str, Any]:
        """
        Generate consolidated report.

        Delegates to ReportingOrchestrator.

        Returns:
            dict: Final report path and generation status

        """
        result: dict[str, Any] = self.reporting_orch.report()
        return result


def plot() -> None:
    """Initialize the FinWiz analysis flow and plot its structure."""
    logger.info("Plotting FinWiz analysis flow structure")
    flow = FinwizFlow()
    flow.plot()
