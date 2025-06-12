"""
RAG tools for knowledge retrieval and storage across FinWiz crews.

This module provides tools for Retrieval Augmented Generation (RAG)
to enable crews to store and retrieve knowledge across sessions.
"""

from typing import List, Optional, Dict, Any

from crewai_tools import RagTool
from crewai.tools import BaseTool as Tool
from finwiz.rag_config import DEFAULT_RAG_CONFIG
from finwiz.tools.save_to_rag_tool import SaveToRagTool


def get_rag_tools(collection_suffix: Optional[str] = None) -> List[Tool]:
    """
    Get RAG tools for knowledge retrieval and storage.

    Args:
        collection_suffix: Optional suffix to create crew-specific collections.
            For example, "stock" would create a "finwiz-stock" collection.

    Returns:
        List of RAG tools for knowledge retrieval and storage.
    """
    # Create a copy of the default config
    config = DEFAULT_RAG_CONFIG.copy()
    
    # If a collection suffix is provided, create a crew-specific collection
    if collection_suffix:
        config["vectordb"]["config"] = config["vectordb"]["config"].copy()
        config["vectordb"]["config"]["collection_name"] = f"finwiz-{collection_suffix}"
    
    # Create the RAG tool for retrieval
    rag_tool = RagTool(
        config=config,
        summarize=True,
        description=(
            "Use this tool to retrieve information from the FinWiz knowledge base. "
            "Ask questions about financial data, market trends, or previously "
            "researched information."
        ),
    )
    
    # Create the SaveToRag tool for storage
    save_to_rag_tool = SaveToRagTool(rag_tool=rag_tool)
    
    return [rag_tool, save_to_rag_tool]
