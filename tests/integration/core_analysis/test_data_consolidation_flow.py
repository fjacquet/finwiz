"""
Integration tests for data consolidation flow.

Tests that verify crew outputs are properly stored, retrieved, and consolidated
for use in portfolio analysis and report generation.
"""

from datetime import datetime

import pytest

from finwiz.integration.manager import CrewDataIntegrationManager


class TestDataConsolidationFlow:
    """Test cases for data consolidation flow from crew execution to report."""

    @pytest.fixture
    def integration_manager(self, tmp_path):
        """Create integration manager with temporary output directory."""
        return CrewDataIntegrationManager(output_dir=tmp_path)

    @pytest.fixture
    def sample_crew_outputs(self):
        """Create sample crew outputs for testing."""
        return {
            "stock": {
                "raw_output": "Stock analysis for AAPL",
                "json_dict": {
                    "ticker": "AAPL",
                    "recommendation": "BUY",
                    "risk_score": 6,
                    "price_target": 165.0,
                },
                "pydantic": {
                    "ticker": "AAPL",
                    "analysis": "Strong fundamentals with P/E of 25.5",
                    "recommendation": "BUY",
                    "risk_score": 6,
                    "confidence": 0.85,
                },
                "timestamp": datetime.now().isoformat(),
            },
            "etf": {
                "raw_output": "ETF analysis for SPY",
                "json_dict": {
                    "ticker": "SPY",
                    "recommendation": "BUY",
                    "risk_score": 4,
                    "expense_ratio": 0.0945,
                },
                "pydantic": {
                    "ticker": "SPY",
                    "analysis": "Broad market exposure with low expense ratio",
                    "recommendation": "BUY",
                    "risk_score": 4,
                    "confidence": 0.90,
                },
                "timestamp": datetime.now().isoformat(),
            },
            "crypto": {
                "raw_output": "Crypto analysis for BTC",
                "json_dict": {
                    "ticker": "BTC",
                    "recommendation": "HOLD",
                    "risk_score": 8,
                    "price_target": 55000.0,
                },
                "pydantic": {
                    "ticker": "BTC",
                    "analysis": "Digital gold narrative with institutional support",
                    "recommendation": "HOLD",
                    "risk_score": 8,
                    "confidence": 0.75,
                },
                "timestamp": datetime.now().isoformat(),
            },
        }

    def test_should_store_crew_outputs_correctly(self, integration_manager, sample_crew_outputs):
        """Test that integration_manager.store_crew_output() stores crew outputs correctly."""
        # Act - Store all crew outputs
        storage_results = {}
        for crew_name, output in sample_crew_outputs.items():
            result = integration_manager.store_crew_output(crew_name, output)
            storage_results[crew_name] = result

        # Assert - All storage operations should succeed
        assert all(storage_results.values()), "All crew outputs should be stored successfully"

        # Verify files were created
        for crew_name in sample_crew_outputs.keys():
            crew_dir = integration_manager.output_dir / crew_name
            assert crew_dir.exists(), f"Directory for {crew_name} should exist"

            # Check for output files
            output_files = list(crew_dir.glob(f"{crew_name}_output_*.json"))
            assert len(output_files) > 0, f"Output file for {crew_name} should exist"

            # Check for latest symlink/file
            latest_file = crew_dir / f"{crew_name}_latest.json"
            assert latest_file.exists(), f"Latest file for {crew_name} should exist"

    def test_should_retrieve_stored_crew_outputs(self, integration_manager, sample_crew_outputs):
        """Test that stored crew outputs can be retrieved successfully."""
        # Arrange - Store crew outputs
        for crew_name, output in sample_crew_outputs.items():
            integration_manager.store_crew_output(crew_name, output)

        # Act - Retrieve stored outputs
        retrieved_outputs = {}
        for crew_name in sample_crew_outputs.keys():
            retrieved = integration_manager.get_cached_crew_output(crew_name)
            retrieved_outputs[crew_name] = retrieved

        # Assert - All outputs should be retrieved
        assert all(v is not None for v in retrieved_outputs.values()), "All crew outputs should be retrievable"

        # Verify content matches
        for crew_name, expected_output in sample_crew_outputs.items():
            retrieved = retrieved_outputs[crew_name]
            assert retrieved is not None, f"Retrieved output for {crew_name} should not be None"

            # Check that key fields are present
            assert "raw_output" in retrieved, f"raw_output should be in {crew_name} output"
            assert "json_dict" in retrieved, f"json_dict should be in {crew_name} output"
            assert "pydantic" in retrieved, f"pydantic should be in {crew_name} output"
            assert "metadata" in retrieved, f"metadata should be in {crew_name} output"

            # Verify metadata
            metadata = retrieved["metadata"]
            assert metadata["crew_name"] == crew_name, "Crew name should match in metadata"
            assert "storage_timestamp" in metadata, "Storage timestamp should be present"
            assert "data_freshness" in metadata, "Data freshness info should be present"

    def test_should_retrieve_crew_data_with_freshness_check(self, integration_manager, sample_crew_outputs):
        """Test that get_crew_data_with_freshness_check() returns non-None data."""
        # Arrange - Store crew outputs
        for crew_name, output in sample_crew_outputs.items():
            integration_manager.store_crew_output(crew_name, output)

        # Act - Retrieve with freshness check
        retrieved_data = {}
        for crew_name in sample_crew_outputs.keys():
            data = integration_manager.get_crew_data_with_freshness_check(crew_name, max_age_hours=24)
            retrieved_data[crew_name] = data

        # Assert - All data should be retrieved
        assert all(v is not None for v in retrieved_data.values()), "All crew data should be retrievable with freshness check"

        # Verify data is fresh (stored just now)
        for crew_name, data in retrieved_data.items():
            assert data is not None, f"Data for {crew_name} should not be None"
            assert "metadata" in data, f"Metadata should be present in {crew_name} data"

            # Check freshness info
            freshness = data["metadata"]["data_freshness"]
            assert freshness["is_fresh"] is True, f"Data for {crew_name} should be marked as fresh"
            assert freshness["age_hours"] == 0.0, "Age should be 0 for just-stored data"

    def test_should_handle_missing_crew_data_gracefully(self, integration_manager):
        """Test that retrieval of non-existent crew data returns None."""
        # Act - Try to retrieve non-existent crew data
        result = integration_manager.get_crew_data_with_freshness_check("nonexistent_crew")

        # Assert - Should return None, not raise exception
        assert result is None, "Non-existent crew data should return None"

    def test_should_consolidate_data_from_multiple_crews(self, integration_manager, sample_crew_outputs):
        """Test that data from multiple crews can be consolidated."""
        # Arrange - Store all crew outputs
        for crew_name, output in sample_crew_outputs.items():
            integration_manager.store_crew_output(crew_name, output)

        # Act - Retrieve all crew data
        consolidated_data = {}
        for crew_name in ["stock", "etf", "crypto"]:
            crew_data = integration_manager.get_crew_data_with_freshness_check(crew_name)
            if crew_data:
                consolidated_data[crew_name] = crew_data

        # Assert - All crews should be in consolidated data
        assert len(consolidated_data) == 3, "Should have data from all 3 crews"
        assert "stock" in consolidated_data, "Stock data should be in consolidated data"
        assert "etf" in consolidated_data, "ETF data should be in consolidated data"
        assert "crypto" in consolidated_data, "Crypto data should be in consolidated data"

        # Verify each crew's data is complete
        for crew_name, crew_data in consolidated_data.items():
            assert crew_data is not None, f"Data for {crew_name} should not be None"
            assert "raw_output" in crew_data, f"raw_output should be in {crew_name} data"
            assert "json_dict" in crew_data, f"json_dict should be in {crew_name} data"
            assert "pydantic" in crew_data, f"pydantic should be in {crew_name} data"

    def test_should_not_show_core_analysis_missing_warnings_when_data_exists(
        self, integration_manager, sample_crew_outputs, caplog
    ):
        """Test that no 'Core analysis data missing' warnings appear when crews execute successfully."""
        # Arrange - Store all crew outputs
        for crew_name, output in sample_crew_outputs.items():
            integration_manager.store_crew_output(crew_name, output)

        # Act - Retrieve data with freshness check (this would trigger warnings if data was missing)
        for crew_name in ["stock", "etf", "crypto"]:
            data = integration_manager.get_crew_data_with_freshness_check(crew_name, warn_on_stale=True)
            assert data is not None, f"Data for {crew_name} should be available"

        # Assert - No warnings about missing core analysis data
        warning_messages = [record.message for record in caplog.records if record.levelname == "WARNING"]

        # Filter for core analysis missing warnings
        core_analysis_warnings = [msg for msg in warning_messages if "core analysis" in msg.lower() and "missing" in msg.lower()]

        assert len(core_analysis_warnings) == 0, "Should not have 'core analysis missing' warnings when data exists"

    def test_should_verify_data_flow_from_storage_to_consolidation(self, integration_manager, sample_crew_outputs):
        """Test the complete data flow: crew execution → storage → consolidation → report."""
        # Step 1: Crew Execution (simulated) → Storage
        storage_success = {}
        for crew_name, output in sample_crew_outputs.items():
            result = integration_manager.store_crew_output(crew_name, output)
            storage_success[crew_name] = result

        assert all(storage_success.values()), "All crew outputs should be stored successfully"

        # Step 2: Storage → Retrieval
        retrieved_data = {}
        for crew_name in sample_crew_outputs.keys():
            data = integration_manager.get_cached_crew_output(crew_name)
            retrieved_data[crew_name] = data

        assert all(v is not None for v in retrieved_data.values()), "All stored data should be retrievable"

        # Step 3: Retrieval → Consolidation
        consolidated_data = {}
        for crew_name in ["stock", "etf", "crypto"]:
            crew_data = integration_manager.get_crew_data_with_freshness_check(crew_name)
            if crew_data:
                # Extract relevant fields for consolidation
                consolidated_data[crew_name] = {
                    "recommendation": crew_data.get("json_dict", {}).get("recommendation"),
                    "risk_score": crew_data.get("json_dict", {}).get("risk_score"),
                    "analysis": crew_data.get("pydantic", {}).get("analysis"),
                    "confidence": crew_data.get("pydantic", {}).get("confidence"),
                }

        # Step 4: Verify consolidated data is ready for report
        assert len(consolidated_data) == 3, "Consolidated data should have all 3 crews"

        # Verify each crew has required fields for reporting
        for crew_name, crew_data in consolidated_data.items():
            assert crew_data["recommendation"] is not None, f"{crew_name} should have recommendation"
            assert crew_data["risk_score"] is not None, f"{crew_name} should have risk_score"
            assert crew_data["analysis"] is not None, f"{crew_name} should have analysis"
            assert crew_data["confidence"] is not None, f"{crew_name} should have confidence"

    def test_should_handle_partial_crew_execution(self, integration_manager, sample_crew_outputs):
        """Test that system handles partial crew execution (some crews succeed, others fail)."""
        # Arrange - Store only stock and ETF outputs (crypto fails)
        integration_manager.store_crew_output("stock", sample_crew_outputs["stock"])
        integration_manager.store_crew_output("etf", sample_crew_outputs["etf"])
        # Crypto crew not executed (simulating failure)

        # Act - Try to consolidate data
        consolidated_data = {}
        for crew_name in ["stock", "etf", "crypto"]:
            crew_data = integration_manager.get_crew_data_with_freshness_check(crew_name)
            if crew_data:
                consolidated_data[crew_name] = crew_data

        # Assert - Should have data from successful crews only
        assert len(consolidated_data) == 2, "Should have data from 2 successful crews"
        assert "stock" in consolidated_data, "Stock data should be available"
        assert "etf" in consolidated_data, "ETF data should be available"
        assert "crypto" not in consolidated_data, "Crypto data should not be available"

        # Verify system continues with partial data
        assert consolidated_data["stock"] is not None, "Stock data should be usable"
        assert consolidated_data["etf"] is not None, "ETF data should be usable"

    def test_should_preserve_metadata_through_consolidation(self, integration_manager, sample_crew_outputs):
        """Test that metadata is preserved through the consolidation process."""
        # Arrange - Store crew outputs
        for crew_name, output in sample_crew_outputs.items():
            integration_manager.store_crew_output(crew_name, output)

        # Act - Retrieve and check metadata
        for crew_name in sample_crew_outputs.keys():
            crew_data = integration_manager.get_cached_crew_output(crew_name)

            # Assert - Metadata should be present and complete
            assert "metadata" in crew_data, f"Metadata should be present for {crew_name}"

            metadata = crew_data["metadata"]
            assert "crew_name" in metadata, "Crew name should be in metadata"
            assert "storage_timestamp" in metadata, "Storage timestamp should be in metadata"
            assert "integration_version" in metadata, "Integration version should be in metadata"
            assert "data_freshness" in metadata, "Data freshness should be in metadata"

            # Verify crew name matches
            assert metadata["crew_name"] == crew_name, f"Crew name in metadata should match {crew_name}"

            # Verify freshness info
            freshness = metadata["data_freshness"]
            assert "stored_at" in freshness, "Stored_at should be in freshness info"
            assert "is_fresh" in freshness, "is_fresh should be in freshness info"
            assert "age_hours" in freshness, "age_hours should be in freshness info"

    def test_should_support_concurrent_crew_storage(self, integration_manager, sample_crew_outputs):
        """Test that multiple crews can store outputs concurrently without conflicts."""
        # Act - Store all outputs (simulating concurrent execution)
        storage_results = []
        for crew_name, output in sample_crew_outputs.items():
            result = integration_manager.store_crew_output(crew_name, output)
            storage_results.append((crew_name, result))

        # Assert - All storage operations should succeed
        assert all(result for _, result in storage_results), "All concurrent storage operations should succeed"

        # Verify no data corruption
        for crew_name in sample_crew_outputs.keys():
            crew_data = integration_manager.get_cached_crew_output(crew_name)
            assert crew_data is not None, f"Data for {crew_name} should not be corrupted"
            assert crew_data["metadata"]["crew_name"] == crew_name, f"Crew name should match for {crew_name}"

    def test_should_verify_upstream_data_collection(self, integration_manager, sample_crew_outputs):
        """Test that upstream data collection works correctly."""
        # Arrange - Store crew outputs
        for crew_name, output in sample_crew_outputs.items():
            integration_manager.store_crew_output(crew_name, output)

        # Act - Get upstream data for a hypothetical downstream crew
        upstream_data = integration_manager.get_upstream_data("report", max_age_hours=24)

        # Assert - Upstream data should include all stored crews
        assert upstream_data is not None, "Upstream data should not be None"
        assert hasattr(upstream_data, "available_data"), "Should have available_data attribute"
        assert hasattr(upstream_data, "missing_data"), "Should have missing_data attribute"
        assert hasattr(upstream_data, "stale_data"), "Should have stale_data attribute"

        # Verify available data includes our crews
        available_crews = list(upstream_data.available_data.keys())
        assert "stock" in available_crews, "Stock should be in available data"
        assert "etf" in available_crews, "ETF should be in available data"
        assert "crypto" in available_crews, "Crypto should be in available data"

        # Verify no stale data (just stored)
        assert len(upstream_data.stale_data) == 0, "Should have no stale data for fresh outputs"
