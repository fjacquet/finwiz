"""
RAG tools for knowledge retrieval and storage across FinWiz crews.

This module provides tools for Retrieval Augmented Generation (RAG)
to enable crews to store and retrieve knowledge across sessions.
"""

from typing import Any

from crewai.tools import BaseTool as Tool
from crewai_tools import RagTool
from pydantic import BaseModel

from finwiz.rag_config import DEFAULT_RAG_CONFIG

# Import schema from centralized location
from finwiz.schemas.tools import KnowledgeBaseInput
from finwiz.tools.save_to_rag_tool import SaveToRagTool


class KnowledgeBaseTool(Tool):
    """
    Wrapper around RagTool that fixes the schema validation issue.

    The crewai_tools.RagTool has a bug where similarity_threshold and limit
    are marked as required in the schema even though they have default values.
    This wrapper provides the correct schema with optional parameters.
    """

    name: str = "Knowledge base"
    description: str = (
        "Use this tool to retrieve information from the FinWiz knowledge base. Ask questions about financial data, market trends, or previously researched information."
    )
    args_schema: type[BaseModel] = KnowledgeBaseInput
    _rag_tool: Any = None

    def __init__(self, rag_tool: RagTool) -> None:
        """Initialize with an underlying RagTool instance."""
        super().__init__()
        self._rag_tool = rag_tool

    def _run(
        self,
        query: str,
        similarity_threshold: float | None = None,
        limit: int | None = None,
    ) -> str:
        """Execute the RAG query with optional parameters."""
        result: str = self._rag_tool._run(
            query=query,
            similarity_threshold=similarity_threshold,
            limit=limit,
        )
        return result


def get_rag_tools(collection_suffix: str | None = None) -> list[Tool]:
    """
    Get RAG tools for knowledge retrieval and storage.

    Args:
        collection_suffix: Optional suffix to create crew-specific collections.
            For example, "stock" would create a "finwiz-stock" collection.

    Returns:
        List of RAG tools for knowledge retrieval and storage.

    """
    # Create a copy of the default config
    config: dict[str, Any] = DEFAULT_RAG_CONFIG.copy()

    # If a collection suffix is provided, create a crew-specific collection
    if collection_suffix:
        config["vectordb"]["config"] = config["vectordb"]["config"].copy()
        config["vectordb"]["config"]["collection_name"] = f"finwiz-{collection_suffix}"

    # Create the underlying RAG tool for retrieval
    underlying_rag_tool = RagTool(
        config=config,
        summarize=True,
    )

    # Wrap it with our custom tool that has the correct schema
    knowledge_base_tool = KnowledgeBaseTool(rag_tool=underlying_rag_tool)

    # Create the SaveToRag tool for storage
    save_to_rag_tool = SaveToRagTool(rag_tool=underlying_rag_tool)

    return [knowledge_base_tool, save_to_rag_tool]
