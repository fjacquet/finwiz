"""
Unit tests for Supabase PortfolioRepository.

Tests portfolio repository functionality including:
- create_snapshot() with valid portfolio data
- get_snapshots() retrieval ordered by date
- compare_snapshots() change calculation
- Async execution (non-blocking)
- Mock Supabase client
"""

from pytest import approx
import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from finwiz.supabase.client import SupabaseClient
from finwiz.supabase.models import PortfolioSnapshot
from finwiz.supabase.repositories.portfolio_repository import PortfolioRepository


class TestPortfolioRepository:
    """Test suite for PortfolioRepository."""

    @pytest.fixture
    def mock_client(self, mocker):
        """Create mock SupabaseClient."""
        return mocker.Mock(spec=SupabaseClient)

    @pytest.fixture
    def portfolio_repository(self, mock_client):
        """Create PortfolioRepository with mock client."""
        return PortfolioRepository(client=mock_client)

    @pytest.fixture
    def sample_holdings(self):
        """Create sample portfolio holdings."""
        return {
            "AAPL": {
                "quantity": 100,
                "value": 15000.0,
                "grade": "A+",
                "recommendation": "BUY",
            },
            "GOOGL": {
                "quantity": 50,
                "value": 7500.0,
                "grade": "A",
                "recommendation": "HOLD",
            },
            "MSFT": {
                "quantity": 75,
                "value": 22500.0,
                "grade": "A+",
                "recommendation": "BUY",
            },
        }

    @pytest.fixture
    def sample_snapshot(self):
        """Create sample PortfolioSnapshot."""
        return PortfolioSnapshot(
            id="550e8400-e29b-41d4-a716-446655440000",
            snapshot_date=datetime.now(UTC),
            total_value=45000.0,
            holdings={
                "AAPL": {
                    "quantity": 100,
                    "value": 15000.0,
                    "grade": "A+",
                    "recommendation": "BUY",
                },
                "GOOGL": {
                    "quantity": 50,
                    "value": 7500.0,
                    "grade": "A",
                    "recommendation": "HOLD",
                },
                "MSFT": {
                    "quantity": 75,
                    "value": 22500.0,
                    "grade": "A+",
                    "recommendation": "BUY",
                },
            },
            created_at=datetime.now(UTC),
        )

    @pytest.mark.asyncio
    async def test_should_initialize_with_client(self, mock_client):
        """Test PortfolioRepository initialization."""
        # Act
        repository = PortfolioRepository(client=mock_client)

        # Assert
        assert repository.client == mock_client
        assert repository.table == "portfolio_snapshots"

    @pytest.mark.asyncio
    async def test_should_create_snapshot_with_valid_data(self, portfolio_repository, mock_client, sample_holdings, mocker):
        """Test create_snapshot() with valid portfolio data."""
        # Arrange
        total_value = 45000.0
        snapshot_date = datetime.now(UTC)

        # Mock execute_with_timeout to return success
        mock_result = mocker.Mock()
        mock_result.data = [{"id": "test-id"}]
        mock_client.execute_with_timeout = mocker.AsyncMock(return_value=mock_result)

        # Act
        result = await portfolio_repository.create_snapshot(
            total_value=total_value,
            holdings=sample_holdings,
            snapshot_date=snapshot_date,
        )

        # Assert
        assert result is True  # Returns immediately

    @pytest.mark.asyncio
    async def test_should_create_snapshot_with_default_date(self, portfolio_repository, mock_client, sample_holdings, mocker):
        """Test create_snapshot() uses current time when date not provided."""
        # Arrange
        total_value = 45000.0

        # Mock execute_with_timeout
        mock_result = mocker.Mock()
        mock_result.data = [{"id": "test-id"}]
        mock_client.execute_with_timeout = mocker.AsyncMock(return_value=mock_result)

        # Act
        result = await portfolio_repository.create_snapshot(
            total_value=total_value,
            holdings=sample_holdings,
            snapshot_date=None,  # Should use current time
        )

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_should_execute_snapshot_creation_asynchronously(self, portfolio_repository, mock_client, sample_holdings, mocker):
        """Test async execution (non-blocking) of create_snapshot()."""
        # Arrange
        total_value = 45000.0
        snapshot_date = datetime.now(UTC)

        # Track if background task was created
        original_create_task = asyncio.create_task
        task_created = False

        def mock_create_task(coro):
            nonlocal task_created
            task_created = True
            # Create actual task but don't await it
            return original_create_task(coro)

        mocker.patch("asyncio.create_task", side_effect=mock_create_task)

        # Mock execute_with_timeout
        mock_result = mocker.Mock()
        mock_result.data = [{"id": "test-id"}]
        mock_client.execute_with_timeout = mocker.AsyncMock(return_value=mock_result)

        # Act
        result = await portfolio_repository.create_snapshot(
            total_value=total_value,
            holdings=sample_holdings,
            snapshot_date=snapshot_date,
        )

        # Assert
        assert result is True  # Returns immediately
        assert task_created is True  # Background task was created

    @pytest.mark.asyncio
    async def test_should_get_snapshots_ordered_by_date(self, portfolio_repository, mock_client, mocker):
        """Test get_snapshots() retrieval ordered by date descending."""
        # Arrange
        now = datetime.now(UTC)
        mock_data = [
            {
                "id": "id-3",
                "snapshot_date": now.isoformat(),
                "total_value": 50000.0,
                "holdings": {"AAPL": {"value": 50000.0}},
                "created_at": now.isoformat(),
            },
            {
                "id": "id-2",
                "snapshot_date": (now - timedelta(days=1)).isoformat(),
                "total_value": 48000.0,
                "holdings": {"AAPL": {"value": 48000.0}},
                "created_at": (now - timedelta(days=1)).isoformat(),
            },
            {
                "id": "id-1",
                "snapshot_date": (now - timedelta(days=2)).isoformat(),
                "total_value": 45000.0,
                "holdings": {"AAPL": {"value": 45000.0}},
                "created_at": (now - timedelta(days=2)).isoformat(),
            },
        ]

        mock_result = mocker.Mock()
        mock_result.data = mock_data
        mock_client.execute_with_timeout = mocker.AsyncMock(return_value=mock_result)

        # Act
        snapshots = await portfolio_repository.get_snapshots(limit=10)

        # Assert
        assert len(snapshots) == 3
        assert isinstance(snapshots[0], PortfolioSnapshot)
        assert snapshots[0].id == "id-3"  # Most recent first
        assert snapshots[1].id == "id-2"
        assert snapshots[2].id == "id-1"  # Oldest last

        # Verify execute_with_timeout was called (timeout is handled internally by client)
        mock_client.execute_with_timeout.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_return_empty_list_when_no_snapshots(self, portfolio_repository, mock_client, mocker):
        """Test get_snapshots() returns empty list when no snapshots exist."""
        # Arrange
        mock_result = mocker.Mock()
        mock_result.data = []
        mock_client.execute_with_timeout = mocker.AsyncMock(return_value=mock_result)

        # Act
        snapshots = await portfolio_repository.get_snapshots()

        # Assert
        assert snapshots == []

    @pytest.mark.asyncio
    async def test_should_handle_get_snapshots_timeout(self, portfolio_repository, mock_client, mocker):
        """Test get_snapshots() handles timeout gracefully."""
        # Arrange
        mock_client.execute_with_timeout = mocker.AsyncMock(return_value=None)

        # Act
        snapshots = await portfolio_repository.get_snapshots()

        # Assert
        assert snapshots == []

    @pytest.mark.asyncio
    async def test_should_handle_get_snapshots_error(self, portfolio_repository, mock_client, mocker):
        """Test get_snapshots() handles errors gracefully."""
        # Arrange
        mock_client.execute_with_timeout = mocker.AsyncMock(side_effect=Exception("Database error"))

        # Act
        snapshots = await portfolio_repository.get_snapshots()

        # Assert
        assert snapshots == []

    @pytest.mark.asyncio
    async def test_should_compare_snapshots_and_calculate_changes(self, portfolio_repository):
        """Test compare_snapshots() change calculation."""
        # Arrange
        snapshot1 = PortfolioSnapshot(
            id="id-1",
            snapshot_date=datetime.now(UTC) - timedelta(days=7),
            total_value=45000.0,
            holdings={
                "AAPL": {
                    "quantity": 100,
                    "value": 15000.0,
                    "grade": "A",
                    "recommendation": "HOLD",
                },
                "GOOGL": {
                    "quantity": 50,
                    "value": 7500.0,
                    "grade": "B+",
                    "recommendation": "HOLD",
                },
                "MSFT": {
                    "quantity": 75,
                    "value": 22500.0,
                    "grade": "A+",
                    "recommendation": "BUY",
                },
            },
            created_at=datetime.now(UTC) - timedelta(days=7),
        )

        snapshot2 = PortfolioSnapshot(
            id="id-2",
            snapshot_date=datetime.now(UTC),
            total_value=50000.0,
            holdings={
                "AAPL": {
                    "quantity": 120,  # Increased quantity
                    "value": 18000.0,  # Increased value
                    "grade": "A+",  # Upgraded
                    "recommendation": "BUY",  # Changed recommendation
                },
                "MSFT": {
                    "quantity": 75,
                    "value": 25000.0,  # Value increased
                    "grade": "A+",
                    "recommendation": "BUY",
                },
                "TSLA": {  # New holding
                    "quantity": 50,
                    "value": 7000.0,
                    "grade": "B",
                    "recommendation": "HOLD",
                },
            },
            created_at=datetime.now(UTC),
        )

        # Act
        comparison = await portfolio_repository.compare_snapshots(snapshot1, snapshot2)

        # Assert
        assert comparison["value_change"] == approx(5000.0)  # 50000 - 45000
        assert comparison["value_change_pct"] == pytest.approx(11.11, rel=0.01)

        # Check holdings changes
        assert "TSLA" in comparison["holdings_added"]
        assert "GOOGL" in comparison["holdings_removed"]

        # Check modified holdings
        assert "AAPL" in comparison["holdings_modified"]
        assert "MSFT" in comparison["holdings_modified"]

        # Check AAPL modifications
        aapl_changes = comparison["holdings_modified"]["AAPL"]
        assert aapl_changes["quantity"]["old"] == 100
        assert aapl_changes["quantity"]["new"] == 120
        assert aapl_changes["value"]["old"] == approx(15000.0)
        assert aapl_changes["value"]["new"] == approx(18000.0)
        assert aapl_changes["grade"]["old"] == "A"
        assert aapl_changes["grade"]["new"] == "A+"
        assert aapl_changes["recommendation"]["old"] == "HOLD"
        assert aapl_changes["recommendation"]["new"] == "BUY"

        # Check grade changes
        assert "AAPL" in comparison["grade_changes"]
        assert comparison["grade_changes"]["AAPL"]["old"] == "A"
        assert comparison["grade_changes"]["AAPL"]["new"] == "A+"

    @pytest.mark.asyncio
    async def test_should_compare_snapshots_with_no_changes(self, portfolio_repository):
        """Test compare_snapshots() when holdings are identical."""
        # Arrange
        holdings = {
            "AAPL": {
                "quantity": 100,
                "value": 15000.0,
                "grade": "A+",
                "recommendation": "BUY",
            }
        }

        snapshot1 = PortfolioSnapshot(
            id="id-1",
            snapshot_date=datetime.now(UTC) - timedelta(days=1),
            total_value=15000.0,
            holdings=holdings,
            created_at=datetime.now(UTC) - timedelta(days=1),
        )

        snapshot2 = PortfolioSnapshot(
            id="id-2",
            snapshot_date=datetime.now(UTC),
            total_value=15000.0,
            holdings=holdings,
            created_at=datetime.now(UTC),
        )

        # Act
        comparison = await portfolio_repository.compare_snapshots(snapshot1, snapshot2)

        # Assert
        assert comparison["value_change"] == approx(0.0)
        assert comparison["value_change_pct"] == approx(0.0)
        assert comparison["holdings_added"] == []
        assert comparison["holdings_removed"] == []
        assert comparison["holdings_modified"] == {}
        assert comparison["grade_changes"] == {}

    @pytest.mark.asyncio
    async def test_should_handle_zero_initial_value_in_comparison(self, portfolio_repository):
        """Test compare_snapshots() handles zero initial value correctly."""
        # Arrange
        snapshot1 = PortfolioSnapshot(
            id="id-1",
            snapshot_date=datetime.now(UTC) - timedelta(days=1),
            total_value=0.0,  # Zero initial value
            holdings={},
            created_at=datetime.now(UTC) - timedelta(days=1),
        )

        snapshot2 = PortfolioSnapshot(
            id="id-2",
            snapshot_date=datetime.now(UTC),
            total_value=10000.0,
            holdings={"AAPL": {"quantity": 100, "value": 10000.0}},
            created_at=datetime.now(UTC),
        )

        # Act
        comparison = await portfolio_repository.compare_snapshots(snapshot1, snapshot2)

        # Assert
        assert comparison["value_change"] == approx(10000.0)
        assert comparison["value_change_pct"] == approx(0.0)  # Avoid division by zero

    @pytest.mark.asyncio
    async def test_should_get_snapshot_by_id(self, portfolio_repository, mock_client, mocker):
        """Test get_snapshot_by_id() retrieves specific snapshot."""
        # Arrange
        snapshot_id = "550e8400-e29b-41d4-a716-446655440000"
        now = datetime.now(UTC)

        mock_data = {
            "id": snapshot_id,
            "snapshot_date": now.isoformat(),
            "total_value": 45000.0,
            "holdings": {"AAPL": {"value": 45000.0}},
            "created_at": now.isoformat(),
        }

        mock_result = mocker.Mock()
        mock_result.data = [mock_data]
        mock_client.execute_with_timeout = mocker.AsyncMock(return_value=mock_result)

        # Act
        snapshot = await portfolio_repository.get_snapshot_by_id(snapshot_id)

        # Assert
        assert snapshot is not None
        assert isinstance(snapshot, PortfolioSnapshot)
        assert snapshot.id == snapshot_id
        assert snapshot.total_value == approx(45000.0)

    @pytest.mark.asyncio
    async def test_should_return_none_when_snapshot_not_found(self, portfolio_repository, mock_client, mocker):
        """Test get_snapshot_by_id() returns None when snapshot not found."""
        # Arrange
        snapshot_id = "nonexistent-id"

        mock_result = mocker.Mock()
        mock_result.data = []
        mock_client.execute_with_timeout = mocker.AsyncMock(return_value=mock_result)

        # Act
        snapshot = await portfolio_repository.get_snapshot_by_id(snapshot_id)

        # Assert
        assert snapshot is None

    @pytest.mark.asyncio
    async def test_should_handle_get_snapshot_by_id_error(self, portfolio_repository, mock_client, mocker):
        """Test get_snapshot_by_id() handles errors gracefully."""
        # Arrange
        snapshot_id = "test-id"
        mock_client.execute_with_timeout = mocker.AsyncMock(side_effect=Exception("Database error"))

        # Act
        snapshot = await portfolio_repository.get_snapshot_by_id(snapshot_id)

        # Assert
        assert snapshot is None

    @pytest.mark.asyncio
    async def test_should_respect_limit_parameter(self, portfolio_repository, mock_client, mocker):
        """Test get_snapshots() respects limit parameter."""
        # Arrange
        now = datetime.now(UTC)
        mock_data = [
            {
                "id": f"id-{i}",
                "snapshot_date": (now - timedelta(days=i)).isoformat(),
                "total_value": 45000.0 + i * 1000,
                "holdings": {"AAPL": {"value": 45000.0}},
                "created_at": (now - timedelta(days=i)).isoformat(),
            }
            for i in range(5)
        ]

        mock_result = mocker.Mock()
        mock_result.data = mock_data
        mock_client.execute_with_timeout = mocker.AsyncMock(return_value=mock_result)

        # Act
        snapshots = await portfolio_repository.get_snapshots(limit=5)

        # Assert
        assert len(snapshots) == 5

    @pytest.mark.asyncio
    async def test_should_track_grade_evolution_across_snapshots(self, portfolio_repository):
        """Test compare_snapshots() tracks grade evolution correctly."""
        # Arrange
        snapshot1 = PortfolioSnapshot(
            id="id-1",
            snapshot_date=datetime.now(UTC) - timedelta(days=1),
            total_value=30000.0,
            holdings={
                "AAPL": {"grade": "B+"},
                "GOOGL": {"grade": "A"},
                "MSFT": {"grade": "C"},
            },
            created_at=datetime.now(UTC) - timedelta(days=1),
        )

        snapshot2 = PortfolioSnapshot(
            id="id-2",
            snapshot_date=datetime.now(UTC),
            total_value=35000.0,
            holdings={
                "AAPL": {"grade": "A+"},  # Upgraded
                "GOOGL": {"grade": "A"},  # No change
                "MSFT": {"grade": "B"},  # Upgraded
            },
            created_at=datetime.now(UTC),
        )

        # Act
        comparison = await portfolio_repository.compare_snapshots(snapshot1, snapshot2)

        # Assert
        grade_changes = comparison["grade_changes"]
        assert len(grade_changes) == 2  # Only AAPL and MSFT changed

        assert "AAPL" in grade_changes
        assert grade_changes["AAPL"]["old"] == "B+"
        assert grade_changes["AAPL"]["new"] == "A+"

        assert "MSFT" in grade_changes
        assert grade_changes["MSFT"]["old"] == "C"
        assert grade_changes["MSFT"]["new"] == "B"

        assert "GOOGL" not in grade_changes  # No change

    @pytest.mark.asyncio
    async def test_should_handle_missing_grade_in_holdings(self, portfolio_repository):
        """Test compare_snapshots() handles missing grade fields gracefully."""
        # Arrange
        snapshot1 = PortfolioSnapshot(
            id="id-1",
            snapshot_date=datetime.now(UTC) - timedelta(days=1),
            total_value=15000.0,
            holdings={"AAPL": {"value": 15000.0}},  # No grade field
            created_at=datetime.now(UTC) - timedelta(days=1),
        )

        snapshot2 = PortfolioSnapshot(
            id="id-2",
            snapshot_date=datetime.now(UTC),
            total_value=18000.0,
            holdings={"AAPL": {"value": 18000.0, "grade": "A+"}},  # Grade added
            created_at=datetime.now(UTC),
        )

        # Act
        comparison = await portfolio_repository.compare_snapshots(snapshot1, snapshot2)

        # Assert
        assert "AAPL" in comparison["holdings_modified"]
        assert "grade" in comparison["holdings_modified"]["AAPL"]
        assert comparison["holdings_modified"]["AAPL"]["grade"]["old"] is None
        assert comparison["holdings_modified"]["AAPL"]["grade"]["new"] == "A+"

        # Grade change should be tracked
        assert "AAPL" in comparison["grade_changes"]
        assert comparison["grade_changes"]["AAPL"]["old"] == "N/A"
        assert comparison["grade_changes"]["AAPL"]["new"] == "A+"