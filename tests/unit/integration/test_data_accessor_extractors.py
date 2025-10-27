"""
Unit tests for CrewDataAccessor extractor initialization.

Tests that the enhanced data extractors are properly initialized
in the CrewDataAccessor class.
"""

import logging
from pathlib import Path

import pytest

from finwiz.integration.backtesting_extractor import BacktestingDataExtractor
from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.discovery_methodology_extractor import DiscoveryMethodologyExtractor
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.integration.market_context_extractor import MarketContextExtractor
from finwiz.integration.performance_metrics_aggregator import PerformanceMetricsAggregator


class TestCrewDataAccessorExtractorInitialization:
    """Test suite for CrewDataAccessor extractor initialization."""

    @pytest.fixture
    def integration_manager(self, tmp_path: Path) -> CrewDataIntegrationManager:
        """Create integration manager instance with temp directory."""
        return CrewDataIntegrationManager(output_dir=tmp_path)

    @pytest.fixture
    def data_accessor(self, integration_manager: CrewDataIntegrationManager) -> CrewDataAccessor:
        """Create data accessor instance."""
        return CrewDataAccessor(integration_manager)

    def test_should_initialize_backtesting_extractor(self, data_accessor: CrewDataAccessor) -> None:
        """Test that BacktestingDataExtractor is initialized."""
        # Assert
        assert hasattr(data_accessor, "backtesting_extractor")
        assert isinstance(data_accessor.backtesting_extractor, BacktestingDataExtractor)
        assert data_accessor.backtesting_extractor.logger is not None

    def test_should_initialize_market_context_extractor(self, data_accessor: CrewDataAccessor) -> None:
        """Test that MarketContextExtractor is initialized."""
        # Assert
        assert hasattr(data_accessor, "market_context_extractor")
        assert isinstance(data_accessor.market_context_extractor, MarketContextExtractor)
        assert data_accessor.market_context_extractor.logger is not None

    def test_should_initialize_methodology_extractor(self, data_accessor: CrewDataAccessor) -> None:
        """Test that DiscoveryMethodologyExtractor is initialized."""
        # Assert
        assert hasattr(data_accessor, "methodology_extractor")
        assert isinstance(data_accessor.methodology_extractor, DiscoveryMethodologyExtractor)
        assert data_accessor.methodology_extractor.logger is not None

    def test_should_initialize_performance_aggregator(self, data_accessor: CrewDataAccessor) -> None:
        """Test that PerformanceMetricsAggregator is initialized."""
        # Assert
        assert hasattr(data_accessor, "performance_aggregator")
        assert isinstance(data_accessor.performance_aggregator, PerformanceMetricsAggregator)
        assert data_accessor.performance_aggregator.logger is not None
        assert data_accessor.performance_aggregator.backtesting_extractor is not None

    def test_should_share_logger_with_extractors(self, data_accessor: CrewDataAccessor) -> None:
        """Test that all extractors share the same logger instance."""
        # Assert
        assert data_accessor.backtesting_extractor.logger == data_accessor.logger
        assert data_accessor.market_context_extractor.logger == data_accessor.logger
        assert data_accessor.methodology_extractor.logger == data_accessor.logger
        assert data_accessor.performance_aggregator.logger == data_accessor.logger

    def test_should_link_backtesting_extractor_to_performance_aggregator(self, data_accessor: CrewDataAccessor) -> None:
        """Test that PerformanceMetricsAggregator has reference to BacktestingDataExtractor."""
        # Assert
        assert data_accessor.performance_aggregator.backtesting_extractor == data_accessor.backtesting_extractor

    def test_should_initialize_all_extractors_with_integration_manager(
        self, integration_manager: CrewDataIntegrationManager
    ) -> None:
        """Test that all extractors are initialized when CrewDataAccessor is created."""
        # Act
        accessor = CrewDataAccessor(integration_manager)

        # Assert - All extractors should be initialized
        assert accessor.backtesting_extractor is not None
        assert accessor.market_context_extractor is not None
        assert accessor.methodology_extractor is not None
        assert accessor.performance_aggregator is not None

    def test_should_log_initialization_with_extractors(
        self, integration_manager: CrewDataIntegrationManager, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that initialization logs mention enhanced extractors."""
        # Arrange
        caplog.set_level(logging.INFO)

        # Act
        CrewDataAccessor(integration_manager)

        # Assert
        assert any("CrewDataAccessor initialized with enhanced extractors" in record.message for record in caplog.records)

    def test_should_maintain_backward_compatibility_with_existing_components(self, data_accessor: CrewDataAccessor) -> None:
        """Test that existing components (cache, validator) are still initialized."""
        # Assert - Existing components should still be present
        assert hasattr(data_accessor, "cache")
        assert hasattr(data_accessor, "validator")
        assert hasattr(data_accessor, "integration_manager")
        assert hasattr(data_accessor, "logger")

        # New extractors should be added without breaking existing functionality
        assert hasattr(data_accessor, "backtesting_extractor")
        assert hasattr(data_accessor, "market_context_extractor")
        assert hasattr(data_accessor, "methodology_extractor")
        assert hasattr(data_accessor, "performance_aggregator")
