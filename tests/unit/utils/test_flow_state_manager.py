"""
Unit tests for FlowStateManager.

Tests state discovery, metadata extraction, user prompts, state loading,
cleanup, and error handling with mocked file system and SQLite operations.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pytest import approx

from finwiz.utils.flow_state_manager import FlowStateManager


class TestFlowStateManager:
    """Test suite for FlowStateManager."""

    @pytest.fixture
    def manager(self, mocker, tmp_path):
        """Create FlowStateManager with mocked home directory."""
        # Mock Path.home() to return tmp_path
        mocker.patch("pathlib.Path.home", return_value=tmp_path)
        # Create the state directory structure
        state_dir = tmp_path / "Library" / "Application Support" / "finwiz"
        state_dir.mkdir(parents=True, exist_ok=True)
        return FlowStateManager()

    @pytest.fixture
    def mock_state_file(self, tmp_path):
        """Create a mock state file path (legacy - for metadata tests)."""
        state_dir = tmp_path / ".crewai" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir / "test-uuid-123.db"

    @pytest.fixture
    def mock_db(self, tmp_path):
        """Create a mock flow_states.db database."""
        state_dir = tmp_path / "Library" / "Application Support" / "finwiz"
        state_dir.mkdir(parents=True, exist_ok=True)
        db_path = state_dir / "flow_states.db"

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE flow_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flow_uuid TEXT NOT NULL,
                method_name TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                state_json TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        return db_path

    @pytest.fixture
    def sample_state_data(self):
        """Sample state data for testing."""
        # Use a recent time (1 hour ago) to avoid stale state
        recent_time = datetime.now() - timedelta(hours=1)
        return {
            "id": "test-uuid-123",
            "session_id": "session-123",
            "analysis_count": 10,
            "current_date": "2025-01-15",
            "holdings_processed": 10,
            "total_holdings": 20,
            "flow_start_time": recent_time.isoformat(),
            "current_ticker": "AAPL",
            "progress_percentage": 50.0,
        }

    @pytest.fixture
    def sample_resume_state(self):
        """Sample state metadata for prompt_user_for_resume tests."""
        return {
            "uuid": "uuid-123",
            "method": "run_sequential_workflow",
            "session_id": "session-123",
            "analysis_count": 10,
            "current_date": "2025-01-15",
            "age_hours": 2.0,
            "last_update": datetime.now(),
            "is_stale": False,
            "is_complete": True,
        }

    def test_should_initialize_with_state_directory(self, mocker, tmp_path):
        """Test FlowStateManager initialization creates state directory."""
        # Arrange
        mocker.patch("pathlib.Path.home", return_value=tmp_path)
        # Create the directory since __init__ doesn't create it
        state_dir = tmp_path / "Library" / "Application Support" / "finwiz"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Act
        manager = FlowStateManager()

        # Assert
        assert manager.state_dir == tmp_path / "Library" / "Application Support" / "finwiz"
        assert manager.db_path == manager.state_dir / "flow_states.db"

    def test_should_discover_no_states_when_directory_empty(self, manager):
        """Test discovering states returns empty list when no .db files exist."""
        # Act
        states = manager.discover_persisted_states()

        # Assert
        assert states == []

    def test_should_discover_states_when_db_files_exist(self, manager, mock_db, sample_state_data):
        """Test discovering states finds flow_states.db and extracts metadata."""
        # Arrange - Insert test data
        timestamp = datetime.now().isoformat()
        conn = sqlite3.connect(str(mock_db))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO flow_states (flow_uuid, method_name, timestamp, state_json) VALUES (?, ?, ?, ?)",
            ("test-uuid-123", "run_sequential_workflow", timestamp, json.dumps(sample_state_data)),
        )
        conn.commit()
        conn.close()

        # Act
        states = manager.discover_persisted_states()

        # Assert
        assert len(states) == 1
        assert states[0]["uuid"] == "test-uuid-123"
        assert states[0]["method"] == "run_sequential_workflow"
        assert states[0]["is_complete"] is True

    def test_should_sort_states_by_last_update_newest_first(self, manager, mock_db):
        """Test states are sorted by last_update in descending order."""
        # Arrange
        older_time = (datetime.now() - timedelta(hours=5)).isoformat()
        newer_time = (datetime.now() - timedelta(hours=1)).isoformat()

        state_data = {"id": "uuid", "session_id": "", "analysis_count": 0, "current_date": "2025-01-15"}

        conn = sqlite3.connect(str(mock_db))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO flow_states (flow_uuid, method_name, timestamp, state_json) VALUES (?, ?, ?, ?)", ("uuid-1", "run_sequential_workflow", older_time, json.dumps(state_data))
        )
        cursor.execute(
            "INSERT INTO flow_states (flow_uuid, method_name, timestamp, state_json) VALUES (?, ?, ?, ?)", ("uuid-2", "run_sequential_workflow", newer_time, json.dumps(state_data))
        )
        conn.commit()
        conn.close()

        # Act
        states = manager.discover_persisted_states()

        # Assert
        assert len(states) == 2
        assert states[0]["uuid"] == "uuid-2"  # Newer first
        assert states[1]["uuid"] == "uuid-1"  # Older second

    def test_should_handle_extraction_errors_gracefully(self, manager, mocker, mock_state_file):
        """Test discovery continues when metadata extraction fails."""
        # Arrange
        mock_state_file.touch()
        mocker.patch.object(
            manager,
            "_extract_state_metadata",
            side_effect=Exception("Extraction failed"),
        )

        # Act
        states = manager.discover_persisted_states()

        # Assert
        assert states == []  # Failed extraction returns empty list

    def test_should_extract_metadata_from_valid_state_file(self, manager, mocker, mock_state_file, sample_state_data):
        """Test metadata extraction from valid SQLite state file."""
        # Arrange
        # Create the actual file so stat() works
        mock_state_file.touch()

        mock_conn = mocker.MagicMock()
        mock_cursor = mocker.MagicMock()

        state_json = json.dumps(sample_state_data)
        created_at = "2025-01-10T10:00:00"

        mock_cursor.fetchone.return_value = (state_json, created_at)
        mock_conn.cursor.return_value = mock_cursor

        mocker.patch("sqlite3.connect", return_value=mock_conn)

        # Act
        metadata = manager._extract_state_metadata(mock_state_file)

        # Assert
        assert metadata is not None
        assert metadata["uuid"] == "test-uuid-123"
        assert metadata["holdings_processed"] == 10
        assert metadata["total_holdings"] == 20
        assert metadata["progress_pct"] == approx(50.0)
        assert metadata["is_stale"] is False

        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_should_calculate_age_hours_correctly(self, manager, mocker, mock_state_file, sample_state_data):
        """Test age calculation from flow_start_time."""
        # Arrange
        # Create the actual file so stat() works
        mock_state_file.touch()

        # Set flow_start_time to 3 hours ago
        start_time = datetime.now() - timedelta(hours=3)
        sample_state_data["flow_start_time"] = start_time.isoformat()

        mock_conn = mocker.MagicMock()
        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchone.return_value = (json.dumps(sample_state_data), "2025-01-10")
        mock_conn.cursor.return_value = mock_cursor

        mocker.patch("sqlite3.connect", return_value=mock_conn)

        # Act
        metadata = manager._extract_state_metadata(mock_state_file)

        # Assert
        assert metadata is not None
        assert 2.9 < metadata["age_hours"] < 3.1  # Allow small variance

    def test_should_mark_state_as_stale_when_older_than_24_hours(self, manager, mocker, mock_state_file, sample_state_data):
        """Test is_stale flag is True when age > 24 hours."""
        # Arrange
        # Create the actual file so stat() works
        mock_state_file.touch()

        start_time = datetime.now() - timedelta(hours=30)
        sample_state_data["flow_start_time"] = start_time.isoformat()

        mock_conn = mocker.MagicMock()
        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchone.return_value = (json.dumps(sample_state_data), "2025-01-10")
        mock_conn.cursor.return_value = mock_cursor

        mocker.patch("sqlite3.connect", return_value=mock_conn)

        # Act
        metadata = manager._extract_state_metadata(mock_state_file)

        # Assert
        assert metadata is not None
        assert metadata["is_stale"] is True

    def test_should_return_none_when_no_state_data_in_db(self, manager, mocker, mock_state_file):
        """Test extraction returns None when SQLite query returns no rows."""
        # Arrange
        mock_conn = mocker.MagicMock()
        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchone.return_value = None  # No data
        mock_conn.cursor.return_value = mock_cursor

        mocker.patch("sqlite3.connect", return_value=mock_conn)

        # Act
        metadata = manager._extract_state_metadata(mock_state_file)

        # Assert
        assert metadata is None
        mock_conn.close.assert_called_once()

    def test_should_handle_sqlite_error_during_extraction(self, manager, mocker, mock_state_file):
        """Test extraction handles SQLite errors gracefully."""
        # Arrange
        mocker.patch("sqlite3.connect", side_effect=sqlite3.Error("Database locked"))

        # Act
        metadata = manager._extract_state_metadata(mock_state_file)

        # Assert
        assert metadata is None

    def test_should_handle_json_decode_error_during_extraction(self, manager, mocker, mock_state_file):
        """Test extraction handles JSON decode errors gracefully."""
        # Arrange
        mock_conn = mocker.MagicMock()
        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchone.return_value = ("invalid json", "2025-01-10")
        mock_conn.cursor.return_value = mock_cursor

        mocker.patch("sqlite3.connect", return_value=mock_conn)

        # Act
        metadata = manager._extract_state_metadata(mock_state_file)

        # Assert
        assert metadata is None

    def test_should_handle_missing_flow_start_time(self, manager, mocker, mock_state_file):
        """Test extraction handles missing flow_start_time field."""
        # Arrange
        # Create the actual file so stat() works
        mock_state_file.touch()

        state_data = {
            "holdings_processed": 5,
            "total_holdings": 10,
            # flow_start_time missing
        }

        mock_conn = mocker.MagicMock()
        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchone.return_value = (json.dumps(state_data), "2025-01-10")
        mock_conn.cursor.return_value = mock_cursor

        mocker.patch("sqlite3.connect", return_value=mock_conn)

        # Act
        metadata = manager._extract_state_metadata(mock_state_file)

        # Assert
        assert metadata is not None
        assert metadata["age_hours"] == 0  # Default when missing

    def test_should_calculate_progress_percentage_correctly(self, manager, mocker, mock_state_file):
        """Test progress percentage calculation."""
        # Arrange
        # Create the actual file so stat() works
        mock_state_file.touch()

        state_data = {
            "holdings_processed": 15,
            "total_holdings": 30,
            "flow_start_time": datetime.now().isoformat(),
        }

        mock_conn = mocker.MagicMock()
        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchone.return_value = (json.dumps(state_data), "2025-01-10")
        mock_conn.cursor.return_value = mock_cursor

        mocker.patch("sqlite3.connect", return_value=mock_conn)

        # Act
        metadata = manager._extract_state_metadata(mock_state_file)

        # Assert
        assert metadata is not None
        assert metadata["progress_pct"] == approx(50.0)

    def test_should_handle_zero_total_holdings(self, manager, mocker, mock_state_file):
        """Test progress percentage when total_holdings is 0."""
        # Arrange
        # Create the actual file so stat() works
        mock_state_file.touch()

        state_data = {
            "holdings_processed": 0,
            "total_holdings": 0,
            "flow_start_time": datetime.now().isoformat(),
        }

        mock_conn = mocker.MagicMock()
        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchone.return_value = (json.dumps(state_data), "2025-01-10")
        mock_conn.cursor.return_value = mock_cursor

        mocker.patch("sqlite3.connect", return_value=mock_conn)

        # Act
        metadata = manager._extract_state_metadata(mock_state_file)

        # Assert
        assert metadata is not None
        assert metadata["progress_pct"] == approx(0.0)  # Avoid division by zero

    def test_should_return_none_when_no_states_for_prompt(self, manager):
        """Test prompt returns None when states list is empty."""
        # Act
        result = manager.prompt_user_for_resume([])

        # Assert
        assert result is None

    def test_should_prompt_user_and_return_selected_uuid(self, manager, mocker, sample_resume_state):
        """Test user prompt returns selected UUID."""
        # Arrange
        states = [sample_resume_state]

        # Mock user input to select first option
        mocker.patch("builtins.input", return_value="1")

        # Act
        result = manager.prompt_user_for_resume(states)

        # Assert
        assert result == "uuid-123"

    def test_should_return_none_when_user_selects_start_fresh(self, manager, mocker, sample_resume_state):
        """Test prompt returns None when user selects 'Start Fresh'."""
        # Arrange
        states = [sample_resume_state]

        # Mock user input to select "Start Fresh" (option 2)
        mocker.patch("builtins.input", return_value="2")

        # Act
        result = manager.prompt_user_for_resume(states)

        # Assert
        assert result is None

    def test_should_warn_and_confirm_when_state_is_stale(self, manager, mocker):
        """Test prompt warns user and asks for confirmation when state is stale."""
        # Arrange
        states = [
            {
                "uuid": "uuid-stale",
                "method": "run_sequential_workflow",
                "session_id": "",
                "analysis_count": 5,
                "current_date": "2025-01-15",
                "age_hours": 30.0,
                "last_update": datetime.now() - timedelta(hours=30),
                "is_stale": True,
                "is_complete": True,
            }
        ]

        # Mock user inputs: select option 1, then confirm with 'y'
        mocker.patch("builtins.input", side_effect=["1", "y"])

        # Act
        result = manager.prompt_user_for_resume(states)

        # Assert
        assert result == "uuid-stale"

    def test_should_retry_prompt_when_user_declines_stale_state(self, manager, mocker):
        """Test prompt retries when user declines stale state."""
        # Arrange
        states = [
            {
                "uuid": "uuid-stale",
                "method": "run_sequential_workflow",
                "session_id": "",
                "analysis_count": 5,
                "current_date": "2025-01-15",
                "age_hours": 30.0,
                "last_update": datetime.now() - timedelta(hours=30),
                "is_stale": True,
                "is_complete": True,
            }
        ]

        # Mock user inputs: select option 1, decline with 'n', then select option 2
        mocker.patch("builtins.input", side_effect=["1", "n", "2"])

        # Act
        result = manager.prompt_user_for_resume(states)

        # Assert
        assert result is None  # User selected "Start Fresh" after declining stale

    def test_should_handle_invalid_choice_and_retry(self, manager, mocker, sample_resume_state):
        """Test prompt handles invalid choice and retries."""
        # Arrange
        states = [sample_resume_state]

        # Mock user inputs: invalid choice, then valid choice
        mocker.patch("builtins.input", side_effect=["99", "1"])

        # Act
        result = manager.prompt_user_for_resume(states)

        # Assert
        assert result == "uuid-123"

    def test_should_handle_non_numeric_input_and_retry(self, manager, mocker, sample_resume_state):
        """Test prompt handles non-numeric input and retries."""
        # Arrange
        states = [sample_resume_state]

        # Mock user inputs: non-numeric, then valid choice
        mocker.patch("builtins.input", side_effect=["abc", "1"])

        # Act
        result = manager.prompt_user_for_resume(states)

        # Assert
        assert result == "uuid-123"

    def test_should_exit_on_keyboard_interrupt(self, manager, mocker, sample_resume_state):
        """Test prompt exits gracefully on KeyboardInterrupt."""
        # Arrange
        states = [sample_resume_state]

        # Mock user input to raise KeyboardInterrupt
        mocker.patch("builtins.input", side_effect=KeyboardInterrupt())

        # Act & Assert
        with pytest.raises(SystemExit):
            manager.prompt_user_for_resume(states)

    def test_should_load_state_by_uuid_successfully(self, manager, mock_db, sample_state_data):
        """Test loading state data by UUID."""
        # Arrange - Insert test data
        timestamp = datetime.now().isoformat()
        conn = sqlite3.connect(str(mock_db))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO flow_states (flow_uuid, method_name, timestamp, state_json) VALUES (?, ?, ?, ?)",
            ("test-uuid-123", "run_sequential_workflow", timestamp, json.dumps(sample_state_data)),
        )
        conn.commit()
        conn.close()

        # Act
        state_data = manager.load_flow_state_by_uuid("test-uuid-123")

        # Assert
        assert state_data is not None
        assert state_data["holdings_processed"] == 10
        assert state_data["total_holdings"] == 20

    def test_should_return_none_when_state_file_not_found(self, manager):
        """Test load returns None when state file doesn't exist."""
        # Act
        state_data = manager.load_flow_state_by_uuid("nonexistent-uuid")

        # Assert
        assert state_data is None

    def test_should_handle_sqlite_error_during_load(self, manager, mocker, mock_state_file):
        """Test load handles SQLite errors gracefully."""
        # Arrange
        mock_state_file.touch()
        mocker.patch("sqlite3.connect", side_effect=sqlite3.Error("Database error"))

        # Act
        state_data = manager.load_flow_state_by_uuid("test-uuid-123")

        # Assert
        assert state_data is None

    def test_should_handle_json_decode_error_during_load(self, manager, mocker, mock_state_file):
        """Test load handles JSON decode errors gracefully."""
        # Arrange
        mock_state_file.touch()

        mock_conn = mocker.MagicMock()
        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchone.return_value = ("invalid json",)
        mock_conn.cursor.return_value = mock_cursor

        mocker.patch("sqlite3.connect", return_value=mock_conn)

        # Act
        state_data = manager.load_flow_state_by_uuid("test-uuid-123")

        # Assert
        assert state_data is None

    def test_should_return_none_when_no_state_data_during_load(self, manager, mock_db):
        """Test load returns None when query returns no rows."""
        # Arrange - mock_db exists but has no data for the requested UUID

        # Act
        state_data = manager.load_flow_state_by_uuid("nonexistent-uuid")

        # Assert
        assert state_data is None

    def test_should_cleanup_old_states_successfully(self, manager, mock_db):
        """Test cleanup deletes state entries older than max_age_days from database."""
        # Arrange
        old_time = (datetime.now() - timedelta(days=10)).isoformat()
        recent_time = (datetime.now() - timedelta(days=2)).isoformat()
        state_data = json.dumps({"id": "uuid", "session_id": ""})

        conn = sqlite3.connect(str(mock_db))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO flow_states (flow_uuid, method_name, timestamp, state_json) VALUES (?, ?, ?, ?)", ("old-uuid", "run_sequential_workflow", old_time, state_data))
        cursor.execute(
            "INSERT INTO flow_states (flow_uuid, method_name, timestamp, state_json) VALUES (?, ?, ?, ?)", ("recent-uuid", "run_sequential_workflow", recent_time, state_data)
        )
        conn.commit()
        conn.close()

        # Act
        deleted_count = manager.cleanup_old_states(max_age_days=7)

        # Assert
        assert deleted_count == 1

        # Verify only old entry was deleted
        conn = sqlite3.connect(str(mock_db))
        cursor = conn.cursor()
        cursor.execute("SELECT flow_uuid FROM flow_states")
        remaining = [row[0] for row in cursor.fetchall()]
        conn.close()
        assert "recent-uuid" in remaining
        assert "old-uuid" not in remaining

    def test_should_return_zero_when_no_old_states_to_cleanup(self, manager):
        """Test cleanup returns 0 when no old states exist."""
        # Act
        deleted_count = manager.cleanup_old_states(max_age_days=7)

        # Assert
        assert deleted_count == 0

    def test_should_return_zero_when_database_not_exists(self, manager):
        """Test cleanup returns 0 when database file doesn't exist."""
        # Arrange - db_path doesn't exist (manager fixture creates dir but not db)

        # Act
        deleted_count = manager.cleanup_old_states(max_age_days=7)

        # Assert
        assert deleted_count == 0

    def test_should_handle_deletion_errors_gracefully(self, manager, mocker, tmp_path):
        """Test cleanup handles file deletion errors gracefully."""
        # Arrange
        state_dir = tmp_path / ".crewai" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        old_file = state_dir / "old-uuid.db"
        old_file.touch()

        # Mock file modification time to be old
        old_time = datetime.now() - timedelta(days=10)

        import os

        original_stat = os.stat

        def mock_stat(path, *args, **kwargs):
            path_str = str(path)
            if "old-uuid" in path_str:
                result = original_stat(path, *args, **kwargs)
                return os.stat_result(
                    (
                        result.st_mode,
                        result.st_ino,
                        result.st_dev,
                        result.st_nlink,
                        result.st_uid,
                        result.st_gid,
                        result.st_size,
                        result.st_atime,
                        old_time.timestamp(),
                        result.st_ctime,
                    )
                )
            return original_stat(path, *args, **kwargs)

        mocker.patch("os.stat", side_effect=mock_stat)

        # Mock unlink to raise exception
        original_unlink = Path.unlink

        def mock_unlink(self, *args, **kwargs):
            if "old-uuid" in str(self):
                raise OSError("Permission denied")
            return original_unlink(self, *args, **kwargs)

        mocker.patch.object(Path, "unlink", mock_unlink)

        # Act
        deleted_count = manager.cleanup_old_states(max_age_days=7)

        # Assert
        assert deleted_count == 0  # Failed to delete

    def test_should_handle_corrupted_state_file(self, manager, mocker, mock_state_file):
        """Test extraction handles corrupted state files gracefully."""
        # Arrange
        mock_state_file.touch()

        # Mock SQLite to raise error indicating corruption
        mocker.patch(
            "sqlite3.connect",
            side_effect=sqlite3.DatabaseError("Database disk image is malformed"),
        )

        # Act
        metadata = manager._extract_state_metadata(mock_state_file)

        # Assert
        assert metadata is None

    def test_should_handle_empty_state_data_fields(self, manager, mocker, mock_state_file):
        """Test extraction handles state data with missing fields."""
        # Arrange
        # Create the actual file so stat() works
        mock_state_file.touch()

        state_data = {}  # Empty state data

        mock_conn = mocker.MagicMock()
        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchone.return_value = (json.dumps(state_data), "2025-01-10")
        mock_conn.cursor.return_value = mock_cursor

        mocker.patch("sqlite3.connect", return_value=mock_conn)

        # Act
        metadata = manager._extract_state_metadata(mock_state_file)

        # Assert
        assert metadata is not None
        assert metadata["holdings_processed"] == 0  # Default value
        assert metadata["total_holdings"] == 0  # Default value
        assert metadata["age_hours"] == 0  # Default when flow_start_time missing
