# Supabase Module

This directory contains Supabase integration for persistent storage, vector embeddings, and RAG (Retrieval Augmented Generation) functionality.

## Directory Structure

```
supabase/
├── client.py                # Supabase client initialization
├── models.py               # Database models
├── circuit_breaker.py      # Circuit breaker for resilience
├── repositories/           # Data access layer
│   ├── analysis_repository.py   # Analysis results storage
│   ├── portfolio_repository.py  # Portfolio data storage
│   └── vector_repository.py     # Vector embeddings storage
├── services/               # Business logic layer
│   ├── cache_service.py    # Caching via Supabase
│   ├── embedding_service.py # Text embedding generation
│   ├── migration_service.py # Database migrations
│   └── rag_service.py      # RAG query/storage service
├── utils/                  # Utilities
│   ├── async_tasks.py      # Async task handling
│   ├── encryption.py       # Data encryption
│   ├── monitoring.py       # Performance monitoring
│   └── rag_integration.py  # RAG integration helpers
└── cli/
    └── migrate.py          # Migration CLI commands
```

## Major Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `client.py` | `get_supabase_client()` | Get Supabase client instance |
| `services/rag_service.py` | `RAGService` | Main RAG query/storage |
| `services/embedding_service.py` | `EmbeddingService` | Generate embeddings |
| `repositories/vector_repository.py` | `VectorRepository` | Vector similarity search |
| `repositories/analysis_repository.py` | `AnalysisRepository` | Store/retrieve analyses |

## Usage Pattern

```python
from finwiz.supabase.services.rag_service import RAGService

rag = RAGService()

# Store analysis for future retrieval
await rag.store_analysis(
    ticker="AAPL",
    analysis_type="stock",
    content=analysis_text,
    metadata={"date": "2024-01-15"}
)

# Query similar analyses
results = await rag.query(
    query="What are the key risks for AAPL?",
    top_k=5
)
```

## Environment Variables

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-key
SUPABASE_ANON_KEY=your-anon-key
```

## Documentation

- `INTEGRATION_GUIDE.md` - Setup and configuration guide
- `RAG_INTEGRATION_GUIDE.md` - RAG-specific documentation
- `NAMING_CONVENTION.md` - Table/column naming standards
- `CACHE_INTEGRATION_VERIFICATION.md` - Cache verification steps

## Related Modules

- `finwiz.tools.rag_tools` - CrewAI RAG tools
- `finwiz.tools.save_to_rag_tool` - Save to RAG tool
- `finwiz.rag_config` - RAG configuration
