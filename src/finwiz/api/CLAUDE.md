# API Module

FastAPI REST API for programmatic access to FinWiz portfolio rebalancing.

## Directory Structure

```
api/
├── __init__.py          # Exports: create_app, rebalancing_router
├── app.py               # FastAPI app factory, lifespan handler
└── rebalancing.py       # Portfolio rebalancing endpoints
```

## Entry Points

| File | Function/Class | Purpose |
|------|---------------|---------|
| `app.py` | `create_app()` | FastAPI application factory |
| `app.py` | `lifespan()` | App startup/shutdown lifecycle |
| `rebalancing.py` | `analyze_portfolio_rebalancing()` | POST — run rebalancing analysis |
| `rebalancing.py` | `get_portfolio_analysis()` | GET — retrieve analysis results |
| `rebalancing.py` | `simulate_rebalancing_scenario()` | POST — simulate scenarios |
| `rebalancing.py` | `get_rebalancing_status()` | GET — check rebalancing status |

## Usage

```python
from finwiz.api.app import create_app

app = create_app()
# uvicorn finwiz.api.app:app --reload
```

## Related Modules

- `finwiz.schemas.api` — Request/response Pydantic models
- `finwiz.orchestrators` — Business logic behind endpoints
