---
title: "CLI Commands Reference"
description: "Complete reference for FinWiz command-line interface commands and options"
category: "reference"
tags:
  - "cli"
  - "commands"
  - "reference"
  - "command-line"
date: "2025-10-26"
---

# CLI Commands Reference

Complete reference for FinWiz's command-line interface, including all available commands, options, and usage examples.

## Overview

FinWiz provides a comprehensive command-line interface for running analyses, managing portfolios, and configuring the system. All commands are executed through the main entry point.

## Basic Usage

```bash
# Basic command structure
uv run python src/finwiz/main.py [OPTIONS] [COMMAND]

# Get help
uv run python src/finwiz/main.py --help
```

## Global Options

Options that apply to all commands:

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--verbose` | `-v` | Enable verbose logging | `False` |
| `--quiet` | `-q` | Suppress non-error output | `False` |
| `--config` | `-c` | Configuration file path | `.env` |
| `--log-level` | | Set logging level | `INFO` |
| `--output-dir` | `-o` | Output directory | `output` |
| `--cache-dir` | | Cache directory | `cache` |
| `--help` | `-h` | Show help message | |

## Analysis Commands

### Single Asset Analysis

Analyze individual stocks, ETFs, or cryptocurrencies.

**Command**: `analyze` (default)

**Usage**:

```bash
uv run python src/finwiz/main.py --ticker TICKER --asset-class CLASS [OPTIONS]
```

**Required Options**:

- `--ticker TICKER`: Asset ticker symbol (e.g., AAPL, SPY, BTC)
- `--asset-class CLASS`: Asset class (`stock`, `etf`, or `crypto`)

**Optional Options**:

- `--deep-analysis`: Enable comprehensive deep analysis
- `--output-format FORMAT`: Output format (`html`, `json`, `both`) [default: `both`]
- `--save-report`: Save HTML report to file
- `--no-cache`: Disable caching for this analysis

**Examples**:

```bash
# Analyze Apple stock
uv run python src/finwiz/main.py --ticker AAPL --asset-class stock

# Analyze S&P 500 ETF with deep analysis
uv run python src/finwiz/main.py --ticker SPY --asset-class etf --deep-analysis

# Analyze Bitcoin with JSON output only
uv run python src/finwiz/main.py --ticker BTC --asset-class crypto --output-format json

# Analyze with verbose logging
uv run python src/finwiz/main.py --ticker MSFT --asset-class stock --verbose
```

### Portfolio Analysis

Analyze complete investment portfolios.

**Command**: `portfolio`

**Usage**:

```bash
uv run python src/finwiz/main.py --mode portfolio_review [OPTIONS]
```

**Options**:

- `--portfolio-file FILE`: Custom portfolio CSV file
- `--asset-class CLASS`: Analyze specific asset class only
- `--deep-analysis`: Enable deep analysis for all holdings
- `--batch-size SIZE`: Batch size for parallel processing [default: `5`]
- `--max-holdings COUNT`: Maximum holdings to analyze
- `--skip-alternatives`: Skip alternative investment suggestions

**Examples**:

```bash
# Analyze complete portfolio
uv run python src/finwiz/main.py --mode portfolio_review

# Analyze only stock holdings with deep analysis
uv run python src/finwiz/main.py --mode portfolio_review --asset-class stock --deep-analysis

# Analyze with custom batch size
uv run python src/finwiz/main.py --mode portfolio_review --batch-size 10

# Analyze first 20 holdings only
uv run python src/finwiz/main.py --mode portfolio_review --max-holdings 20
```

### Batch Analysis

Analyze multiple assets in batch mode.

**Command**: `batch`

**Usage**:

```bash
uv run python src/finwiz/main.py --mode batch --input-file FILE [OPTIONS]
```

**Required Options**:

- `--input-file FILE`: CSV file with tickers and asset classes

**Optional Options**:

- `--batch-size SIZE`: Number of assets to process in parallel [default: `5`]
- `--output-format FORMAT`: Output format for each analysis
- `--continue-on-error`: Continue processing if individual analyses fail
- `--max-retries COUNT`: Maximum retry attempts for failed analyses [default: `3`]

**Input File Format**:

```csv
ticker,asset_class,name
AAPL,stock,Apple Inc
SPY,etf,SPDR S&P 500 ETF Trust
BTC,crypto,Bitcoin
```

**Examples**:

```bash
# Batch analyze from CSV file
uv run python src/finwiz/main.py --mode batch --input-file assets.csv

# Batch analyze with larger batch size
uv run python src/finwiz/main.py --mode batch --input-file assets.csv --batch-size 10

