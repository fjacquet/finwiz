---
title: "Index"
description: "Complete reference documentation for Index"
category: "reference"
tags:
  - "reference"
date: "2025-10-26"
source: "reference/index.md"
---

# Reference Documentation

This section provides comprehensive technical reference information for FinWiz. Use these documents to look up specific details about APIs, schemas, commands, and configuration options.

## API Reference

Complete documentation for FinWiz's APIs and interfaces:

- **[Crews API](api/crews.md)** - CrewAI crews for stock, ETF, and crypto analysis
- **[Tools API](api/tools.md)** - Analysis tools and data sources
- **[Schemas API](api/schemas.md)** - Data models and validation schemas
- **[Flow API](api/flows.md)** - Orchestration and workflow management
- **[Configuration API](api/configuration.md)** - Configuration options and settings

## Command Line Interface

- **[CLI Commands](cli_commands.md)** - Complete command-line reference
- **[Command Options](cli_options.md)** - Detailed options for each command
- **[Environment Variables](environment_variables.md)** - Configuration via environment variables

## Data Schemas

Comprehensive schema documentation with examples:

- **[Schema Overview](schemas/index.md)** - Introduction to FinWiz data schemas
- **[Analysis Schemas](schemas/analysis_schemas.md)** - TenKInsight, MarketSentiment, RiskAssessment
- **[Portfolio Schemas](schemas/portfolio_schemas.md)** - PortfolioReview, HoldingDecision, Alternative
- **[Discovery Schemas](schemas/discovery_schemas.md)** - APlusDiscoveryResult, InvestmentCandidate
- **[Validation Schemas](schemas/validation_schemas.md)** - Input validation and error handling

## Configuration Reference

- **[Configuration Files](configuration.md)** - Complete configuration reference
- **[Agent Configuration](agent_configuration.md)** - CrewAI agent setup and customization
- **[Task Configuration](task_configuration.md)** - Task definitions and parameters
- **[Tool Configuration](tool_configuration.md)** - Tool setup and configuration options

## Error Codes and Messages

- **[Error Reference](errors.md)** - Complete list of error codes and messages
- **[Validation Errors](validation_errors.md)** - Data validation error reference
- **[API Errors](api_errors.md)** - External API error handling

## Data Sources and Providers

- **[Supported Data Sources](data_sources.md)** - Complete list of supported data providers
- **[API Requirements](api_requirements.md)** - Required API keys and rate limits
- **[Data Quality Standards](data_quality.md)** - Data validation and quality requirements

## Performance and Limits

- **[Performance Specifications](performance.md)** - System requirements and performance characteristics
- **[Rate Limits](rate_limits.md)** - API rate limits and throttling
- **[Resource Usage](resource_usage.md)** - Memory and CPU usage guidelines

## Version Information

- **[Changelog](changelog.md)** - Version history and changes
- **[Migration Guide](migration.md)** - Upgrading between versions
- **[Compatibility Matrix](compatibility.md)** - Supported versions and dependencies

## Quick Reference Tables

### Asset Classes

| Asset Class | Crew | Primary Tools | Output Schema |
|-------------|------|---------------|---------------|
| Stock | StockCrew | SEC Analysis, Quantitative Analysis | TenKInsight |
| ETF | EtfCrew | ETF Analysis, Holdings Analysis | ETFFactsheet |
| Crypto | CryptoCrew | Crypto Analysis, Market Data | CryptoThesis |

### Risk Assessment Scale

| Score | Level | Description |
|-------|-------|-------------|
| 1-2 | Very Low | Minimal risk, stable assets |
| 3-4 | Low | Below-average risk |
| 5-6 | Moderate | Average market risk |
| 7-8 | High | Above-average risk |
| 9-10 | Very High | Extreme risk, speculative |

### Recommendation Types

| Recommendation | Confidence Threshold | Time Horizon |
|----------------|---------------------|--------------|
| BUY | ≥ 0.7 | 12+ months |
| HOLD | 0.4 - 0.7 | 6-12 months |
| SELL | < 0.4 | Immediate |

## Using This Reference

This reference documentation is organized for quick lookup:

- **Alphabetical indexes** for finding specific items
- **Cross-references** between related concepts
- **Code examples** for practical implementation
- **Version notes** for compatibility information

## API Documentation Format

All API documentation follows this consistent format:

- **Endpoint/Function signature**
- **Parameters** with types and descriptions
- **Return values** with schema references
- **Examples** with sample requests and responses
- **Error conditions** and handling
- **Related endpoints/functions**
