"""
Unit tests for memory management functionality.

Tests memory monitoring, cache cleanup, and constraint validation.
"""

from finwiz.utils.memory_manager import MemoryManager, get_memory_manager


class TestMemoryManager:
    """Test suite for MemoryManager."""

    def test_should_initialize_memory_manager(self):
        """Test that memory manager initializes correctly."""
        manager = MemoryManager(session_id="test-session")

        assert manager.session_id == "test-session"
        assert manager.initial_memory > 0
        assert manager.peak_memory == manager.initial_memory
        assert len(manager.memory_samples) == 0

    def test_should_monitor_memory_at_stage(self):
        """Test memory monitoring at a specific stage."""
        manager = MemoryManager(session_id="test-session")

        sample = manager.monitor_memory("test-stage")

        assert sample["stage"] == "test-stage"
        assert sample["memory_mb"] > 0
        assert sample["memory_bytes"] > 0
        assert sample["delta_mb"] >= 0
        assert sample["peak_mb"] > 0
        assert "within_limit" in sample
        assert len(manager.memory_samples) == 1

    def test_should_track_peak_memory(self):
        """Test that peak memory is tracked correctly."""
        manager = MemoryManager(session_id="test-session")

        sample1 = manager.monitor_memory("stage-1")
        sample2 = manager.monitor_memory("stage-2")

        # Peak should be at least as high as any sample
        assert manager.peak_memory >= sample1["memory_bytes"]
        assert manager.peak_memory >= sample2["memory_bytes"]

    def test_should_cleanup_cache_when_exists(self, tmp_path):
        """Test cache cleanup when cache directory exists."""
        # Create a test cache directory with files
        cache_dir = tmp_path / "cache" / "batch_data" / "test-session"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Create some test files
        (cache_dir / "test1.json").write_text('{"test": 1}')
        (cache_dir / "test2.json").write_text('{"test": 2}')

        # Create manager with custom cache dir
        manager = MemoryManager(session_id="test-session")
        manager.cache_dir = cache_dir

        # Clean up
        result = manager.cleanup_cache()

        assert result["success"]
        assert result["files_removed"] == 2
        assert result["disk_freed_mb"] >= 0  # May be 0 for very small files
        assert not cache_dir.exists()

    def test_should_handle_cleanup_when_cache_not_exists(self):
        """Test cache cleanup when cache directory doesn't exist."""
        manager = MemoryManager(session_id="nonexistent-session")

        result = manager.cleanup_cache()

        assert result["success"]
        assert result["files_removed"] == 0
        assert result["disk_freed_mb"] == 0.0

    def test_should_get_memory_metrics(self):
        """Test getting comprehensive memory metrics."""
        manager = MemoryManager(session_id="test-session")

        # Monitor at multiple stages
        manager.monitor_memory("stage-1")
        manager.monitor_memory("stage-2")
        manager.monitor_memory("stage-3")

        metrics = manager.get_memory_metrics()

        assert "initial_memory_mb" in metrics
        assert "peak_memory_mb" in metrics
        assert "final_memory_mb" in metrics
        assert "memory_increase_mb" in metrics
        assert "max_memory_limit_mb" in metrics
        assert "within_limit" in metrics
        assert "peak_usage_percent" in metrics
        assert "samples" in metrics
        assert "sample_count" in metrics

        assert metrics["sample_count"] == 3
        assert len(metrics["samples"]) == 3
        assert metrics["max_memory_limit_mb"] == 1024

    def test_should_validate_memory_constraints_when_within_limit(self):
        """Test memory constraint validation when within limit."""
        manager = MemoryManager(session_id="test-session")

        # Monitor memory (should be well within 500 MB limit)
        manager.monitor_memory("test-stage")

        # Validate constraints
        is_valid = manager.validate_memory_constraints()

        assert is_valid

    def test_should_format_bytes_correctly(self):
        """Test byte formatting utility."""
        manager = MemoryManager(session_id="test-session")

        assert "B" in manager._format_bytes(1024)
        assert "KB" in manager._format_bytes(1024)
        assert "MB" in manager._format_bytes(1024 * 1024)
        assert "GB" in manager._format_bytes(1024 * 1024 * 1024)

    def test_should_create_manager_via_factory(self):
        """Test creating memory manager via factory function."""
        manager = get_memory_manager(session_id="test-session")

        assert isinstance(manager, MemoryManager)
        assert manager.session_id == "test-session"

    def test_should_accumulate_memory_samples(self):
        """Test that memory samples accumulate correctly."""
        manager = MemoryManager(session_id="test-session")

        # Monitor at multiple stages
        for i in range(5):
            manager.monitor_memory(f"stage-{i}")

        assert len(manager.memory_samples) == 5

        # Verify all samples have required fields
        for sample in manager.memory_samples:
            assert "stage" in sample
            assert "memory_mb" in sample
            assert "delta_mb" in sample
            assert "peak_mb" in sample
            assert "within_limit" in sample
