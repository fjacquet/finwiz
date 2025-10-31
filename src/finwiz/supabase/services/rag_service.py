"""
Historical Analysis Service for retrieving past analysis results.

Provides historical context from Supabase by:
- Searching for similar historical analyses using vector similarity
- Retrieving full analysis records for context
- Formatting context for AI agent consumption
- Graceful handling when no similar analyses exist

Note: This is NOT related to document RAG tools. This service retrieves
historical ANALYSIS RESULTS (grades, recommendations, scores) from Supabase.
"""

import logging
from typing import Any

from finwiz.supabase.repositories.analysis_repository import AnalysisRepository
from finwiz.supabase.repositories.vector_repository import VectorRepository

logger = logging.getLogger(__name__)


class HistoricalAnalysisService:
    """
    Service for historical analysis context retrieval.

    Combines vector similarity search with analysis retrieval to provide
    historical context for AI agents. Enables agents to ground recommendations
    in past analyses and reduce hallucinations.

    This retrieves ANALYSIS RESULTS (not documents) from Supabase.

    Attributes:
        vector_repo: VectorRepository for similarity search
        analysis_repo: AnalysisRepository for retrieving full analyses

    """

    def __init__(
        self,
        vector_repo: VectorRepository,
        analysis_repo: AnalysisRepository,
    ) -> None:
        """
        Initialize Historical Analysis Service.

        Args:
            vector_repo: VectorRepository instance for similarity search
            analysis_repo: AnalysisRepository instance for analysis retrieval

        """
        self.vector_repo = vector_repo
        self.analysis_repo = analysis_repo

        logger.info("HistoricalAnalysisService initialized")

    async def get_context(
        self,
        query: str,
        limit: int = 3,
        similarity_threshold: float = 0.7,
    ) -> list[dict[str, Any]] | None:
        """
        Get historical context for query.

        Performs vector similarity search to find relevant historical analyses,
        then retrieves full analysis records and formats them for AI agent
        consumption.

        Args:
            query: Query text to search for similar analyses
            limit: Maximum number of similar analyses to return (default: 3)
            similarity_threshold: Minimum similarity score 0-1 (default: 0.7)

        Returns:
            List of context dictionaries with analysis details, or None if no
            similar analyses found. Each dict contains:
            - ticker: Asset ticker symbol
            - asset_class: Asset class (stock, etf, crypto)
            - grade: Letter grade (A+ to F)
            - recommendation: BUY/HOLD/SELL
            - composite_score: Composite score 0-1
            - similarity: Similarity score 0-1
            - summary: Analysis summary (if available in export_json)
            - created_at: Analysis timestamp

        """
        # Validate inputs
        if not query or not query.strip():
            logger.warning("Empty query provided for RAG context retrieval")
            return None

        if limit < 1:
            logger.warning(f"Invalid limit: {limit}, using default 3")
            limit = 3

        if not 0.0 <= similarity_threshold <= 1.0:
            logger.warning(f"Invalid similarity threshold: {similarity_threshold}, using default 0.7")
            similarity_threshold = 0.7

        logger.debug(f"Retrieving historical analysis context for query (length: {len(query)}, limit: {limit}, threshold: {similarity_threshold})")

        try:
            # Step 1: Search for similar analyses using vector similarity
            similar_analyses = await self.vector_repo.search_similar(
                query=query,
                limit=limit,
                similarity_threshold=similarity_threshold,
            )

            if not similar_analyses:
                logger.info("No similar analyses found for historical context")
                return None

            logger.debug(f"Found {len(similar_analyses)} similar analyses, retrieving full records...")

            # Step 2: Retrieve full analysis records
            context = []
            for analysis_id, similarity in similar_analyses:
                try:
                    # Get full analysis record
                    analysis = await self.analysis_repo.get_by_id(analysis_id)

                    if analysis:
                        # Extract summary from export_json if available
                        summary = ""
                        if isinstance(analysis.export_json, dict):
                            # Try common summary field names
                            summary = analysis.export_json.get("summary") or analysis.export_json.get("executive_summary") or analysis.export_json.get("key_findings") or ""

                        # Format context entry
                        context_entry = {
                            "ticker": analysis.ticker,
                            "asset_class": analysis.asset_class,
                            "grade": analysis.grade,
                            "recommendation": analysis.recommendation,
                            "composite_score": analysis.composite_score,
                            "similarity": similarity,
                            "summary": summary,
                            "created_at": analysis.created_at.isoformat(),
                        }

                        context.append(context_entry)
                        logger.debug(f"Added context: {analysis.ticker} (grade: {analysis.grade}, similarity: {similarity:.2f})")

                    else:
                        logger.warning(f"Analysis not found for ID: {analysis_id}")

                except Exception as e:
                    logger.error(f"Failed to retrieve analysis {analysis_id}: {e}")
                    # Continue with other analyses

            if not context:
                logger.warning("No valid analyses retrieved for historical context")
                return None

            logger.info(f"Retrieved {len(context)} analyses for historical context")
            return context

        except Exception as e:
            logger.error(f"Historical context retrieval failed: {e}")
            return None

    def format_context_for_agent(
        self,
        context: list[dict[str, Any]] | None,
        query: str = "",
    ) -> str:
        """
        Format historical analysis context for AI agent consumption.

        Converts context list into a formatted string suitable for inclusion
        in agent task descriptions or prompts.

        Args:
            context: List of context dictionaries from get_context()
            query: Original query (optional, for context)

        Returns:
            Formatted context string for agent, or empty string if no context

        """
        if not context:
            return ""

        # Build formatted context string
        lines = []

        if query:
            lines.append(f"Historical Context for: {query}")
            lines.append("")

        lines.append("Similar Past Analyses:")
        lines.append("")

        for i, entry in enumerate(context, 1):
            ticker = entry.get("ticker", "Unknown")
            asset_class = entry.get("asset_class", "unknown")
            grade = entry.get("grade", "N/A")
            recommendation = entry.get("recommendation", "N/A")
            similarity = entry.get("similarity", 0.0)
            summary = entry.get("summary", "No summary available")

            lines.append(f"{i}. {ticker} ({asset_class.upper()})")
            lines.append(f"   Grade: {grade} | Recommendation: {recommendation}")
            lines.append(f"   Similarity: {similarity:.2%}")

            if summary:
                # Truncate long summaries
                max_summary_length = 200
                if len(summary) > max_summary_length:
                    summary = summary[:max_summary_length] + "..."
                lines.append(f"   Summary: {summary}")

            lines.append("")

        return "\n".join(lines)

    async def get_context_for_ticker(
        self,
        ticker: str,
        asset_class: str,
        limit: int = 3,
    ) -> list[dict[str, Any]] | None:
        """
        Get historical context for a specific ticker.

        Convenience method that constructs a query from ticker and asset class,
        then retrieves similar analyses.

        Args:
            ticker: Asset ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            limit: Maximum number of similar analyses to return (default: 3)

        Returns:
            List of context dictionaries, or None if no similar analyses found

        """
        # Construct query from ticker and asset class
        query = f"Analysis of {ticker} {asset_class}"

        logger.debug(f"Getting historical analysis context for ticker: {ticker} ({asset_class})")

        return await self.get_context(
            query=query,
            limit=limit,
            similarity_threshold=0.7,
        )
