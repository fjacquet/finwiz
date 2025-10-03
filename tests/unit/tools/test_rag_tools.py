#!/usr/bin/env python3
"""
Test script for RAG tools integration in FinWiz.

This script demonstrates how the RAG tools can be used to store and retrieve
financial knowledge across different crews.
"""

import pytest
from crewai_tools import RagTool
from pydantic import ValidationError

from finwiz.rag_config import DEFAULT_RAG_CONFIG
from finwiz.tools.rag_tools import KnowledgeBaseTool, get_rag_tools
from finwiz.tools.save_to_rag_tool import SaveToRagTool


def test_knowledge_base_tool_schema() -> None:
    """Test that KnowledgeBaseTool has correct schema with optional parameters."""
    tools = get_rag_tools()
    kb_tool = tools[0]

    # Verify tool name
    assert kb_tool.name == "Knowledge base"

    # Verify schema fields
    schema_fields = kb_tool.args_schema.model_fields
    assert "query" in schema_fields
    assert "similarity_threshold" in schema_fields
    assert "limit" in schema_fields

    # Verify query is required
    assert schema_fields["query"].is_required()

    # Verify similarity_threshold and limit are optional
    assert not schema_fields["similarity_threshold"].is_required()
    assert not schema_fields["limit"].is_required()

    # Test schema validation with only query (should work)
    try:
        kb_tool.args_schema(query="test query")
    except ValidationError:
        pytest.fail("Schema validation should pass with only query parameter")

    # Test schema validation with all parameters (should work)
    try:
        kb_tool.args_schema(query="test query", similarity_threshold=0.7, limit=10)
    except ValidationError:
        pytest.fail("Schema validation should pass with all parameters")


def test_get_rag_tools_returns_correct_tools() -> None:
    """Test that get_rag_tools returns the correct tools."""
    tools = get_rag_tools()

    assert len(tools) == 2
    assert isinstance(tools[0], KnowledgeBaseTool)
    assert isinstance(tools[1], SaveToRagTool)
    assert tools[0].name == "Knowledge base"
    assert tools[1].name == "SaveToRag"


def test_get_rag_tools_with_collection_suffix() -> None:
    """Test that get_rag_tools creates crew-specific collections."""
    tools = get_rag_tools(collection_suffix="test-crew")

    # Both tools should be created
    assert len(tools) == 2
    assert isinstance(tools[0], KnowledgeBaseTool)
    assert isinstance(tools[1], SaveToRagTool)


@pytest.mark.integration
def test_rag_integration() -> None:
    """Test the RAG tools integration."""
    print("Testing RAG tools integration in FinWiz...")

    # Create RAG tools for different crews
    crypto_config = DEFAULT_RAG_CONFIG.copy()
    crypto_config["vectordb"]["config"] = crypto_config["vectordb"]["config"].copy()
    crypto_config["vectordb"]["config"]["collection_name"] = "finwiz-crypto"

    etf_config = DEFAULT_RAG_CONFIG.copy()
    etf_config["vectordb"]["config"] = etf_config["vectordb"]["config"].copy()
    etf_config["vectordb"]["config"]["collection_name"] = "finwiz-etf"

    # Initialize RAG tools
    crypto_rag = RagTool(config=crypto_config, summarize=True)
    etf_rag = RagTool(config=etf_config, summarize=True)

    # Initialize SaveToRag tools
    crypto_save_tool = SaveToRagTool(rag_tool=crypto_rag)
    etf_save_tool = SaveToRagTool(rag_tool=etf_rag)

    # Store some information in the crypto knowledge base
    print("\n1. Storing information in the crypto knowledge base...")
    crypto_info = """
    Bitcoin (BTC) is showing strong technical indicators with a potential breakout 
    above the $75,000 resistance level. The 50-day moving average has crossed above 
    the 200-day moving average, forming a golden cross pattern. Trading volume has 
    increased by 35% in the past week, suggesting accumulation by institutional investors.
    On-chain metrics indicate a decrease in exchange balances, which historically 
    precedes price appreciation due to reduced selling pressure.
    """
    result = crypto_save_tool._run(crypto_info)
    print(f"Result: {result}")

    # Store some information in the ETF knowledge base
    print("\n2. Storing information in the ETF knowledge base...")
    etf_info = """
    The ARK Innovation ETF (ARKK) has shown significant volatility in recent months,
    with a beta of 1.8 relative to the S&P 500. Its top holdings include Tesla (10.2%),
    Roku (8.5%), and Square (6.3%), all of which are high-growth technology companies
    with above-average volatility metrics. The expense ratio is 0.75%, which is higher
    than the category average of 0.53%. Despite recent underperformance, the 5-year
    return remains competitive at 15.3% annualized.
    """
    result = etf_save_tool._run(etf_info)
    print(f"Result: {result}")

    # Retrieve information from the crypto knowledge base
    print("\n3. Retrieving information from the crypto knowledge base...")
    query = "What are the technical indicators for Bitcoin?"
    response = crypto_rag.run(query)
    print(f"Response: {response}")

    # Retrieve information from the ETF knowledge base
    print("\n4. Retrieving information from the ETF knowledge base...")
    query = "What is the expense ratio of ARKK and how does it compare to the category average?"
    response = etf_rag.run(query)
    print(f"Response: {response}")

    # Test cross-collection retrieval (should not retrieve ETF info when querying crypto)
    print("\n5. Testing isolation between collections...")
    query = "Tell me about ARKK ETF"
    response = crypto_rag.run(query)
    print(f"Response when querying crypto collection about ETFs: {response}")

    print("\nRAG tools integration test completed!")


if __name__ == "__main__":
    test_rag_integration()
