"""
Unit tests for CheckpointManager.

Tests checkpoint saving, loading, and resumption functionality.
"""

import json

import pytest

from finwiz.sessions.checkpoint_manager import CheckpointManager, get_checkpoint_manager


class TestCheckpointManager:
    """Test suite for CheckpointManager."""

    @pytest.fixture
    def checkpoint_manager(self, tmp_path):
        """Create a CheckpointManager with temporary directory."""
        return CheckpointManager(
            session_id="test_session",
            checkpoint_dir=tmp_path / "checkpoints",
        )

    def test_should_initialize_with_session_id(self, tmp_path):
        """Test CheckpointManager initializes correctly."""
        # Act
        manager = CheckpointManager("test_session", tmp_path / "checkpoints")

        # Assert
        assert manager.session_id == "test_session"
        assert manager.checkpoint_dir.exists()

    def test_should_create_checkpoint_directory(self, tmp_path):
        """Test checkpoint directory is created on init."""
        # Arrange
        checkpoint_dir = tmp_path / "new_checkpoints"

        # Act
        CheckpointManager("test", checkpoint_dir)

        # Assert
        assert checkpoint_dir.exists()

    def test_should_save_phase_checkpoint(self, checkpoint_manager):
        """Test saving a phase checkpoint."""
        # Arrange
        phase_data = {"completed_tickers": ["AAPL", "GOOGL"], "results": {}}

        # Act
        checkpoint_file = checkpoint_manager.save_phase("deep_analysis", phase_data)

        # Assert
        assert checkpoint_file.exists()
        with open(checkpoint_file) as f:
            saved = json.load(f)
        assert saved["phase"] == "deep_analysis"
        assert saved["session_id"] == "test_session"
        assert saved["data"] == phase_data

    def test_should_load_phase_checkpoint(self, checkpoint_manager):
        """Test loading a phase checkpoint."""
        # Arrange
        phase_data = {"completed_tickers": ["AAPL"], "results": {"AAPL": {"grade": "A"}}}
        checkpoint_manager.save_phase("deep_analysis", phase_data)

        # Act
        loaded = checkpoint_manager.load_phase("deep_analysis")

        # Assert
        assert loaded == phase_data

    def test_should_return_none_for_missing_phase(self, checkpoint_manager):
        """Test loading non-existent phase returns None."""
        # Act
        loaded = checkpoint_manager.load_phase("nonexistent")

        # Assert
        assert loaded is None

    def test_should_get_completed_tickers(self, checkpoint_manager):
        """Test getting completed tickers for a phase."""
        # Arrange
        phase_data = {"completed_tickers": ["AAPL", "GOOGL", "MSFT"], "results": {}}
        checkpoint_manager.save_phase("deep_analysis", phase_data)

        # Act
        completed = checkpoint_manager.get_completed_tickers("deep_analysis")

        # Assert
        assert completed == {"AAPL", "GOOGL", "MSFT"}

    def test_should_return_empty_set_for_no_completed_tickers(self, checkpoint_manager):
        """Test getting completed tickers when phase doesn't exist."""
        # Act
        completed = checkpoint_manager.get_completed_tickers("nonexistent")

        # Assert
        assert completed == set()

    def test_should_save_ticker_result(self, checkpoint_manager):
        """Test saving a single ticker result."""
        # Act
        checkpoint_manager.save_ticker_result("AAPL", {"grade": "A", "score": 0.85})
        checkpoint_manager.save_ticker_result("GOOGL", {"grade": "A+", "score": 0.92})

        # Assert
        completed = checkpoint_manager.get_completed_tickers()
        assert "AAPL" in completed
        assert "GOOGL" in completed

        results = checkpoint_manager.get_results()
        assert results["AAPL"]["grade"] == "A"
        assert results["GOOGL"]["grade"] == "A+"

    def test_should_preserve_existing_results_on_save(self, checkpoint_manager):
        """Test that saving new ticker preserves existing results."""
        # Arrange
        checkpoint_manager.save_ticker_result("AAPL", {"grade": "A"})

        # Act
        checkpoint_manager.save_ticker_result("GOOGL", {"grade": "A+"})

        # Assert
        results = checkpoint_manager.get_results()
        assert "AAPL" in results
        assert "GOOGL" in results

    def test_should_clear_phase(self, checkpoint_manager):
        """Test clearing a phase checkpoint."""
        # Arrange
        checkpoint_manager.save_phase("deep_analysis", {"data": "test"})
        assert checkpoint_manager.load_phase("deep_analysis") is not None

        # Act
        cleared = checkpoint_manager.clear_phase("deep_analysis")

        # Assert
        assert cleared is True
        assert checkpoint_manager.load_phase("deep_analysis") is None

    def test_should_return_false_for_clearing_nonexistent_phase(self, checkpoint_manager):
        """Test clearing non-existent phase returns False."""
        # Act
        cleared = checkpoint_manager.clear_phase("nonexistent")

        # Assert
        assert cleared is False

    def test_should_clear_all_checkpoints(self, checkpoint_manager):
        """Test clearing all checkpoints."""
        # Arrange
        checkpoint_manager.save_phase("phase1", {"data": "1"})
        checkpoint_manager.save_phase("phase2", {"data": "2"})
        checkpoint_manager.save_phase("phase3", {"data": "3"})

        # Act
        count = checkpoint_manager.clear_all()

        # Assert
        assert count == 3
        assert checkpoint_manager.load_phase("phase1") is None
        assert checkpoint_manager.load_phase("phase2") is None
        assert checkpoint_manager.load_phase("phase3") is None

    def test_should_get_resumption_info(self, checkpoint_manager):
        """Test getting resumption info."""
        # Arrange
        checkpoint_manager.save_phase(
            "deep_analysis",
            {"completed_tickers": ["AAPL", "GOOGL"], "results": {}},
        )
        checkpoint_manager.save_phase(
            "discovery",
            {"completed_tickers": ["MSFT"], "results": {}},
        )

        # Act
        info = checkpoint_manager.get_resumption_info()

        # Assert
        assert info["session_id"] == "test_session"
        assert "deep_analysis" in info["phases"]
        assert "discovery" in info["phases"]
        assert info["phases"]["deep_analysis"]["completed_count"] == 2
        assert info["phases"]["discovery"]["completed_count"] == 1

    def test_should_handle_corrupted_checkpoint(self, checkpoint_manager):
        """Test handling of corrupted checkpoint file."""
        # Arrange - Create corrupted checkpoint
        checkpoint_file = checkpoint_manager.checkpoint_dir / "corrupted.json"
        checkpoint_file.write_text("not valid json {{{")

        # Act
        loaded = checkpoint_manager.load_phase("corrupted")

        # Assert
        assert loaded is None

    def test_get_checkpoint_manager_factory(self, tmp_path, mocker):
        """Test get_checkpoint_manager factory function."""
        # Act
        manager = get_checkpoint_manager("factory_test")

        # Assert
        assert isinstance(manager, CheckpointManager)
        assert manager.session_id == "factory_test"


