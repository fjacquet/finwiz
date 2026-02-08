# CLI Module

Command-line interface utilities for configuring and launching FinWiz.

## Directory Structure

```
cli/
├── __init__.py
└── argument_parser.py    # Configuration and argument parsing
```

## Entry Points

| File | Function | Purpose |
|------|----------|---------|
| `argument_parser.py` | `parse_arguments()` | Parse command-line arguments |
| `argument_parser.py` | `initialize_configuration()` | Load and validate configuration |
| `argument_parser.py` | `initialize_environment()` | Set up environment and retry mechanism |
| `argument_parser.py` | `initialize_flow()` | Create and configure FinwizFlow instance |

## Usage

```python
from finwiz.cli.argument_parser import parse_arguments, initialize_configuration

args = parse_arguments()
config = initialize_configuration()
```

## Related Modules

- `finwiz.main` — Main entry point that calls CLI functions
- `finwiz.core.app_initializer` — Uses CLI functions during bootstrap
- `finwiz.flows.orchestrator` — Flow created by `initialize_flow()`
