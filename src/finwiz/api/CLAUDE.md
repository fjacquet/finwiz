# API Module

This directory contains the FastAPI REST API for programmatic access to FinWiz functionality.

## Directory Structure

```
api/
├── app.py               # FastAPI application setup
├── rebalancing.py       # Rebalancing endpoints
├── monitoring.py        # Monitoring and health endpoints
└── __init__.py
```

## Major Entry Points

| File | Function/Class | Purpose |
|------|---------------|---------|
| `app.py` | `app` | FastAPI application instance |
| `app.py` | `create_app()` | Factory function for app creation |
| `rebalancing.py` | `/api/rebalancing` | Portfolio rebalancing endpoints |
| `monitoring.py` | `/api/health` | Health check endpoint |
| `monitoring.py` | `/api/metrics` | Performance metrics endpoint |

## API Endpoints

```
GET  /api/health              # Health check
GET  /api/metrics             # System metrics
POST /api/analyze             # Run analysis on ticker
POST /api/rebalancing/run     # Execute rebalancing
GET  /api/rebalancing/status  # Get rebalancing status
```

## Usage Pattern

```python
from finwiz.api.app import create_app

app = create_app()

# Run with uvicorn
# uvicorn finwiz.api.app:app --reload
```

## Request/Response Schemas

API uses Pydantic schemas from `finwiz.schemas.api`:

```python
from finwiz.schemas.api.models import AnalysisRequest, AnalysisResponse

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    # Process request
    return AnalysisResponse(...)
```

## Related Modules

- `finwiz.schemas.api` - API request/response schemas
- `finwiz.orchestrators` - Business logic