# Continue on errors with retries
uv run python src/finwiz/main.py --mode batch --input-file assets.csv --continue-on-error --max-retries 5
```

## Discovery Commands

### Investment Discovery

Discover new A+ investment opportunities.

**Command**: `discover`

**Usage**:

```bash
uv run python src/finwiz/main.py --mode discovery --asset-class CLASS [OPTIONS]
```

**Required Options**:

- `--asset-class CLASS`: Asset class to discover (`stock`, `etf`, or `crypto`)

**Optional Options**:

- `--max-results COUNT`: Maximum opportunities to find [default: `10`]
- `--min-score SCORE`: Minimum composite score threshold [default: `0.85`]
- `--sector SECTOR`: Focus on specific sector
- `--market-cap SIZE`: Market cap filter (`small`, `mid`, `large`, `mega`)
- `--exclude-file FILE`: File with tickers to exclude

**Examples**:

```bash
# Discover A+ stocks
uv run python src/finwiz/main.py --mode discovery --asset-class stock

# Discover top 20 ETFs with minimum score 0.9
uv run python src/finwiz/main.py --mode discovery --asset-class etf --max-results 20 --min-score 0.9

# Discover large-cap technology stocks
uv run python src/finwiz/main.py --mode discovery --asset-class stock --sector technology --market-cap large

# Discover crypto excluding current holdings
uv run python src/finwiz/main.py --mode discovery --asset-class crypto --exclude-file data/crypto.csv
```

## Utility Commands

### Validation

Validate tickers, portfolios, or configuration.

**Command**: `validate`

**Usage**:

```bash
uv run python src/finwiz/main.py --mode validate [OPTIONS]
```

**Options**:

- `--ticker TICKER`: Validate single ticker
- `--portfolio-file FILE`: Validate portfolio CSV file
- `--config-only`: Validate configuration only
- `--api-keys`: Test API key connectivity
- `--fix-issues`: Attempt to fix validation issues

**Examples**:

```bash
# Validate single ticker
uv run python src/finwiz/main.py --mode validate --ticker AAPL

# Validate portfolio file
uv run python src/finwiz/main.py --mode validate --portfolio-file data/stock.csv

# Validate configuration and API keys
uv run python src/finwiz/main.py --mode validate --config-only --api-keys

# Validate and fix portfolio issues
uv run python src/finwiz/main.py --mode validate --portfolio-file data/stock.csv --fix-issues
```

### Cache Management

Manage analysis cache.

**Command**: `cache`

**Usage**:

```bash
uv run python src/finwiz/main.py --mode cache ACTION [OPTIONS]
```

**Actions**:

- `clear`: Clear all cache
- `clean`: Clean expired cache entries
- `stats`: Show cache statistics
- `list`: List cached items

**Options**:

- `--cache-type TYPE`: Cache type to manage (`memory`, `file`, `all`) [default: `all`]
- `--older-than DAYS`: Clear cache older than N days
- `--ticker TICKER`: Manage cache for specific ticker

**Examples**:

```bash
# Clear all cache
uv run python src/finwiz/main.py --mode cache clear

# Clean expired entries
uv run python src/finwiz/main.py --mode cache clean

# Show cache statistics
uv run python src/finwiz/main.py --mode cache stats

# Clear cache older than 7 days
uv run python src/finwiz/main.py --mode cache clear --older-than 7

# Clear cache for specific ticker
uv run python src/finwiz/main.py --mode cache clear --ticker AAPL
```

### Configuration

Manage FinWiz configuration.

**Command**: `config`

**Usage**:

```bash
uv run python src/finwiz/main.py --mode config ACTION [OPTIONS]
```

**Actions**:

- `show`: Display current configuration
- `test`: Test configuration and API connectivity
- `init`: Initialize configuration from template
- `validate`: Validate configuration file

**Options**:

- `--config-file FILE`: Configuration file path [default: `.env`]
- `--output-format FORMAT`: Output format (`text`, `json`, `yaml`)
- `--section SECTION`: Show specific configuration section

**Examples**:

```bash
# Show current configuration
uv run python src/finwiz/main.py --mode config show

# Test API connectivity
uv run python src/finwiz/main.py --mode config test

# Initialize configuration from template
uv run python src/finwiz/main.py --mode config init

