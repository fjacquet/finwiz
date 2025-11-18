"""
Unit tests for SupabaseClient connectivity test.

Tests connectivity test functionality including:
- Successful connectivity test
- Failed connectivity test (timeout)
- Failed connectivity test (exception)
- Disabled Supabase integration
- Missing credentials
"""

import pytest

from finwiz.supabase.client import SupabaseClient


class TestSupabaseClientConnectivity:
    """Test suite for SupabaseClient connectivity test."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset SupabaseClient singleton before each test."""
        SupabaseClient._instance = None
        yield
        SupabaseClient._instance = None

    @pytest.fixture
    def client(self, mocker):
        """Create SupabaseClient with mocked environment."""
        mocker.patch.dict(
            "os.environ",
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key",
                "SUPABASE_ENABLED": "true",
                "SUPABASE_CONNECTIVITY_TEST_TIMEOUT": "5.0",
            },
        )
        return SupabaseClient()

    @pytest.mark.asyncio
    async def test_should_pass_connectivity_test_when_supabase_available(self, client, mocker):
        """Test successful connectivity test."""
        # Arrange
        mock_result = mocker.Mock()
        mock_result.data = [{"id": "test-id"}]
        mocker.patch.object(client, "execute_with_timeout", return_value=mock_result)

        # Act
        result = await client.test_connectivity()

        # Assert
        assert result is True
        assert client.is_available is True

    @pytest.mark.asyncio
    async def test_should_fail_connectivity_test_when_timeout(self, client, mocker):
        """Test connectivity test failure due to timeout."""
        # Arrange
        mocker.patch.object(client, "get_api_client", return_value=None)

        # Act & Assert
        with pytest.raises(ConnectionError, match="Could not create API client"):
            await client.test_connectivity()

        assert client.is_available is False

    @pytest.mark.asyncio
    async def test_should_fail_connectivity_test_when_exception(self, client, mocker):
        """Test connectivity test failure due to exception."""
        # Arrange
        mocker.patch.object(
            client,
            "get_api_client",
            side_effect=Exception("Connection error"),
        )

        # Act & Assert
        with pytest.raises(ConnectionError, match="Connection error"):
            await client.test_connectivity()

        assert client.is_available is False

    @pytest.mark.asyncio
    async def test_should_fail_connectivity_test_when_disabled(self, mocker):
        """Test connectivity test when Supabase is disabled."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key",
                "SUPABASE_ENABLED": "false",
            },
        )
        client = SupabaseClient()

        # Act
        result = await client.test_connectivity()

        # Assert
        assert result is False
        assert client.is_available is False

    @pytest.mark.asyncio
    async def test_should_fail_connectivity_test_when_missing_credentials(self, mocker):
        """Test connectivity test when credentials are missing."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "SUPABASE_URL": "",
                "SUPABASE_KEY": "",
                "SUPABASE_ENABLED": "true",
            },
        )
        client = SupabaseClient()

        # Act
        result = await client.test_connectivity()

        # Assert
        assert result is False
        assert client.is_available is False

    @pytest.mark.asyncio
    async def test_should_use_configured_timeout(self, mocker):
        """Test that connectivity test uses configured timeout."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key",
                "SUPABASE_ENABLED": "true",
                "SUPABASE_CONNECTIVITY_TEST_TIMEOUT": "3.0",
            },
        )
        client = SupabaseClient()
        mock_get_api_client = mocker.patch.object(client, "get_api_client", return_value=mocker.Mock())

        # Act
        await client.test_connectivity()

        # Assert
        assert client.connectivity_test_timeout == 3.0
        mock_get_api_client.assert_called_once()


class TestSupabaseClientMetrics:
    """Test suite for SupabaseClient metrics tracking."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset SupabaseClient singleton before each test."""
        SupabaseClient._instance = None
        yield
        SupabaseClient._instance = None

    @pytest.fixture
    def client(self, mocker):
        """Create SupabaseClient with mocked environment."""
        mocker.patch.dict(
            "os.environ",
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key",
                "SUPABASE_ENABLED": "true",
            },
        )
        return SupabaseClient()

    def test_should_initialize_metrics_to_zero(self, client):
        """Test that metrics are initialized to zero."""
        # Assert
        assert client.total_operations == 0
        assert client.successful_operations == 0
        assert client.failed_operations == 0
        assert client.timeout_count == 0
        assert client.response_times == []

    def test_should_calculate_success_rate_correctly(self, client):
        """Test success rate calculation."""
        # Arrange
        client.total_operations = 100
        client.successful_operations = 85
        client.failed_operations = 15

        # Act
        success_rate = client.get_success_rate()

        # Assert
        assert success_rate == 0.85

    def test_should_return_zero_success_rate_when_no_operations(self, client):
        """Test success rate is zero when no operations."""
        # Act
        success_rate = client.get_success_rate()

        # Assert
        assert success_rate == 0.0

    def test_should_calculate_avg_response_time_correctly(self, client):
        """Test average response time calculation."""
        # Arrange
        client.response_times = [100.0, 200.0, 300.0]

        # Act
        avg_time = client.get_avg_response_time()

        # Assert
        assert avg_time == 200.0

    def test_should_return_zero_avg_response_time_when_no_data(self, client):
        """Test average response time is zero when no data."""
        # Act
        avg_time = client.get_avg_response_time()

        # Assert
        assert avg_time == 0.0

    def test_should_record_response_time_correctly(self, client):
        """Test response time recording."""
        # Act
        client._record_response_time(150.5)
        client._record_response_time(250.3)

        # Assert
        assert len(client.response_times) == 2
        assert client.response_times[0] == 150.5
        assert client.response_times[1] == 250.3

    def test_should_limit_response_times_to_max(self, client):
        """Test that response times are limited to max_response_times."""
        # Arrange
        client.max_response_times = 5

        # Act - Add 10 response times
        for i in range(10):
            client._record_response_time(float(i * 100))

        # Assert - Should only keep last 5
        assert len(client.response_times) == 5
        assert client.response_times == [500.0, 600.0, 700.0, 800.0, 900.0]

    def test_should_get_health_status_correctly(self, client):
        """Test health status retrieval."""
        # Arrange
        client.is_available = True
        client.total_operations = 100
        client.successful_operations = 90
        client.failed_operations = 10
        client.timeout_count = 5
        client.response_times = [100.0, 200.0, 300.0]

        # Act
        health = client.get_health_status()

        # Assert
        assert health.is_available is True
        assert health.success_rate == 0.9
        assert health.avg_response_time == 200.0
        assert health.timeout_count == 5
        assert health.total_operations == 100
        assert health.successful_operations == 90
        assert health.failed_operations == 10
        assert health.circuit_breaker_open is False
        assert "url" in health.configuration
        assert "read_timeout" in health.configuration

    def test_should_reset_metrics_correctly(self, client):
        """Test metrics reset."""
        # Arrange
        client.total_operations = 100
        client.successful_operations = 90
        client.failed_operations = 10
        client.timeout_count = 5
        client.response_times = [100.0, 200.0]

        # Act
        client.reset_metrics()

        # Assert
        assert client.total_operations == 0
        assert client.successful_operations == 0
        assert client.failed_operations == 0
        assert client.timeout_count == 0
        assert client.response_times == []

    def test_should_log_metrics_every_100_operations(self, client):
        """Test that should_log_metrics returns True every 100 operations."""
        # Arrange & Act & Assert
        client.total_operations = 0
        assert client.should_log_metrics() is False

        client.total_operations = 50
        assert client.should_log_metrics() is False

        client.total_operations = 100
        assert client.should_log_metrics() is True

        client.total_operations = 200
        assert client.should_log_metrics() is True

        client.total_operations = 150
        assert client.should_log_metrics() is False
