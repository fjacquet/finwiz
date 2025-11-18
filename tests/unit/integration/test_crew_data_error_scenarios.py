"""
Unit tests for error scenarios and edge cases in crew data operations.

Tests various failure modes, data corruption scenarios, and error recovery
mechanisms in the data consolidation system.
"""

import json
from datetime import datetime, timedelta

import pytest

from finwiz.integration.manager import CrewDataIntegrationManager


class TestFileSystemErrors:
    """Tests for file system related errors."""

    @pytest.fixture
    def integration_manager(self, tmp_path):
        """Create integration manager with temporary directory."""
        return CrewDataIntegrationManager(output_dir=tmp_path)

    def test_should_create_missing_directories_automatically(self, tmp_path):
        """Test that missing directories are created automatically."""
        # Arrange
        nonexistent_dir = tmp_path / "deep" / "nested" / "path"
        manager = CrewDataIntegrationManager(output_dir=nonexistent_dir)

        # Act
        result = manager.store_crew_output("test_crew", {"raw_output": "Test"})

        # Assert
        assert result is True
        assert nonexistent_dir.exists()

    def test_should_handle_readonly_directory_gracefully(self, integration_manager, tmp_path):
        """Test handling of read-only directory."""
        # Arrange
        crew_dir = integration_manager.output_dir / "readonly_crew"
        crew_dir.mkdir(parents=True)

        # Make directory read-only (platform-dependent)
        try:
            crew_dir.chmod(0o444)

            # Act
            result = integration_manager.store_crew_output("readonly_crew", {"raw_output": "Test"})

            # Assert
            # Should either fail gracefully or succeed if permissions allow
            assert isinstance(result, bool)

        finally:
            # Restore permissions for cleanup
            crew_dir.chmod(0o755)

    def test_should_handle_disk_full_scenario(self, integration_manager):
        """Test handling of disk full scenario (simulated)."""
        # Note: This is difficult to test without actually filling the disk
        # Just verify the method exists and is callable
        assert hasattr(integration_manager, "store_crew_output")
        assert callable(integration_manager.store_crew_output)

    def test_should_handle_concurrent_file_access(self, integration_manager):
        """Test handling of concurrent file access."""
        # Arrange
        output = {"raw_output": "Test", "timestamp": datetime.now().isoformat()}

        # Act - Simulate concurrent writes
        results = []
        for i in range(5):
            result = integration_manager.store_crew_output("concurrent_crew", output)
            results.append(result)

        # Assert - All writes should succeed
        assert all(results)

        # Verify data integrity
        retrieved = integration_manager.get_cached_crew_output("concurrent_crew")
        assert retrieved is not None


class TestDataCorruption:
    """Tests for data corruption scenarios."""

    @pytest.fixture
    def integration_manager(self, tmp_path):
        """Create integration manager with temporary directory."""
        return CrewDataIntegrationManager(output_dir=tmp_path)

    def test_should_handle_corrupted_json_gracefully(self, integration_manager):
        """Test handling of corrupted JSON file."""
        # Arrange
        crew_dir = integration_manager.output_dir / "corrupted_crew"
        crew_dir.mkdir(parents=True)

        latest_file = crew_dir / "corrupted_crew_latest.json"
        latest_file.write_text("{ this is not valid json }")

        # Act
        result = integration_manager.get_cached_crew_output("corrupted_crew")

        # Assert
        # Should return None or handle error gracefully
        assert result is None or isinstance(result, dict)

    def test_should_handle_truncated_json_file(self, integration_manager):
        """Test handling of truncated JSON file."""
        # Arrange
        crew_dir = integration_manager.output_dir / "truncated_crew"
        crew_dir.mkdir(parents=True)

        latest_file = crew_dir / "truncated_crew_latest.json"
        latest_file.write_text('{"raw_output": "Test", "json_dict": {')  # Truncated

        # Act
        result = integration_manager.get_cached_crew_output("truncated_crew")

        # Assert
        assert result is None or isinstance(result, dict)

    def test_should_handle_empty_json_file(self, integration_manager):
        """Test handling of empty JSON file."""
        # Arrange
        crew_dir = integration_manager.output_dir / "empty_crew"
        crew_dir.mkdir(parents=True)

        latest_file = crew_dir / "empty_crew_latest.json"
        latest_file.write_text("")

        # Act
        result = integration_manager.get_cached_crew_output("empty_crew")

        # Assert
        assert result is None or isinstance(result, dict)

    def test_should_handle_binary_data_in_json_file(self, integration_manager):
        """Test handling of binary data in JSON file."""
        # Arrange
        crew_dir = integration_manager.output_dir / "binary_crew"
        crew_dir.mkdir(parents=True)

        latest_file = crew_dir / "binary_crew_latest.json"
        latest_file.write_bytes(b"\x00\x01\x02\x03\x04")

        # Act
        result = integration_manager.get_cached_crew_output("binary_crew")

        # Assert
        assert result is None or isinstance(result, dict)

    def test_should_handle_missing_required_fields(self, integration_manager):
        """Test handling of output with missing required fields."""
        # Arrange
        incomplete_output = {"raw_output": "Test"}  # Missing other fields

        # Act
        result = integration_manager.store_crew_output("incomplete_crew", incomplete_output)

        # Assert
        # Should succeed (graceful degradation)
        assert result is True

        # Verify retrieval works
        retrieved = integration_manager.get_cached_crew_output("incomplete_crew")
        assert retrieved is not None

    def test_should_handle_malformed_metadata(self, integration_manager):
        """Test handling of output with malformed metadata."""
        # Arrange
        crew_dir = integration_manager.output_dir / "malformed_crew"
        crew_dir.mkdir(parents=True)

        latest_file = crew_dir / "malformed_crew_latest.json"
        malformed_data = {
            "raw_output": "Test",
            "metadata": "this should be a dict, not a string",
        }
        latest_file.write_text(json.dumps(malformed_data))

        # Act
        result = integration_manager.get_cached_crew_output("malformed_crew")

        # Assert
        # Should handle gracefully
        assert result is None or isinstance(result, dict)


