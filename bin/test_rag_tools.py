#!/usr/bin/env python3
"""
Test script for RAG tools integration in FinWiz.

This script demonstrates how the RAG tools can be used to store and retrieve
financial knowledge across different crews.
"""

import os
from crewai_tools import RagTool
from finwiz.rag_config import DEFAULT_RAG_CONFIG
from finwiz.tools.save_to_rag_tool import SaveToRagTool

def test_rag_integration():
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
