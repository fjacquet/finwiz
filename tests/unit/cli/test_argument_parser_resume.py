"""
Unit tests for CLI argument parser resume functionality.

Tests the parse_arguments() and initialize_flow_with_resume() functions
for handling --resume-uuid and --no-resume CLI arguments.
"""

import argparse
from datetime import datetime

import pytest

from finwiz.cli.argument_parser import initialize_flow_with_resume, parse_arguments


class TestParseArguments:
    """Test suite for parse_arguments function."""

    def test_should_parse_no_arguments(self, mocker):
        """Test parsing with no arguments (default behavior)."""
        # Arrange
        mocker.patch("sys.argv", ["finwiz"])

        # Act
        args = parse_arguments()

        # Assert
        assert args.resume_uuid is None
        assert args.no_resume is False

    def test_should_parse_resume_uuid_argument(self, mocker):
        """Test parsing --resume-uuid argument."""
        # Arrange
        test_uuid = "abc123def456"
        mocker.patch("sys.argv", ["finwiz", "--resume-uuid", test_uuid])

        # Act
        args = parse_arguments()

        # Assert
        assert args.resume_uuid == test_uuid
        assert args.no_resume is False

    def test_should_parse_no_resume_flag(self, mocker):
        """Test parsing --no-resume flag."""
        # Arrange
        mocker.patch("sys.argv", ["finwiz", "--no-resume"])

        # Act
        args = parse_arguments()

        # Assert
        assert args.resume_uuid is None
        assert args.no_resume is True

    def test_should_parse_both_arguments(self, mocker):
        """Test parsing both --resume-uuid and --no-resume (no-resume takes precedence)."""
        # Arrange
        test_uuid = "abc123def456"
        mocker.patch("sys.argv", ["finwiz", "--resume-uuid", test_uuid, "--no-resume"])

        # Act
        args = parse_arguments()

        # Assert
        assert args.resume_uuid == test_uuid
        assert args.no_resume is True


