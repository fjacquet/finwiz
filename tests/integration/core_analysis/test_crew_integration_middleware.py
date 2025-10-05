"""
Tests for CrewIntegrationMiddleware.

Tests pre-execution hooks, post-execution hooks, dependency validation,
data storage, and crew execution coordination.
"""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from finwiz.integration.manager import CrewConfig, ExecutionResult
from finwiz.integration.middleware import CrewExecutionContext, CrewIntegrationMiddleware, PostExecutionResult, PreExecutionResult


class TestCrewIntegrationMiddleware:
    """Test suite for CrewIntegrationMiddleware."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_integration_manager(self, mocker):
        """Create mock integration manager."""
        manager = mocker.MagicMock()
        manager.get_crew_data_with_freshness_check.return_value = {"test": "data"}
        manager.freshness_checker.check_data_freshness_for_crew.return_value = mocker.MagicMock(
            freshness_status=mocker.MagicMock(is_fresh=True)
        )
        manager.coordinate_crew_execution = mocker.AsyncMock(
            return_value=ExecutionResult(success=True, executed_crews=["test_crew"], failed_crews=[], execution_time=1.0, errors=[])
        )
        return manager

    @pytest.fixture
    def mock_data_accessor(self, mocker):
        """Create mock data accessor."""
        accessor = mocker.MagicMock()
        return accessor

    @pytest.fixture
    def mock_validation_pipeline(self, mocker):
        """Create mock validation pipeline."""
        pipeline = mocker.MagicMock()
        pipeline.validate_crew_output = mocker.AsyncMock(return_value=mocker.MagicMock(is_valid=True, errors=[], warnings=[]))
        return pipeline

    @pytest.fixture
    def middleware(self, temp_output_dir, mock_integration_manager, mock_data_accessor, mock_validation_pipeline):
        """Create middleware instance with mocked dependencies."""
        return CrewIntegrationMiddleware(
            output_dir=temp_output_dir,
            integration_manager=mock_integration_manager,
            data_accessor=mock_data_accessor,
            validation_pipeline=mock_validation_pipeline,
        )

    def test_should_initialize_middleware_with_default_components(self, temp_output_dir):
        """Test middleware initialization with default components."""
        # Act
        middleware = CrewIntegrationMiddleware(output_dir=temp_output_dir)

        # Assert
        assert middleware.output_dir == temp_output_dir
        assert middleware.integration_dir == temp_output_dir / "integration"
        assert middleware.integration_manager is not None
        assert middleware.data_accessor is not None
        assert middleware.validation_pipeline is not None
        assert len(middleware.active_executions) == 0
        assert "pre_execution" in middleware.execution_hooks
        assert "post_execution" in middleware.execution_hooks
        assert "on_error" in middleware.execution_hooks

    def test_should_register_custom_hooks(self, middleware):
        """Test registering custom hook functions."""

        # Arrange
        async def test_hook(context):
            pass

        # Act
        middleware.register_hook("pre_execution", test_hook)

        # Assert
        assert test_hook in middleware.execution_hooks["pre_execution"]

    def test_should_raise_error_for_invalid_hook_type(self, middleware, mocker):
        """Test error handling for invalid hook types."""

        # Arrange
        async def test_hook(context, mocker):
            pass

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid hook type"):
            middleware.register_hook("invalid_hook", test_hook)

    @pytest.mark.anyio
    async def test_should_validate_dependencies_successfully_when_all_available(self, middleware, mock_integration_manager, mocker):
        """Test successful dependency validation when all dependencies are available."""
        # Arrange
        crew_name = "test_crew"
        dependencies = ["stock", "etf"]

        # Act
        result = await middleware.pre_execution_hook(crew_name, dependencies)

        # Assert
        assert result.can_proceed is True
        assert result.dependencies_met is True
        assert len(result.missing_dependencies) == 0
        assert len(result.stale_dependencies) == 0
        assert "stock" in result.upstream_data
        assert "etf" in result.upstream_data
        assert len(result.errors) == 0

        # Verify execution context was created
        assert len(middleware.active_executions) == 1
        execution_id = list(middleware.active_executions.keys())[0]
        context = middleware.active_executions[execution_id]
        assert context.crew_name == crew_name
        assert context.dependencies == dependencies

    @pytest.mark.anyio
    async def test_should_detect_missing_dependencies(self, middleware, mock_integration_manager, mocker):
        """Test detection of missing dependencies."""
        # Arrange
        crew_name = "test_crew"
        dependencies = ["stock", "missing_crew"]

        # Configure mock to return None for missing dependency
        def mock_get_data(crew, max_age, warn_on_stale=True):
            if crew == "missing_crew":
                return None
            return {"test": "data"}

        mock_integration_manager.get_crew_data_with_freshness_check.side_effect = mock_get_data

        # Act
        result = await middleware.pre_execution_hook(crew_name, dependencies)

        # Assert
        assert result.can_proceed is False
        assert result.dependencies_met is False
        assert "missing_crew" in result.missing_dependencies
        assert "stock" in result.upstream_data
        assert "missing_crew" not in result.upstream_data
        assert len(result.errors) > 0
        assert "Missing required dependencies" in result.errors[0]

    @pytest.mark.anyio
    async def test_should_detect_stale_dependencies(self, mocker, middleware, mock_integration_manager):
        """Test detection of stale dependencies."""
        # Arrange
        crew_name = "test_crew"
        dependencies = ["stock", "stale_crew"]

        # Configure mock to return stale data
        def mock_freshness_check(crew, max_age, mocker):
            if crew == "stale_crew":
                return mocker.MagicMock(freshness_status=mocker.MagicMock(is_fresh=False))
            return mocker.MagicMock(freshness_status=mocker.MagicMock(is_fresh=True))

        mock_integration_manager.freshness_checker.check_data_freshness_for_crew.side_effect = mock_freshness_check

        # Act
        result = await middleware.pre_execution_hook(crew_name, dependencies)

        # Assert
        assert result.can_proceed is True  # Stale data doesn't prevent execution
        assert result.dependencies_met is True
        assert "stale_crew" in result.stale_dependencies
        assert len(result.warnings) > 0
        assert "Stale dependencies detected" in result.warnings[0]

    @pytest.mark.anyio
    async def test_should_handle_pre_execution_errors_gracefully(self, middleware, mock_integration_manager, mocker):
        """Test error handling in pre-execution hook."""
        # Arrange
        crew_name = "test_crew"
        dependencies = ["stock"]

        # Configure mock to raise exception
        mock_integration_manager.get_crew_data_with_freshness_check.side_effect = Exception("Test error")

        # Act
        result = await middleware.pre_execution_hook(crew_name, dependencies)

        # Assert
        assert result.can_proceed is False
        assert result.dependencies_met is False
        assert len(result.errors) > 0
        assert "Missing required dependencies" in result.errors[0]

    @pytest.mark.anyio
    async def test_should_store_crew_output_successfully(self, middleware, mock_validation_pipeline, mocker):
        """Test successful crew output storage and validation."""
        # Arrange
        crew_name = "test_crew"
        dependencies = []
        crew_output = {"analysis": "test data", "recommendations": ["BUY"]}
        execution_duration = 5.5

        # First run pre-execution to create context
        await middleware.pre_execution_hook(crew_name, dependencies)
        execution_id = list(middleware.active_executions.keys())[0]

        # Act
        result = await middleware.post_execution_hook(execution_id, crew_output, execution_duration)

        # Assert
        assert result.storage_success is True
        assert result.validation_success is True
        assert result.metadata_stored is True
        assert result.lineage_updated is True
        assert len(result.errors) == 0

        # Verify output file was created
        crew_output_dir = middleware.integration_dir / crew_name
        assert crew_output_dir.exists()
        output_files = list(crew_output_dir.glob("*.json"))
        assert len(output_files) == 1

        # Verify output content
        with open(output_files[0]) as f:
            stored_data = json.load(f)
        assert stored_data["execution_id"] == execution_id
        assert stored_data["crew_name"] == crew_name
        assert stored_data["execution_duration_seconds"] == execution_duration
        assert stored_data["data"] == crew_output

        # Verify metadata file was created
        metadata_dir = middleware.integration_dir / "metadata"
        metadata_files = list(metadata_dir.glob(f"{execution_id}_metadata.json"))
        assert len(metadata_files) == 1

        # Verify lineage file was created/updated
        lineage_file = metadata_dir / "data_lineage.json"
        assert lineage_file.exists()

        with open(lineage_file) as f:
            lineage_data = json.load(f)
        assert "executions" in lineage_data
        assert len(lineage_data["executions"]) == 1
        assert lineage_data["executions"][0]["execution_id"] == execution_id

        # Verify execution context was cleaned up
        assert execution_id not in middleware.active_executions

    @pytest.mark.anyio
    async def test_should_handle_validation_failures(self, middleware, mock_validation_pipeline, mocker):
        """Test handling of validation failures in post-execution."""
        # Arrange
        crew_name = "test_crew"
        dependencies = []
        crew_output = {"invalid": "data"}

        # Configure validation to fail
        mock_validation_pipeline.validate_crew_output = mocker.AsyncMock(
            return_value=mocker.MagicMock(is_valid=False, errors=["Invalid schema"], warnings=["Missing field"])
        )

        # First run pre-execution to create context
        await middleware.pre_execution_hook(crew_name, dependencies)
        execution_id = list(middleware.active_executions.keys())[0]

        # Act
        result = await middleware.post_execution_hook(execution_id, crew_output)

        # Assert
        assert result.validation_success is False
        assert "Invalid schema" in result.errors
        assert "Missing field" in result.warnings
        # Storage should still succeed even with validation failures
        assert result.storage_success is True

    @pytest.mark.anyio
    async def test_should_handle_missing_execution_context(self, middleware):
        """Test error handling when execution context is missing."""
        # Arrange
        invalid_execution_id = "nonexistent_id"
        crew_output = {"test": "data"}

        # Act
        result = await middleware.post_execution_hook(invalid_execution_id, crew_output)

        # Assert
        assert result.storage_success is False
        assert result.validation_success is False
        assert result.metadata_stored is False
        assert result.lineage_updated is False
        assert len(result.errors) > 0
        assert "No execution context found" in result.errors[0]

    @pytest.mark.anyio
    async def test_should_execute_custom_hooks(self, middleware):
        """Test execution of custom registered hooks."""
        # Arrange
        pre_hook_called = False
        post_hook_called = False

        async def pre_hook(context):
            nonlocal pre_hook_called
            pre_hook_called = True
            assert context.crew_name == "test_crew"

        async def post_hook(context):
            nonlocal post_hook_called
            post_hook_called = True
            assert context.crew_name == "test_crew"

        middleware.register_hook("pre_execution", pre_hook)
        middleware.register_hook("post_execution", post_hook)

        crew_name = "test_crew"
        dependencies = []
        crew_output = {"test": "data"}

        # Act
        await middleware.pre_execution_hook(crew_name, dependencies)
        execution_id = list(middleware.active_executions.keys())[0]
        await middleware.post_execution_hook(execution_id, crew_output)

        # Assert
        assert pre_hook_called is True
        assert post_hook_called is True

    @pytest.mark.anyio
    async def test_should_coordinate_multiple_crews(self, middleware, mock_integration_manager):
        """Test coordination of multiple crew executions."""
        # Arrange
        crew_configs = [
            CrewConfig(name="stock", dependencies=[]),
            CrewConfig(name="etf", dependencies=["stock"]),
            CrewConfig(name="discovery", dependencies=["stock", "etf"]),
        ]

        # Act
        result = await middleware.coordinate_crew_execution(crew_configs)

        # Assert
        assert result.success is True
        assert "test_crew" in result.executed_crews
        assert len(result.failed_crews) == 0
        assert result.execution_time > 0

        # Verify integration manager was called
        mock_integration_manager.coordinate_crew_execution.assert_called_once_with(crew_configs)

    @pytest.mark.anyio
    async def test_should_handle_coordination_errors(self, middleware, mock_integration_manager):
        """Test error handling in crew coordination."""
        # Arrange
        crew_configs = [CrewConfig(name="test_crew")]
        mock_integration_manager.coordinate_crew_execution.side_effect = Exception("Coordination failed")

        # Act
        result = await middleware.coordinate_crew_execution(crew_configs)

        # Assert
        assert result.success is False
        assert "test_crew" in result.failed_crews
        assert len(result.executed_crews) == 0
        assert "Coordinated execution failed" in result.errors[0]

    def test_should_track_active_executions(self, middleware):
        """Test tracking of active executions."""
        # Arrange
        context = CrewExecutionContext(crew_name="test_crew", execution_id="test_id", start_time=datetime.now(), dependencies=[])

        # Act
        middleware.active_executions["test_id"] = context

        # Assert
        active = middleware.get_active_executions()
        assert "test_id" in active
        assert active["test_id"].crew_name == "test_crew"

        retrieved_context = middleware.get_execution_context("test_id")
        assert retrieved_context is not None
        assert retrieved_context.crew_name == "test_crew"

        missing_context = middleware.get_execution_context("nonexistent")
        assert missing_context is None

    @pytest.mark.anyio
    async def test_should_limit_lineage_entries(self, middleware):
        """Test that data lineage is limited to prevent excessive growth."""
        # Arrange
        lineage_file = middleware.integration_dir / "metadata" / "data_lineage.json"
        lineage_file.parent.mkdir(parents=True, exist_ok=True)

        # Create existing lineage with many entries
        existing_lineage = {
            "executions": [
                {
                    "execution_id": f"old_exec_{i}",
                    "crew_name": "old_crew",
                    "timestamp": datetime.now().isoformat(),
                    "dependencies": [],
                    "upstream_sources": [],
                    "output_keys": [],
                }
                for i in range(1005)  # More than the 1000 limit
            ]
        }

        with open(lineage_file, "w") as f:
            json.dump(existing_lineage, f)

        # Act - Add new execution
        crew_name = "test_crew"
        await middleware.pre_execution_hook(crew_name, [])
        execution_id = list(middleware.active_executions.keys())[0]
        await middleware.post_execution_hook(execution_id, {"test": "data"})

        # Assert
        with open(lineage_file) as f:
            updated_lineage = json.load(f)

        # Should be limited to 1000 entries
        assert len(updated_lineage["executions"]) == 1000
        # New execution should be the last entry
        assert updated_lineage["executions"][-1]["execution_id"] == execution_id
        # Old entries should be removed (first entry should not be old_exec_0)
        assert updated_lineage["executions"][0]["execution_id"] != "old_exec_0"


class TestPreExecutionResult:
    """Test PreExecutionResult model."""

    def test_should_create_valid_pre_execution_result(self):
        """Test creation of valid PreExecutionResult."""
        # Act
        result = PreExecutionResult(
            can_proceed=True,
            dependencies_met=True,
            missing_dependencies=["missing_crew"],
            stale_dependencies=["stale_crew"],
            upstream_data={"crew1": {"data": "value"}},
            warnings=["Warning message"],
            errors=["Error message"],
        )

        # Assert
        assert result.can_proceed is True
        assert result.dependencies_met is True
        assert result.missing_dependencies == ["missing_crew"]
        assert result.stale_dependencies == ["stale_crew"]
        assert result.upstream_data == {"crew1": {"data": "value"}}
        assert result.warnings == ["Warning message"]
        assert result.errors == ["Error message"]


class TestPostExecutionResult:
    """Test PostExecutionResult model."""

    def test_should_create_valid_post_execution_result(self):
        """Test creation of valid PostExecutionResult."""
        # Act
        result = PostExecutionResult(
            storage_success=True,
            validation_success=True,
            metadata_stored=True,
            lineage_updated=True,
            errors=["Error message"],
            warnings=["Warning message"],
        )

        # Assert
        assert result.storage_success is True
        assert result.validation_success is True
        assert result.metadata_stored is True
        assert result.lineage_updated is True
        assert result.errors == ["Error message"]
        assert result.warnings == ["Warning message"]


class TestCrewExecutionContext:
    """Test CrewExecutionContext model."""

    def test_should_create_valid_execution_context(self):
        """Test creation of valid CrewExecutionContext."""
        # Arrange
        start_time = datetime.now()

        # Act
        context = CrewExecutionContext(
            crew_name="test_crew",
            execution_id="test_exec_123",
            start_time=start_time,
            dependencies=["stock", "etf"],
            max_age_hours=48,
            upstream_data={"stock": {"data": "value"}},
            metadata={"key": "value"},
        )

        # Assert
        assert context.crew_name == "test_crew"
        assert context.execution_id == "test_exec_123"
        assert context.start_time == start_time
        assert context.dependencies == ["stock", "etf"]
        assert context.max_age_hours == 48
        assert context.upstream_data == {"stock": {"data": "value"}}
        assert context.metadata == {"key": "value"}
