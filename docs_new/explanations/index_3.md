---
title: "Index"
description: "Understanding the concepts and design of Index"
category: "explanations"
tags:
  - "explanations"
date: "2025-10-26"
source: "reference/api/index.md"
---

# API Reference

Complete technical reference for FinWiz's APIs, interfaces, and programmatic access points.

[TOC]

## Core APIs

### CrewAI Integration

- **[Crews](crews.md)** - AI agent crews for financial analysis
  - StockCrew - Comprehensive stock analysis
  - EtfCrew - ETF analysis and evaluation
  - CryptoCrew - Cryptocurrency analysis
  - ReportCrew - Report generation and synthesis

- **[Flows](flows.md)** - Orchestration and workflow management
  - FinwizFlow - Main analysis orchestration
  - Portfolio analysis workflows
  - Batch processing flows

### Data and Analysis

- **[Tools](tools.md)** - Analysis tools and data sources
  - Financial data tools (Yahoo Finance, Alpha Vantage)
  - Technical analysis tools
  - Sentiment analysis tools
  - Validation tools

- **[Schemas](schemas.md)** - Data models and validation
  - Input validation schemas
  - Analysis result schemas
  - Portfolio management schemas
  - Error handling schemas

### Configuration

- **[Configuration](configuration.md)** - System configuration and settings
  - Environment variables
  - Agent configurations
  - Task definitions
  - Tool configurations

## API Categories

### Analysis APIs

| API | Purpose | Input | Output |
|-----|---------|-------|--------|
| Stock Analysis | Analyze individual stocks | Ticker symbol | TenKInsight |
| ETF Analysis | Analyze ETFs | ETF ticker | ETFFactsheet |
| Crypto Analysis | Analyze cryptocurrencies | Crypto symbol | CryptoThesis |
| Portfolio Analysis | Analyze portfolios | Holdings list | PortfolioReview |

### Data APIs

| API | Purpose | Data Source | Rate Limits |
|-----|---------|-------------|-------------|
| Market Data | Real-time prices | Yahoo Finance | 2000/hour |
| Financial Data | Company fundamentals | Alpha Vantage | 500/day |
| News & Sentiment | Market sentiment | Serper API | 2500/month |
| SEC Filings | Regulatory data | SEC EDGAR | No limit |

### Utility APIs

| API | Purpose | Use Case |
|-----|---------|----------|
| Ticker Validation | Validate symbols | Input sanitization |
| Risk Assessment | Standardized scoring | Risk evaluation |
| Report Generation | HTML/PDF reports | Output formatting |
| Data Export | Multiple formats | Data portability |

## Authentication and Access

### API Keys Required

```pythonthon
# Required environment variables
OPENAI_API_KEY = "sk-proj-..."      # OpenAI for AI agents
SERPER_API_KEY = "..."              # Serper for web search
FIRECRAWL_API_KEY = "..."           # Firecrawl for web scraping
ALPHA_VANTAGE_API_KEY = "..."       # Alpha Vantage for financial data
```text
### Optional API Keys

```pythonthon
# Enhanced features (optional)
TWELVE_DATA_API_KEY = "..."         # Technical analysis
PPLX_API_KEY = "..."                # Perplexity search
SEC_API_API_KEY = "..."             # SEC filings (premium)
CHART_IMG_API_KEY = "..."           # Chart generation
COINMARKETCAP_API_KEY = "..."       # Crypto data
```text
## Usage Patterns

### Basic Analysis

```pythonthon
from finwiz.crews.stock_crew import StockCrew

# Analyze a single stock
crew = StockCrew()
result = crew.kickoff(inputs={"ticker": "AAPL"})
print(result.recommendation)  # BUY, HOLD, or SELL
```text
### Portfolio Analysis

```pythonthon
from finwiz.orchestrators.finwiz_flow import FinwizFlow

# Analyze complete portfolio
flow = FinwizFlow()
result = flow.kickoff()
portfolio_review = flow.state.portfolio_review
```text
### Batch Processing

```pythonthon
from finwiz.tools.batch_processor import BatchProcessor

# Process multiple tickers
processor = BatchProcessor()
results = processor.analyze_batch(["AAPL", "GOOGL", "MSFT"])
```text
## Error Handling

### Common Error Types

```pythonthon
from finwiz.exceptions import (
    InvalidTickerError,
    APIError,
    ValidationError,
    RateLimitError
)

try:
    result = analyze_stock("INVALID")
except InvalidTickerError as e:
    print(f"Invalid ticker: {e.ticker}")
except APIError as e:
    print(f"API error: {e.message}")
```text
### Error Response Format

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Invalid ticker symbol format",
    "field": "ticker",
    "code": "INVALID_FORMAT"
  }
}
```text
## Rate Limits and Performance

### API Rate Limits

| Service | Limit | Reset Period |
|---------|-------|--------------|
| OpenAI | 20 RPM | 1 minute |
| Serper | 100/hour | 1 hour |
| Alpha Vantage | 500/day | 24 hours |
| Yahoo Finance | 2000/hour | 1 hour |

### Performance Guidelines

- **Batch Processing**: Use for multiple assets
- **Caching**: Results cached for 1 hour by default
- **Async Operations**: All I/O operations are asynchronous
- **Memory Management**: Automatic cleanup for large datasets

## Versioning and Compatibility

### API Versioning

- **Current Version**: v1.0
- **Backward Compatibility**: Maintained for major versions
- **Deprecation Policy**: 6-month notice for breaking changes

### Schema Evolution

- **Additive Changes**: New fields added without breaking existing code
- **Breaking Changes**: Require version bump
- **Migration Support**: Automatic schema migration tools provided

## Getting Help

### Documentation

- **[Schemas Reference](../schemas/index.md)** - Detailed schema documentation
- **[Error Codes](../errors.md)** - Complete error reference
- **[Examples](../../tutorials/index.md)** - Working code examples

### Support

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community support and questions
- **Documentation**: Comprehensive guides and references

## Contributing

Interested in contributing to FinWiz APIs? See our:

- **[Developer Guide](../../explanations/DEVELOPER_GUIDE.md)** - Development setup and guidelines
- **[API Design Principles](../../explanations/design_principles.md)** - Our API design philosophy
- **[Testing Standards](../../how-to/testing.md)** - How we test our APIs