class TestCheckpointManagerIntegration:
    """Integration tests for checkpoint resumption scenarios."""

    @pytest.fixture
    def checkpoint_manager(self, tmp_path):
        """Create a CheckpointManager with temporary directory."""
        return CheckpointManager("integration_test", tmp_path / "checkpoints")

    def test_resume_deep_analysis_workflow(self, checkpoint_manager):
        """Test resuming deep analysis after partial completion."""
        # Arrange - Simulate partial completion
        tickers_to_analyze = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]
        checkpoint_manager.save_ticker_result("AAPL", {"grade": "A", "score": 0.85})
        checkpoint_manager.save_ticker_result("GOOGL", {"grade": "A+", "score": 0.92})

        # Act - Get remaining tickers
        completed = checkpoint_manager.get_completed_tickers()
        remaining = [t for t in tickers_to_analyze if t not in completed]

        # Assert
        assert len(completed) == 2
        assert len(remaining) == 3
        assert "MSFT" in remaining
        assert "AMZN" in remaining
        assert "META" in remaining

    def test_continue_after_simulated_crash(self, checkpoint_manager):
        """Test continuing work after simulated crash."""
        # Arrange - Simulate work before crash
        checkpoint_manager.save_ticker_result("AAPL", {"grade": "A"})
        checkpoint_manager.save_ticker_result("GOOGL", {"grade": "A+"})

        # Simulate crash - create new manager instance
        new_manager = CheckpointManager(
            "integration_test",
            checkpoint_manager.checkpoint_dir,
        )

        # Act - Load previous state
        completed = new_manager.get_completed_tickers()
        results = new_manager.get_results()

        # Assert - Previous work is preserved
        assert completed == {"AAPL", "GOOGL"}
        assert results["AAPL"]["grade"] == "A"
        assert results["GOOGL"]["grade"] == "A+"
