#!/usr/bin/env python3
"""
Unit tests for the KnowledgeBaseTool wrapper.

This module tests the fix for the RagTool schema validation issue where
similarity_threshold and limit were incorrectly marked as required.
"""

import pytest
from pydantic import ValidationError

# Skip entire module if qdrant_client has import issues
pytestmark = pytest.mark.skip(reason="qdrant_client import issues - requires dependency update")

from finwiz.tools.rag_tools import KnowledgeBaseTool, get_rag_tools


def test_knowledge_base_tool_schema_validation() -> None:
    """Test that the KnowledgeBaseTool correctly handles optional parameters."""
    tools = get_rag_tools()
    kb_tool = tools[0]

    # Verify it's the correct tool
    assert isinstance(kb_tool, KnowledgeBaseTool)
    assert kb_tool.name == "Knowledge base"

    # Test 1: Schema validation with only required parameter (query)
    schema = kb_tool.args_schema(query="What is Bitcoin?")
    assert schema.query == "What is Bitcoin?"
    assert schema.similarity_threshold is None
    assert schema.limit is None

    # Test 2: Schema validation with query and similarity_threshold
    schema = kb_tool.args_schema(
        query="What is Bitcoin?",
        similarity_threshold=0.75,
    )
    assert schema.query == "What is Bitcoin?"
    assert schema.similarity_threshold == 0.75
    assert schema.limit is None

    # Test 3: Schema validation with all parameters
    schema = kb_tool.args_schema(
        query="What is Bitcoin?",
        similarity_threshold=0.75,
        limit=5,
    )
    assert schema.query == "What is Bitcoin?"
    assert schema.similarity_threshold == 0.75
    assert schema.limit == 5


def test_knowledge_base_tool_schema_fields() -> None:
    """Test that the schema fields are correctly defined."""
    tools = get_rag_tools()
    kb_tool = tools[0]

    schema_fields = kb_tool.args_schema.model_fields

    # Verify all expected fields exist
    assert "query" in schema_fields
    assert "similarity_threshold" in schema_fields
    assert "limit" in schema_fields

    # Verify required/optional status
    assert schema_fields["query"].is_required()
    assert not schema_fields["similarity_threshold"].is_required()
    assert not schema_fields["limit"].is_required()

    # Verify default values
    assert schema_fields["similarity_threshold"].default is None
    assert schema_fields["limit"].default is None


def test_knowledge_base_tool_missing_query_fails() -> None:
    """Test that validation fails when query is missing."""
    tools = get_rag_tools()
    kb_tool = tools[0]

    with pytest.raises(ValidationError) as exc_info:
        kb_tool.args_schema()

    # Verify the error is about the missing query field
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("query",)
    assert errors[0]["type"] == "missing"


def test_get_rag_tools_structure() -> None:
    """Test that get_rag_tools returns the expected tools."""
    tools = get_rag_tools()

    # Should return exactly 2 tools
    assert len(tools) == 2

    # First tool should be KnowledgeBaseTool
    assert isinstance(tools[0], KnowledgeBaseTool)
    assert tools[0].name == "Knowledge base"

    # Second tool should be SaveToRagTool
    assert tools[1].name == "SaveToRag"


def test_get_rag_tools_with_collection_suffix() -> None:
    """Test that collection suffix creates crew-specific collections."""
    tools_default = get_rag_tools()
    tools_custom = get_rag_tools(collection_suffix="test-crew")

    # Both should return the same structure
    assert len(tools_default) == 2
    assert len(tools_custom) == 2

    # Both should have KnowledgeBaseTool as first tool
    assert isinstance(tools_default[0], KnowledgeBaseTool)
    assert isinstance(tools_custom[0], KnowledgeBaseTool)
