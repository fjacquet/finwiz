"""
Supabase repository layer for data access operations.

Provides CRUD operations for analyses, portfolios, and vector embeddings
with async execution, timeout enforcement, and error handling.
"""

from finwiz.supabase.repositories.analysis_repository import AnalysisRepository

__all__ = ["AnalysisRepository"]
