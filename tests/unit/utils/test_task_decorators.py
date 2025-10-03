"""Unit tests for task decorators."""

from crewai import Task

from finwiz.utils.task_decorators import async_task, sync_task


class TestAsyncTaskDecorator:
    """Tests for async_task decorator."""

    def test_should_set_async_execution_true_when_decorator_applied(self, mocker):
        """Test async_task decorator sets async_execution=True."""
        # Arrange
        mock_task = mocker.Mock(spec=Task)
        mock_task.description = "Test async task"
        mock_task.async_execution = None
        mock_logger = mocker.patch("finwiz.utils.task_decorators.logger")

        @async_task
        def create_task():
            return mock_task

        # Act
        result = create_task()

        # Assert
        assert result.async_execution is True
        mock_logger.debug.assert_called_once()
        assert "async execution" in mock_logger.debug.call_args[0][0]

    def test_should_preserve_function_metadata_when_decorator_applied(self):
        """Test async_task decorator preserves function metadata."""
        # Arrange
        @async_task
        def test_function():
            """Test docstring."""
            pass

        # Assert
        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test docstring."

    def test_should_handle_task_without_description_when_logging(self, mocker):
        """Test async_task decorator handles tasks without description."""
        # Arrange
        mock_task = mocker.Mock(spec=Task)
        mock_task.description = None
        mock_task.async_execution = None
        mock_logger = mocker.patch("finwiz.utils.task_decorators.logger")

        @async_task
        def create_task():
            return mock_task

        # Act
        result = create_task()

        # Assert
        assert result.async_execution is True
        mock_logger.debug.assert_called_once()
        assert "unnamed" in mock_logger.debug.call_args[0][0]


class TestSyncTaskDecorator:
    """Tests for sync_task decorator."""

    def test_should_set_async_execution_false_when_decorator_applied(self, mocker):
        """Test sync_task decorator sets async_execution=False."""
        # Arrange
        mock_task = mocker.Mock(spec=Task)
        mock_task.description = "Test sync task"
        mock_task.async_execution = None
        mock_logger = mocker.patch("finwiz.utils.task_decorators.logger")

        @sync_task
        def create_task():
            return mock_task

        # Act
        result = create_task()

        # Assert
        assert result.async_execution is False
        mock_logger.debug.assert_called_once()
        assert "sync execution" in mock_logger.debug.call_args[0][0]

    def test_should_preserve_function_metadata_when_decorator_applied(self):
        """Test sync_task decorator preserves function metadata."""
        # Arrange
        @sync_task
        def test_function():
            """Test docstring."""
            pass

        # Assert
        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test docstring."

    def test_should_handle_task_without_description_when_logging(self, mocker):
        """Test sync_task decorator handles tasks without description."""
        # Arrange
        mock_task = mocker.Mock(spec=Task)
        mock_task.description = None
        mock_task.async_execution = None
        mock_logger = mocker.patch("finwiz.utils.task_decorators.logger")

        @sync_task
        def create_task():
            return mock_task

        # Act
        result = create_task()

        # Assert
        assert result.async_execution is False
        mock_logger.debug.assert_called_once()
        assert "unnamed" in mock_logger.debug.call_args[0][0]


class TestDecoratorIntegration:
    """Integration tests for task decorators."""

    def test_should_work_with_function_arguments_when_decorator_applied(self, mocker):
        """Test decorators work with functions that accept arguments."""
        # Arrange
        mock_task = mocker.Mock(spec=Task)
        mock_task.description = "Test task"
        mock_task.async_execution = None
        mocker.patch("finwiz.utils.task_decorators.logger")

        @async_task
        def create_task(self, config):
            return mock_task

        # Act
        result = create_task(None, {"key": "value"})

        # Assert
        assert result.async_execution is True

    def test_should_work_with_keyword_arguments_when_decorator_applied(self, mocker):
        """Test decorators work with functions that accept keyword arguments."""
        # Arrange
        mock_task = mocker.Mock(spec=Task)
        mock_task.description = "Test task"
        mock_task.async_execution = None
        mocker.patch("finwiz.utils.task_decorators.logger")

        @sync_task
        def create_task(self, config=None):
            return mock_task

        # Act
        result = create_task(None, config={"key": "value"})

        # Assert
        assert result.async_execution is False
