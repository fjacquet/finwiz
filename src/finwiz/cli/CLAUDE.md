# CLI Module

This directory contains command-line interface utilities for parsing arguments and running FinWiz from the terminal.

## Directory Structure

```
cli/
├── argument_parser.py    # Main argument parsing logic
└── __init__.py
```

## Major Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `argument_parser.py` | `parse_args()` | Parse command line arguments |
| `argument_parser.py` | `create_parser()` | Create ArgumentParser with all options |
| `argument_parser.py` | `validate_args()` | Validate argument combinations |

## CLI Options

```bash
# Full portfolio analysis
crewai flow kickoff

# Specific ticker analysis
uv run python src/finwiz/main.py --ticker AAPL

# A+ discovery mode
uv run python src/finwiz/main.py --discovery

# Portfolio rebalancing
uv run python src/finwiz/main.py --rebalancing

# Verbose mode
uv run python src/finwiz/main.py --verbose

# Specify portfolio file
uv run python src/finwiz/main.py --portfolio data/portfolio.csv
```

## Usage in Code

```python
from finwiz.cli.argument_parser import parse_args

args = parse_args()
if args.ticker:
    run_single_ticker_analysis(args.ticker)
elif args.discovery:
    run_discovery_mode()
```

## Related Modules

- `finwiz.main` - Main entry point
- `finwiz.flows.flow_orchestrator` - Flow execution