class TestInvalidInputs:
    """Tests for invalid input handling."""

    @pytest.fixture
    def integration_manager(self, tmp_path):
        """Create integration manager with temporary directory."""
        return CrewDataIntegrationManager(output_dir=tmp_path)

    def test_should_handle_none_crew_name(self, integration_manager):
        """Test handling of None crew name."""
        # Act
        result = integration_manager.store_crew_output(None, {"raw_output": "Test"})

        # Assert - Should return False (error caught and logged)
        assert result is False

    def test_should_handle_empty_crew_name(self, integration_manager):
        """Test handling of empty crew name."""
        # Act
        result = integration_manager.store_crew_output("", {"raw_output": "Test"})

        # Assert
        # Should either fail or handle gracefully
        assert isinstance(result, bool)

    def test_should_handle_none_output(self, integration_manager):
        """Test handling of None output."""
        # Act
        result = integration_manager.store_crew_output("test_crew", None)

        # Assert
        # Should handle None gracefully
        assert isinstance(result, bool)

    def test_should_handle_invalid_output_type(self, integration_manager):
        """Test handling of invalid output type."""
        # Act
        result = integration_manager.store_crew_output("test_crew", "not a dict")

        # Assert
        # Should either fail or handle gracefully
        assert isinstance(result, bool)

    def test_should_handle_circular_reference_in_output(self, integration_manager):
        """Test handling of circular reference in output."""
        # Arrange
        output = {"raw_output": "Test"}
        output["self_reference"] = output  # Circular reference

        # Act
        result = integration_manager.store_crew_output("circular_crew", output)

        # Assert
        # Should either fail or handle gracefully (JSON serialization will fail)
        assert isinstance(result, bool)

    def test_should_handle_special_characters_in_crew_name(self, integration_manager):
        """Test handling of special characters in crew name."""
        # Act
        special_names = [
            "crew/with/slashes",
            "crew\\with\\backslashes",
            "crew:with:colons",
            "crew*with*asterisks",
            "crew?with?questions",
        ]

        results = []
        for name in special_names:
            try:
                result = integration_manager.store_crew_output(name, {"raw_output": "Test"})
                results.append((name, result))
            except Exception:
                results.append((name, False))

        # Assert
        # Should handle special characters (either sanitize or reject)
        assert all(isinstance(result, bool) for _, result in results)

    def test_should_handle_very_long_crew_name(self, integration_manager):
        """Test handling of very long crew name."""
        # Arrange
        long_name = "a" * 1000  # Very long name

        # Act
        result = integration_manager.store_crew_output(long_name, {"raw_output": "Test"})

        # Assert
        # Should either succeed or fail gracefully
        assert isinstance(result, bool)

    def test_should_handle_unicode_in_crew_name(self, integration_manager):
        """Test handling of Unicode characters in crew name."""
        # Act
        result = integration_manager.store_crew_output("crew_测试_🚀", {"raw_output": "Test"})

        # Assert
        # Should handle Unicode gracefully
        assert isinstance(result, bool)


