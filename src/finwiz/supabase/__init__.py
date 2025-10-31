"""
Supabase integration for FinWiz.

Provides centralized data persistence and vector storage with:
- Analysis caching and retrieval
- Portfolio snapshot tracking
- Vector embeddings for semantic search
- RAG-enhanced AI agents
- Circuit breaker protection
- Async background operations
"""

from finwiz.supabase.circuit_breaker import CircuitBreaker, CircuitState
from finwiz.supabase.client import SupabaseClient
from finwiz.supabase.models import AnalysisRecord, EmbeddingRecord, PortfolioSnapshot
from finwiz.supabase.repositories.analysis_repository import AnalysisRepository
from finwiz.supabase.repositories.vector_repository import VectorRepository
from finwiz.supabase.services.embedding_service import EmbeddingService
from finwiz.supabase.services.rag_service import HistoricalAnalysisService
from finwiz.supabase.utils.async_tasks import (
    BackgroundTaskManager,
    create_background_task,
    get_task_manager,
    shutdown_task_manager,
)
from finwiz.supabase.utils.rag_integration import (
    enhance_task_description_with_historical_context,
    get_historical_analysis_service,
    get_historical_context_for_inputs,
    is_historical_analysis_enabled,
)

__all__ = [
    # Core client and circuit breaker
    "SupabaseClient",
    "CircuitBreaker",
    "CircuitState",
    # Data models
    "AnalysisRecord",
    "PortfolioSnapshot",
    "EmbeddingRecord",
    # Repositories
    "AnalysisRepository",
    "VectorRepository",
    # Services
    "EmbeddingService",
    "HistoricalAnalysisService",
    # Background task management
    "BackgroundTaskManager",
    "create_background_task",
    "get_task_manager",
    "shutdown_task_manager",
    # Historical Analysis integration utilities (NOT document RAG tools)
    "get_historical_analysis_service",
    "is_historical_analysis_enabled",
    "get_historical_context_for_inputs",
    "enhance_task_description_with_historical_context",
]
