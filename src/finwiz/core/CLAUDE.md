# Core Module

Application bootstrapping and entry point for the FinWiz platform.

## Directory Structure

```
core/
├── __init__.py
└── app_initializer.py    # Main entry point
```

## Entry Points

| File | Function | Purpose |
|------|----------|---------|
| `app_initializer.py` | `kickoff()` | Bootstraps and runs the full FinWiz flow |

## Startup Sequence

`kickoff()` performs these steps in order:

1. Validate template variables at startup
2. Initialize configuration (settings, env)
3. Initialize environment and retry mechanism
4. Create `FinwizState` instance
5. Create `FinwizFlow` instance
6. Execute the flow (`flow.kickoff()`)
7. Returns `None`

## Usage

```python
from finwiz.core.app_initializer import kickoff

kickoff()  # Runs the full analysis pipeline
```

## Related Modules

- `finwiz.flows.orchestrator` — `FinwizFlow` created and executed by `kickoff()`
- `finwiz.flow_state` — `FinwizState` created during bootstrap
- `finwiz.config.settings` — Configuration loaded during init
- `finwiz.validation.template` — Template variable validation at startup