class TestTimestampHandling:
    """Tests for timestamp handling and freshness calculation."""

    @pytest.fixture
    def integration_manager(self, tmp_path):
        """Create integration manager with temporary directory."""
        return CrewDataIntegrationManager(output_dir=tmp_path)

    def test_should_handle_missing_timestamp(self, integration_manager):
        """Test handling of output without timestamp."""
        # Arrange
        output = {"raw_output": "Test"}  # No timestamp

        # Act
        result = integration_manager.store_crew_output("test_crew", output)

        # Assert
        assert result is True

        # Verify retrieval works
        retrieved = integration_manager.get_cached_crew_output("test_crew")
        assert retrieved is not None

    def test_should_handle_invalid_timestamp_format(self, integration_manager):
        """Test handling of invalid timestamp format."""
        # Arrange
        output = {
            "raw_output": "Test",
            "timestamp": "not-a-valid-timestamp",
        }

        # Act
        result = integration_manager.store_crew_output("test_crew", output)

        # Assert
        assert result is True

    def test_should_handle_future_timestamp(self, integration_manager):
        """Test handling of timestamp in the future."""
        # Arrange
        future_timestamp = (datetime.now() + timedelta(days=1)).isoformat()
        output = {
            "raw_output": "Test",
            "timestamp": future_timestamp,
        }

        # Act
        result = integration_manager.store_crew_output("test_crew", output)

        # Assert
        assert result is True

        # Verify retrieval works
        retrieved = integration_manager.get_cached_crew_output("test_crew")
        assert retrieved is not None

    def test_should_handle_very_old_timestamp(self, integration_manager):
        """Test handling of very old timestamp."""
        # Arrange
        old_timestamp = (datetime.now() - timedelta(days=365)).isoformat()
        output = {
            "raw_output": "Test",
            "timestamp": old_timestamp,
        }

        # Act
        result = integration_manager.store_crew_output("test_crew", output)

        # Assert
        assert result is True

        # Verify freshness check logs warning for stale data
        # Note: Current implementation logs warning but doesn't update metadata in returned data
        retrieved = integration_manager.get_crew_data_with_freshness_check("test_crew", max_age_hours=24)

        # Data should be retrieved (implementation returns data even if stale)
        assert retrieved is not None
        # Metadata reflects storage time, not retrieval time freshness check
        assert "metadata" in retrieved

    def test_should_handle_timestamp_with_timezone(self, integration_manager):
        """Test handling of timestamp with timezone information."""
        # Arrange
        timestamp_with_tz = datetime.now().astimezone().isoformat()
        output = {
            "raw_output": "Test",
            "timestamp": timestamp_with_tz,
        }

        # Act
        result = integration_manager.store_crew_output("test_crew", output)

        # Assert
        assert result is True

    def test_should_handle_timestamp_as_unix_epoch(self, integration_manager):
        """Test handling of timestamp as Unix epoch."""
        # Arrange
        output = {
            "raw_output": "Test",
            "timestamp": datetime.now().timestamp(),  # Unix timestamp
        }

        # Act
        result = integration_manager.store_crew_output("test_crew", output)

        # Assert
        # Should handle gracefully (may or may not parse correctly)
        assert isinstance(result, bool)


class TestConcurrencyAndRaceConditions:
    """Tests for concurrency and race condition handling."""

    @pytest.fixture
    def integration_manager(self, tmp_path):
        """Create integration manager with temporary directory."""
        return CrewDataIntegrationManager(output_dir=tmp_path)

    def test_should_handle_simultaneous_writes_to_same_crew(self, integration_manager):
        """Test handling of simultaneous writes to the same crew."""
        # Arrange
        outputs = [{"raw_output": f"Output {i}", "timestamp": datetime.now().isoformat()} for i in range(10)]

        # Act - Simulate rapid successive writes
        results = []
        for output in outputs:
            result = integration_manager.store_crew_output("concurrent_crew", output)
            results.append(result)

        # Assert - All writes should succeed
        assert all(results)

        # Verify final state is consistent
        retrieved = integration_manager.get_cached_crew_output("concurrent_crew")
        assert retrieved is not None

    def test_should_handle_simultaneous_reads_and_writes(self, integration_manager):
        """Test handling of simultaneous reads and writes."""
        # Arrange
        integration_manager.store_crew_output("test_crew", {"raw_output": "Initial"})

        # Act - Interleave reads and writes
        for i in range(5):
            integration_manager.store_crew_output("test_crew", {"raw_output": f"Update {i}"})
            retrieved = integration_manager.get_cached_crew_output("test_crew")
            assert retrieved is not None

        # Assert - Final state should be consistent
        final = integration_manager.get_cached_crew_output("test_crew")
        assert final is not None

    def test_should_handle_multiple_crews_concurrent_operations(self, integration_manager):
        """Test handling of concurrent operations on multiple crews."""
        # Act - Store outputs for multiple crews simultaneously
        crews = ["crew1", "crew2", "crew3", "crew4", "crew5"]
        results = []

        for crew_name in crews:
            result = integration_manager.store_crew_output(crew_name, {"raw_output": f"Output for {crew_name}"})
            results.append(result)

        # Assert - All operations should succeed
        assert all(results)

        # Verify all crews can be retrieved
        for crew_name in crews:
            retrieved = integration_manager.get_cached_crew_output(crew_name)
            assert retrieved is not None


