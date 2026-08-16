"""Unit tests for DataParser.load_and_parse_json's dict-shape handling."""

import json

from finwiz.orchestrators.extraction.parsers import DataParser


class TestLoadAndParseJsonOpportunitiesKey:
    """NewcomerDiscoveryPipeline's writer emits {"opportunities": [...]}, not
    {"candidates": [...]} or {"a_plus_candidates": [...]}. The parser must
    accept all three shapes.
    """

    def test_reads_candidates_from_opportunities_key(self, tmp_path):
        # Arrange
        payload = {"opportunities": [{"ticker": "NVDA", "grade": "A+"}], "analysis_summary": "found one"}
        json_file = tmp_path / "a_plus_stocks.json"
        json_file.write_text(json.dumps(payload))

        # Act
        candidates = DataParser().load_and_parse_json(json_file, "stock")

        # Assert
        assert candidates == [{"ticker": "NVDA", "grade": "A+"}]

    def test_still_reads_candidates_from_candidates_key(self, tmp_path):
        # Arrange
        payload = {"candidates": [{"symbol": "NVDA", "grade": "A+"}]}
        json_file = tmp_path / "a_plus_stocks.json"
        json_file.write_text(json.dumps(payload))

        # Act
        candidates = DataParser().load_and_parse_json(json_file, "stock")

        # Assert
        assert candidates == [{"symbol": "NVDA", "grade": "A+"}]

    def test_still_reads_candidates_from_a_plus_candidates_key(self, tmp_path):
        # Arrange
        payload = {"a_plus_candidates": [{"candidate": {"symbol": "NVDA"}, "composite_score": 0.9}]}
        json_file = tmp_path / "a_plus_stocks.json"
        json_file.write_text(json.dumps(payload))

        # Act
        candidates = DataParser().load_and_parse_json(json_file, "stock")

        # Assert
        # Nested "candidate" wrapper is unwrapped and merged with sibling fields.
        assert candidates == [{"symbol": "NVDA", "composite_score": 0.9}]

    def test_returns_empty_list_when_none_of_the_known_keys_are_present(self, tmp_path):
        # Arrange
        payload = {"unrelated_key": [{"symbol": "NVDA"}]}
        json_file = tmp_path / "a_plus_stocks.json"
        json_file.write_text(json.dumps(payload))

        # Act
        candidates = DataParser().load_and_parse_json(json_file, "stock")

        # Assert
        assert candidates == []
