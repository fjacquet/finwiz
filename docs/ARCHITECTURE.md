# FinWiz Architecture Guide

This guide provides a high-level overview of the FinWiz system architecture, its core components, and data flows. For specific implementation rules and coding standards, refer to the steering files in the `.kiro/steering/` directory.

## Table of Contents

1.  [System Architecture](#system-architecture)
2.  [Core Systems](#core-systems)
3.  [Data Flow](#data-flow)
4.  [Modernization History](#modernization-history)
5.  [Performance & Security](#performance--security)
6.  [See Also](#see-also)

## System Architecture

### High-Level View

FinWiz is a modular system composed of specialized AI agent crews that perform financial analysis. The crews work in concert, orchestrated by a central flow, to analyze assets, review portfolios, and generate reports. The core systems provide cross-cutting services like validation, caching, and feature flagging.

```
┌─────────────────────────────────────────────────────────────┐
│                     FinWiz Application                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Stock Crew   │  │  ETF Crew    │  │ Crypto Crew  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │ Portfolio Review │                        │
│                   └────────┬────────┘                        │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │   Rebalancing   │                        │
│                   └────────┬────────┘                        │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │  Report Crew    │                        │
│                   └─────────────────┘                        │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                     Core Systems                              │
├─────────────────────────────────────────────────────────────┤
│  Validation │ Caching │ Feature Flags │ Quantitative         │
└─────────────────────────────────────────────────────────────┘
```

### Project Structure

The codebase is organized by function to promote separation of concerns.

```
src/finwiz/
├── crews/              # AI agent crews
├── tools/              # Domain-specific analysis tools
├── schemas/            # Pydantic models with strict validation
├── orchestrators/      # Flow coordination logic
├── quantitative/       # Quantitative analysis framework
├── integration/        # Data integration components
├── validation/         # Validation system
├── utils/              # Utility functions
└── main.py            # CrewAI Flow entry point
```

For detailed rules on code structure, file organization, and CrewAI patterns, see **[/.kiro/steering/structure.md](/.kiro/steering/structure.md)** and **[/.kiro/steering/crewai-standards.md](/.kiro/steering/crewai-standards.md)**.

## Core Systems

### 1. Validation System

-   **Purpose**: Provides centralized data validation with configurable strictness (`off`, `warn`, `error`).
-   **Components**: Includes a `ValidationManager` and a `SchemaRegistry` for all Pydantic models.
-   **More Info**: See **[/.kiro/steering/validation.md](/.kiro/steering/validation.md)** for validation rules.

### 2. Caching System

-   **Purpose**: An intelligent caching layer to improve performance and reduce API calls.
-   **Backends**: Supports `memory`, `file`, and `hybrid` backends.
-   **Features**: Configurable TTL, multiple eviction strategies (TTL, LRU, LFU), and performance monitoring.

### 3. Feature Flags System

-   **Purpose**: Allows for gradual feature rollouts and provides circuit breaker protection for external services.
-   **Configuration**: Managed via environment variables (e.g., `FF_PERPLEXITY_RESEARCH`).

### 4. Quantitative Analysis Framework

-   **Purpose**: A professional-grade framework for quantitative analysis.
-   **Components**: Integrates libraries like TA-Lib for technical analysis and Backtrader for strategy backtesting.

## Data Flow

The system processes data in well-defined flows.

### Portfolio Analysis Flow

```
1. CSV Input (data/etf.csv, data/stock.csv)
   ↓
2. Ticker Validation (TickerValidationTool)
   ↓
3. Crew Analysis (Stock/ETF/Crypto Crews)
   ↓
4. Price Target Calculation (PriceTargetCalculator)
   ↓
5. Alternative Finding (AlternativeFinder)
   ↓
6. Position Sizing (PositionSizingTool)
   ↓
7. Portfolio Review (PortfolioReview schema)
   ↓
8. HTML Report Generation
```

### Validation Flow

```
1. Data Input
   ↓
2. Schema Lookup (SchemaRegistry)
   ↓
3. Pydantic Validation
   ↓
4. ValidationResult Creation
   ↓
5. Error Handling (based on strictness mode)
   ↓
6. Sanitized Data Output
```

## Modernization History

The FinWiz codebase has undergone significant refactoring to improve maintainability and performance. Key initiatives include:

-   **File Decomposition**: Large monolithic files (often over 1000 lines) were split into focused, single-responsibility modules, with a target of under 200 lines per file.
-   **Scientific Package Optimization**: Manual, loop-based calculations were replaced with vectorized operations using `pandas` and `numpy` for significant performance gains.
-   **Testing Infrastructure**: The test suite was standardized on `pytest` with `pytest-mock`, banning `unittest.mock` entirely.

## Performance & Security

### Performance Architecture

-   **Asynchronous Operations**: `asyncio` is used for I/O-bound operations, such as parallel API calls, to improve throughput.
-   **Caching**: A multi-backend caching system reduces latency and external API usage.
-   **Rate Limiting**: A rate limiter with exponential backoff prevents API throttling.

### Security Architecture

-   **Data Privacy**: The system is designed to never log sensitive personal or financial data. API keys are managed via environment variables.
-   **Input Validation**: All external inputs are sanitized and validated using Pydantic models to prevent injection and data corruption.
-   **API Security**: All external API calls are made over HTTPS, with request timeouts and certificate verification.

## See Also

-   **[Developer Guide](DEVELOPER_GUIDE.md)**: High-level guide for developers.
-   **[API Reference](API_REFERENCE.md)**: Complete API documentation.
-   **[Steering Files](/.kiro/steering/)**: Prescriptive rules for AI-assisted development.