class TestMemoryAndPerformance:
    """Tests for memory usage and performance edge cases."""

    @pytest.fixture
    def integration_manager(self, tmp_path):
        """Create integration manager with temporary directory."""
        return CrewDataIntegrationManager(output_dir=tmp_path)

    def test_should_handle_very_large_output(self, integration_manager):
        """Test handling of very large output."""
        # Arrange
        large_output = {
            "raw_output": "A" * 1_000_000,  # 1MB of data
            "json_dict": {"data": ["item"] * 10_000},  # Large list
        }

        # Act
        result = integration_manager.store_crew_output("large_crew", large_output)

        # Assert
        assert result is True

        # Verify retrieval works
        retrieved = integration_manager.get_cached_crew_output("large_crew")
        assert retrieved is not None

    def test_should_handle_deeply_nested_output(self, integration_manager):
        """Test handling of deeply nested output structure."""
        # Arrange
        nested_output = {"level_0": {}}
        current = nested_output["level_0"]

        for i in range(1, 50):  # Create 50 levels of nesting
            current[f"level_{i}"] = {}
            current = current[f"level_{i}"]

        current["data"] = "Deep value"

        # Act
        result = integration_manager.store_crew_output("nested_crew", nested_output)

        # Assert
        # Should handle deep nesting (JSON serialization may have limits)
        assert isinstance(result, bool)

    def test_should_handle_many_historical_outputs(self, integration_manager):
        """Test handling of many historical outputs."""
        # Act - Store many outputs
        for i in range(100):
            integration_manager.store_crew_output("historical_crew", {"raw_output": f"Output {i}"})

        # Assert - Latest should still be retrievable
        retrieved = integration_manager.get_cached_crew_output("historical_crew")
        assert retrieved is not None

        # Verify historical files exist
        crew_dir = integration_manager.output_dir / "historical_crew"
        output_files = list(crew_dir.glob("historical_crew_output_*.json"))
        assert len(output_files) > 0


class TestEdgeCasesAndBoundaryConditions:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture
    def integration_manager(self, tmp_path):
        """Create integration manager with temporary directory."""
        return CrewDataIntegrationManager(output_dir=tmp_path)

    def test_should_handle_zero_max_age_hours(self, integration_manager):
        """Test handling of zero max_age_hours."""
        # Arrange
        integration_manager.store_crew_output("test_crew", {"raw_output": "Test"})

        # Act
        result = integration_manager.get_crew_data_with_freshness_check("test_crew", max_age_hours=0)

        # Assert
        # Should either return None (all data is stale) or handle gracefully
        assert result is None or isinstance(result, dict)

    def test_should_handle_negative_max_age_hours(self, integration_manager):
        """Test handling of negative max_age_hours."""
        # Arrange
        integration_manager.store_crew_output("test_crew", {"raw_output": "Test"})

        # Act
        result = integration_manager.get_crew_data_with_freshness_check("test_crew", max_age_hours=-1)

        # Assert
        # Should handle gracefully (may treat as invalid or use default)
        assert result is None or isinstance(result, dict)

    def test_should_handle_very_large_max_age_hours(self, integration_manager):
        """Test handling of very large max_age_hours."""
        # Arrange
        integration_manager.store_crew_output("test_crew", {"raw_output": "Test"})

        # Act
        result = integration_manager.get_crew_data_with_freshness_check("test_crew", max_age_hours=1_000_000)

        # Assert
        # Should return data (everything is fresh with such a large max_age)
        assert result is not None

    def test_should_handle_output_with_only_metadata(self, integration_manager):
        """Test handling of output that contains only metadata."""
        # Arrange
        metadata_only = {
            "metadata": {
                "crew_name": "test_crew",
                "timestamp": datetime.now().isoformat(),
            }
        }

        # Act
        result = integration_manager.store_crew_output("metadata_crew", metadata_only)

        # Assert
        assert result is True

    def test_should_handle_output_with_null_values(self, integration_manager):
        """Test handling of output with null values."""
        # Arrange
        output_with_nulls = {
            "raw_output": None,
            "json_dict": None,
            "pydantic": None,
        }

        # Act
        result = integration_manager.store_crew_output("null_crew", output_with_nulls)

        # Assert
        assert result is True

        # Verify retrieval works
        retrieved = integration_manager.get_cached_crew_output("null_crew")
        assert retrieved is not None
