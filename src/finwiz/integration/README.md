# FinWiz Crew Data Integration System

The Crew Data Integration System provides centralized coordination and data management for FinWiz crews, ensuring proper data flow between analysis crews (Stock, ETF, Crypto, Discovery) and the final Report crew.

## Overview

This system addresses the communication breakdowns between crews that previously resulted in incomplete reports with missing SEC/EDGAR citations, unavailable market sentiment data, unvalidated tickers, and lack of upstream data integration.

## Key Features

- **Centralized Data Management**: Standardized storage and access for all crew outputs
- **Data Validation Pipeline**: Automated validation of crew outputs against schemas
- **Freshness Monitoring**: Tracks data age and warns about stale data
- **Dependency Management**: Coordinates crew execution based on data dependencies
- **Error Recovery**: Provides clear diagnostics and recovery suggestions
- **Structured Logging**: Comprehensive logging for debugging and auditing
- **Data Lineage Tracking**: Tracks data flow and transformations across crews

## Architecture

### Core Components

1. **CrewDataIntegrationManager**: Central coordinator for all integration operations
2. **Configuration System**: Flexible configuration for crews, dependencies, and quality checks
3. **Logging Utilities**: Structured logging with data lineage tracking
4. **Directory Structure**: Organized storage for metadata, contracts, and consolidated data

### Directory Structure

```
output/
├── integration/
│   ├── metadata/           # Execution logs, validation status, data lineage
│   ├── contracts/          # Standardized crew output contracts
│   └── consolidated/       # Consolidated data for report generation
├── stock/                  # Stock crew outputs
├── etf/                    # ETF crew outputs
├── crypto/                 # Crypto crew outputs
├── discovery/              # Discovery crew outputs
└── portfolio/              # Portfolio crew outputs
```

## Usage

### Basic Usage

```python
from finwiz.integration import CrewDataIntegrationManager
from finwiz.integration.manager import CrewConfig

# Initialize the integration manager
manager = CrewDataIntegrationManager(output_dir=Path("output"))

# Check data freshness
freshness_report = manager.check_data_freshness(max_age_hours=24)
print(f"Overall status: {freshness_report.overall_status}")

# Validate crew output
validation_result = manager.validate_crew_output("stock", output_data)
if not validation_result.is_valid:
    print(f"Validation errors: {validation_result.errors}")

# Coordinate crew execution
crews = [
    CrewConfig(name="stock", dependencies=[]),
    CrewConfig(name="etf", dependencies=[]),
    CrewConfig(name="discovery", dependencies=["stock", "etf"])
]

execution_result = await manager.coordinate_crew_execution(crews)
```

### Configuration

The system uses three main configuration classes:

- **IntegrationConfig**: General integration settings (directories, timeouts, logging)
- **CrewDependencyConfig**: Crew dependencies and execution order
- **DataQualityConfig**: Data quality thresholds and validation rules

```python
from finwiz.integration.config import get_integration_config

config = get_integration_config()
config.default_max_age_hours = 12  # Custom freshness threshold
```

### Logging

The integration system provides structured logging for all operations:

```python
from finwiz.integration.logging_utils import integration_logger

# The logger automatically tracks:
# - Crew execution start/completion
# - Data validation results
# - Data freshness checks
# - Integration errors with recovery suggestions
# - Data lineage and transformations
# - Performance metrics
```

## Data Contracts

All crew outputs must follow standardized contracts with metadata:

```python
{
    "metadata": {
        "crew_name": "stock",
        "execution_timestamp": "2024-01-15T10:30:00Z",
        "schema_version": 1,
        "validation_status": "VALID",
        "data_sources": [...],
        "dependencies_met": true,
        "freshness_status": {...}
    },
    "analysis_results": [...],
    "sec_citations": [...],
    "validated_tickers": [...],
    "market_sentiments": [...]
}
```

## Error Handling

The system provides comprehensive error handling with recovery suggestions:

- **Missing Data**: Clear identification of missing crew outputs with expected paths
- **Stale Data**: Warnings for data older than configured thresholds
- **Validation Errors**: Detailed schema validation errors with specific field issues
- **Dependency Failures**: Clear dependency chain analysis and resolution steps

## Testing

The integration system includes comprehensive unit tests:

```bash
# Run integration system tests
uv run pytest tests/test_integration_manager.py -v

# Run all tests without coverage
uv run pytest tests/test_integration_manager.py --no-cov
```

## Demo

Run the integration system demo to see it in action:

```bash
uv run python examples/integration_system_demo.py
```

## Requirements Addressed

This implementation addresses the following requirements from the specification:

- **4.1, 4.2**: Centralized data integration with standardized contracts
- **7.1**: Comprehensive logging and error reporting with specific file paths
- **6.1, 6.2**: Data freshness monitoring and stale data detection
- **3.1, 3.2**: Data validation pipeline with schema compliance
- **1.1, 1.2**: SEC citation handling and integration
- **2.1, 2.2**: Market sentiment data consolidation
- **5.1, 5.2**: A+ opportunity integration framework

## Next Steps

This core infrastructure provides the foundation for:

1. Enhanced data schemas with metadata (Task 2)
2. Data freshness monitoring system (Task 3)
3. Centralized validation pipeline (Task 4)
4. Unified data access layer (Task 5)
5. A+ opportunity integration (Task 6)
6. Error handling and recovery (Task 7)
7. Integration middleware (Task 8)
8. Report crew integration (Task 9)
9. Logging and monitoring (Task 10)

The system is designed to be extensible and can be enhanced with additional features as needed.