class TestInitializeFlowWithResume:
    """Test suite for initialize_flow_with_resume function."""

    @pytest.fixture
    def mock_flow_state_manager(self, mocker):
        """Create mock FlowStateManager."""
        mock_manager = mocker.Mock()
        mocker.patch("finwiz.cli.argument_parser.FlowStateManager", return_value=mock_manager)
        return mock_manager

    @pytest.fixture
    def mock_finwiz_flow(self, mocker):
        """Create mock FinwizFlow class."""
        mock_flow_class = mocker.Mock()
        # Patch where it's imported in the function
        mocker.patch("finwiz.flows.flow_orchestrator.FinwizFlow", mock_flow_class)
        return mock_flow_class

    @pytest.fixture
    def mock_finwiz_state(self, mocker):
        """Create mock FinwizState class."""
        mock_state_class = mocker.Mock()
        # Patch where it's imported in the function
        mocker.patch("finwiz.flow_state.FinwizState", mock_state_class)
        return mock_state_class

    def test_should_start_fresh_when_no_resume_flag_set(self, mocker, mock_flow_state_manager, mock_finwiz_flow, mock_finwiz_state):
        """Test that --no-resume flag forces fresh start."""
        # Arrange
        args = argparse.Namespace(resume_uuid=None, no_resume=True)
        mock_state_instance = mocker.Mock()
        mock_finwiz_state.return_value = mock_state_instance

        # Act
        result = initialize_flow_with_resume(args)

        # Assert
        mock_finwiz_state.assert_called_once()
        mock_finwiz_flow.assert_called_once_with(state=mock_state_instance)
        mock_flow_state_manager.discover_persisted_states.assert_not_called()

    def test_should_load_specific_uuid_when_provided(self, mocker, mock_flow_state_manager, mock_finwiz_flow, mock_finwiz_state):
        """Test loading specific UUID via --resume-uuid."""
        # Arrange
        test_uuid = "abc123def456"
        args = argparse.Namespace(resume_uuid=test_uuid, no_resume=False)

        mock_state_data = {
            "holdings_processed": 10,
            "total_holdings": 20,
            "flow_start_time": datetime.now().isoformat(),
        }
        mock_flow_state_manager.load_flow_state_by_uuid.return_value = mock_state_data

        mock_state_instance = mocker.Mock()
        mock_finwiz_state.return_value = mock_state_instance

        # Act
        result = initialize_flow_with_resume(args)

        # Assert
        mock_flow_state_manager.load_flow_state_by_uuid.assert_called_once_with(test_uuid)
        mock_finwiz_state.assert_called_once_with(**mock_state_data)
        assert mock_state_instance.resume_from_checkpoint is True
        assert mock_state_instance.checkpoint_uuid == test_uuid
        mock_finwiz_flow.assert_called_once_with(state=mock_state_instance)

    def test_should_exit_when_invalid_uuid_provided(self, mocker, mock_flow_state_manager, mock_finwiz_flow):
        """Test error handling for invalid UUID."""
        # Arrange
        test_uuid = "invalid_uuid"
        args = argparse.Namespace(resume_uuid=test_uuid, no_resume=False)
        mock_flow_state_manager.load_flow_state_by_uuid.return_value = None

        # Act & Assert
        with pytest.raises(SystemExit) as exc_info:
            initialize_flow_with_resume(args)

        assert exc_info.value.code == 1
        mock_flow_state_manager.load_flow_state_by_uuid.assert_called_once_with(test_uuid)

    def test_should_start_fresh_when_no_states_found(self, mocker, mock_flow_state_manager, mock_finwiz_flow, mock_finwiz_state):
        """Test starting fresh when no persisted states exist."""
        # Arrange
        args = argparse.Namespace(resume_uuid=None, no_resume=False)
        mock_flow_state_manager.discover_persisted_states.return_value = []

        mock_state_instance = mocker.Mock()
        mock_finwiz_state.return_value = mock_state_instance

        # Act
        result = initialize_flow_with_resume(args)

        # Assert
        mock_flow_state_manager.discover_persisted_states.assert_called_once()
        mock_finwiz_state.assert_called_once()
        mock_finwiz_flow.assert_called_once_with(state=mock_state_instance)

    def test_should_prompt_user_when_states_exist(self, mocker, mock_flow_state_manager, mock_finwiz_flow, mock_finwiz_state):
        """Test interactive prompt when states exist."""
        # Arrange
        args = argparse.Namespace(resume_uuid=None, no_resume=False)

        mock_states = [
            {
                "uuid": "state1",
                "age_hours": 2.5,
                "holdings_processed": 10,
                "total_holdings": 20,
                "progress_pct": 50.0,
                "last_update": datetime.now(),
                "is_stale": False,
            }
        ]
        mock_flow_state_manager.discover_persisted_states.return_value = mock_states
        mock_flow_state_manager.prompt_user_for_resume.return_value = "state1"

        mock_state_data = {
            "holdings_processed": 10,
            "total_holdings": 20,
            "flow_start_time": datetime.now().isoformat(),
        }
        mock_flow_state_manager.load_flow_state_by_uuid.return_value = mock_state_data

        mock_state_instance = mocker.Mock()
        mock_finwiz_state.return_value = mock_state_instance

        # Act
        result = initialize_flow_with_resume(args)

        # Assert
        mock_flow_state_manager.discover_persisted_states.assert_called_once()
        mock_flow_state_manager.prompt_user_for_resume.assert_called_once_with(mock_states)
        mock_flow_state_manager.load_flow_state_by_uuid.assert_called_once_with("state1")
        assert mock_state_instance.resume_from_checkpoint is True
        assert mock_state_instance.checkpoint_uuid == "state1"

    def test_should_start_fresh_when_user_selects_fresh(self, mocker, mock_flow_state_manager, mock_finwiz_flow, mock_finwiz_state):
        """Test starting fresh when user selects 'Start Fresh' option."""
        # Arrange
        args = argparse.Namespace(resume_uuid=None, no_resume=False)

        mock_states = [{"uuid": "state1"}]
        mock_flow_state_manager.discover_persisted_states.return_value = mock_states
        mock_flow_state_manager.prompt_user_for_resume.return_value = None  # User chose fresh

        mock_state_instance = mocker.Mock()
        mock_finwiz_state.return_value = mock_state_instance

        # Act
        result = initialize_flow_with_resume(args)

        # Assert
        mock_flow_state_manager.prompt_user_for_resume.assert_called_once_with(mock_states)
        mock_finwiz_state.assert_called_once()
        mock_finwiz_flow.assert_called_once_with(state=mock_state_instance)

    def test_should_fallback_to_fresh_when_load_fails(self, mocker, mock_flow_state_manager, mock_finwiz_flow, mock_finwiz_state):
        """Test fallback to fresh start when state loading fails."""
        # Arrange
        args = argparse.Namespace(resume_uuid=None, no_resume=False)

        mock_states = [{"uuid": "state1"}]
        mock_flow_state_manager.discover_persisted_states.return_value = mock_states
        mock_flow_state_manager.prompt_user_for_resume.return_value = "state1"
        mock_flow_state_manager.load_flow_state_by_uuid.return_value = None  # Load fails

        mock_state_instance = mocker.Mock()
        mock_finwiz_state.return_value = mock_state_instance

        # Act
        result = initialize_flow_with_resume(args)

        # Assert
        mock_flow_state_manager.load_flow_state_by_uuid.assert_called_once_with("state1")
        mock_finwiz_state.assert_called_once()  # Fresh state created
        mock_finwiz_flow.assert_called_once_with(state=mock_state_instance)

    def test_should_handle_keyboard_interrupt(self, mocker, mock_flow_state_manager):
        """Test handling of KeyboardInterrupt during interactive prompt."""
        # Arrange
        args = argparse.Namespace(resume_uuid=None, no_resume=False)

        mock_states = [{"uuid": "state1"}]
        mock_flow_state_manager.discover_persisted_states.return_value = mock_states
        mock_flow_state_manager.prompt_user_for_resume.side_effect = KeyboardInterrupt()

        # Act & Assert
        with pytest.raises(KeyboardInterrupt):
            initialize_flow_with_resume(args)

    def test_should_exit_when_state_creation_fails_with_uuid(self, mocker, mock_flow_state_manager, mock_finwiz_state):
        """Test error handling when FinwizState creation fails with loaded data."""
        # Arrange
        test_uuid = "abc123def456"
        args = argparse.Namespace(resume_uuid=test_uuid, no_resume=False)

        mock_state_data = {"invalid": "data"}
        mock_flow_state_manager.load_flow_state_by_uuid.return_value = mock_state_data
        mock_finwiz_state.side_effect = Exception("Invalid state data")

        # Act & Assert
        with pytest.raises(SystemExit) as exc_info:
            initialize_flow_with_resume(args)

        assert exc_info.value.code == 1

    def test_should_fallback_when_state_creation_fails_interactive(
        self, mocker, mock_flow_state_manager, mock_finwiz_flow, mock_finwiz_state
    ):
        """Test fallback to fresh when FinwizState creation fails in interactive mode."""
        # Arrange
        args = argparse.Namespace(resume_uuid=None, no_resume=False)

        mock_states = [{"uuid": "state1"}]
        mock_flow_state_manager.discover_persisted_states.return_value = mock_states
        mock_flow_state_manager.prompt_user_for_resume.return_value = "state1"

        mock_state_data = {"invalid": "data"}
        mock_flow_state_manager.load_flow_state_by_uuid.return_value = mock_state_data

        # First call fails, second call succeeds (fresh state)
        mock_state_instance = mocker.Mock()
        mock_finwiz_state.side_effect = [Exception("Invalid state data"), mock_state_instance]

        # Act
        result = initialize_flow_with_resume(args)

        # Assert
        assert mock_finwiz_state.call_count == 2  # Failed once, succeeded with fresh
        mock_finwiz_flow.assert_called_once_with(state=mock_state_instance)