# Show API configuration in JSON format
uv run python src/finwiz/main.py --mode config show --section api --output-format json
```

## Output Options

### Format Options

Control output format and destination:

| Option | Values | Description |
|--------|--------|-------------|
| `--output-format` | `html`, `json`, `both` | Analysis output format |
| `--output-file` | `FILE` | Custom output file path |
| `--no-timestamp` | | Don't add timestamp to output files |
| `--compress` | | Compress output files |

### Verbosity Options

Control logging and output verbosity:

| Option | Description |
|--------|-------------|
| `--verbose` | Enable verbose logging (INFO level) |
| `--debug` | Enable debug logging (DEBUG level) |
| `--quiet` | Suppress all non-error output |
| `--log-file FILE` | Write logs to file |
| `--no-color` | Disable colored output |

## Environment Variables

CLI behavior can be controlled through environment variables:

```bash
# Logging
export LOG_LEVEL=DEBUG
export FINWIZ_VERBOSE=true
export FINWIZ_LOG_FILE=logs/finwiz.log

# Output
export FINWIZ_OUTPUT_DIR=custom_output
export FINWIZ_OUTPUT_FORMAT=json
export FINWIZ_COMPRESS_OUTPUT=true

# Performance
export FINWIZ_BATCH_SIZE=10
export FINWIZ_MAX_WORKERS=8
export FINWIZ_TIMEOUT=300

# Cache
export FINWIZ_CACHE_DIR=custom_cache
export FINWIZ_CACHE_TTL=7200
export FINWIZ_DISABLE_CACHE=false
```

## Exit Codes

FinWiz uses standard exit codes:

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Invalid command line arguments |
| `3` | Configuration error |
| `4` | API connection error |
| `5` | Validation error |
| `6` | Analysis error |
| `7` | File I/O error |
| `8` | Timeout error |

## Examples by Use Case

### Quick Stock Analysis

```bash
# Basic analysis
uv run python src/finwiz/main.py --ticker AAPL --asset-class stock

# With verbose output
uv run python src/finwiz/main.py --ticker AAPL --asset-class stock --verbose

# Save to custom location
uv run python src/finwiz/main.py --ticker AAPL --asset-class stock --output-dir ~/finwiz_reports
```

### Portfolio Management

```bash
# Full portfolio review
uv run python src/finwiz/main.py --mode portfolio_review --deep-analysis

# Quick portfolio check (no deep analysis)
uv run python src/finwiz/main.py --mode portfolio_review --skip-alternatives

# Analyze specific asset class
uv run python src/finwiz/main.py --mode portfolio_review --asset-class etf
```

### Research and Discovery

```bash
# Find A+ stock opportunities
uv run python src/finwiz/main.py --mode discovery --asset-class stock --max-results 20

# Technology sector focus
uv run python src/finwiz/main.py --mode discovery --asset-class stock --sector technology

# High-quality ETFs only
uv run python src/finwiz/main.py --mode discovery --asset-class etf --min-score 0.9
```

### Batch Processing

```bash
# Process watchlist
uv run python src/finwiz/main.py --mode batch --input-file watchlist.csv --batch-size 8

# Large portfolio analysis
uv run python src/finwiz/main.py --mode batch --input-file large_portfolio.csv --continue-on-error
```

### Maintenance Tasks

```bash
# System health check
uv run python src/finwiz/main.py --mode config test --verbose

# Clean up old cache
uv run python src/finwiz/main.py --mode cache clean --older-than 30

# Validate portfolio data
uv run python src/finwiz/main.py --mode validate --portfolio-file data/stock.csv --fix-issues
```

## Troubleshooting

### Common Issues

**Issue**: Command not found

```bash
# Solution: Use full path to Python script
uv run python src/finwiz/main.py --help
```

**Issue**: API key errors

```bash
# Solution: Test configuration
uv run python src/finwiz/main.py --mode config test
```

**Issue**: Slow performance

```bash
# Solution: Increase batch size and enable caching
uv run python src/finwiz/main.py --mode portfolio_review --batch-size 10
```

**Issue**: Memory errors

```bash
# Solution: Reduce batch size
uv run python src/finwiz/main.py --mode portfolio_review --batch-size 3
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Enable debug logging
uv run python src/finwiz/main.py --debug --ticker AAPL --asset-class stock

# Save debug logs to file
uv run python src/finwiz/main.py --debug --log-file debug.log --ticker AAPL --asset-class stock
```

### Performance Monitoring

Monitor command performance:

```bash
# Time command execution
time uv run python src/finwiz/main.py --mode portfolio_review

# Monitor memory usage (macOS/Linux)
/usr/bin/time -v uv run python src/finwiz/main.py --mode portfolio_review
```

## Related Documentation

- **[Getting Started Tutorial](../tutorials/getting_started.md)** - Basic CLI usage
- **[Configuration Guide](../how-to/setup_environment.md)** - Environment setup
- **[API Reference](api/)** - Programmatic interface
- **[Troubleshooting Guide](../how-to/troubleshooting.md)** - Common issues

---

**Version**: 2.0  
**Last Updated**: 2025-10-26
