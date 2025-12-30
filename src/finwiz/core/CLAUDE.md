# Core Module

This directory contains core application initialization and bootstrapping logic.

## Directory Structure

```
core/
├── app_initializer.py    # Application initialization logic
└── __init__.py
```

## Major Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `app_initializer.py` | `AppInitializer` | Initializes all FinWiz components |
| `app_initializer.py` | `initialize_app()` | Main entry point for app setup |
| `app_initializer.py` | `validate_environment()` | Check required env vars |
| `app_initializer.py` | `setup_logging()` | Configure logging infrastructure |

## Usage Pattern

```python
from finwiz.core.app_initializer import initialize_app

# Initialize application
app = initialize_app()

# Access initialized components
cache = app.cache
config = app.config
```

## Initialization Sequence

1. Load environment variables
2. Validate required API keys
3. Initialize caching layer
4. Setup logging
5. Configure LLM clients
6. Return initialized app context

## Related Modules

- `finwiz.config.settings` - Configuration loading
- `finwiz.utils.logging_helpers` - Logging setup
