# CLI Module

Command-line interface utilities for configuring and launching FinWiz.

## Directory Structure

```
cli/
├── __init__.py
└── argument_parser.py    # Configuration and environment bootstrap
```

**There is no argument parsing here, despite the module name.** FinWiz does not
use argparse — `crewai flow kickoff` is the sole production entry point, and
flow parameters travel through CrewAI's own `inputs={...}` mechanism into
`FinwizState`. See the root `CLAUDE.md` section "Parameterizing a flow run".

## Entry Points

| File | Function | Purpose |
|------|----------|---------|
| `argument_parser.py` | `initialize_configuration()` | Load and validate configuration |
| `argument_parser.py` | `initialize_environment()` | Set up environment |

These two are the whole module-level surface.

## Usage

```python
from finwiz.cli.argument_parser import initialize_configuration, initialize_environment

initialize_environment()
initialize_configuration()
```

Both return `None` — they configure global state rather than handing back a
config object.

## Related Modules

- `finwiz.main` — Main entry point that calls CLI functions
- `finwiz.core.app_initializer` — Uses CLI functions during bootstrap; builds
  the flow directly (`FinwizFlow(state=flow_state)`, `app_initializer.py:62`)
- `finwiz.flows.orchestrator` — `FinwizFlow` itself
