---
title: "Api Reference"
description: "Complete reference documentation for Api Reference"
category: "reference"
tags:
  - "api"
  - "reference"
date: "2025-10-26"
source: "investment_discovery/api_reference.md"
---

# API Reference - A+ Investment Discovery System

## Overview

This document provides comprehensive API reference for the A+ Investment Discovery system, including REST endpoints, Python APIs, and data schemas.

## REST API Endpoints

### Base URL

```text
https://api.finwiz.ai/v1/discovery
```text
### Authentication

All endpoints require Bearer token authentication:

```http
Authorization: Bearer <your-api-token>
```text
### Discovery Endpoints

#### POST /discover/{asset_type}

Discover A+ investment opportunities for a specific asset type.

**Parameters:**

- `asset_type` (path): Asset type to discover (`etf`, `stock`, `crypto`)

**Request Body:**

```json
{
  "custom_criteria": {
    "min_score": 0.95,
    "max_results": 20,
    "regions": ["US", "EU"],
    "risk_tolerance": "moderate"
  },
  "portfolio_context": {
    "current_holdings": [
      {"symbol": "VTI", "allocation": 0.4},
      {"symbol": "VXUS", "allocation": 0.3}
    ],
    "target_allocation": {
      "stocks": 0.7,
      "bonds": 0.2,
      "alternatives": 0.1
    }
  }
}
```text
**Response:**

```json
{
  "discovery_date": "2025-09-25T10:30:00Z",
  "asset_type": "etf",
  "total_screened": 3247,
  "execution_time_seconds": 45.2,
  "a_plus_candidates": [
    {
      "candidate": {
        "symbol": "VXUS",
        "name": "Vanguard Total International Stock ETF",
        "asset_type": "etf",
        "current_price": 58.42,
        "market_cap": 45000000000,
        "preliminary_score": 0.97,
        "discovery_date": "2025-09-25T10:30:00Z"
      },
      "fundamental_score": 0.95,
      "technical_score": 0.92,
      "quality_score": 0.98,
      "risk_score": 0.89,
      "final_grade": "A+",
      "confidence_level": 0.94,
      "rationale": [
        "Exceptionally low expense ratio of 0.08%",
        "Strong tracking performance with 0.12% error",
        "Excellent diversification across 4,000+ holdings",
        "Consistent outperformance vs benchmark"
      ]
    }
  ],
  "portfolio_improvements": [
    {
      "current_holding": "FTSE Developed Markets ETF",
      "recommended_replacement": {
        "symbol": "VXUS",
        "name": "Vanguard Total International Stock ETF"
      },
      "expected_grade_improvement": 0.15,
      "risk_impact": {
        "volatility_change": -0.02,
        "sharpe_improvement": 0.08
      },
      "cost_analysis": {
        "current_expense_ratio": 0.45,
        "new_expense_ratio": 0.08,
        "annual_savings": 0.37
      },
      "implementation_priority": 1
    }
  ],
  "market_context": {
    "regime": "moderate_volatility",
    "vix_level": 18.5,
    "interest_rate_environment": "rising",
    "inflation_rate": 3.2
  }
}
```text
#### GET /monitor/{symbol}

Monitor the current A+ status of a specific investment.

**Parameters:**

- `symbol` (path): Investment symbol to monitor

**Response:**

```json
{
  "symbol": "VXUS",
  "current_grade": "A+",
  "current_score": 0.96,
  "last_updated": "2025-09-25T08:00:00Z",
  "grade_history": [
    {"date": "2025-09-01", "grade": "A+", "score": 0.97},
    {"date": "2025-08-01", "grade": "A+", "score": 0.96},
    {"date": "2025-07-01", "grade": "A", "score": 0.94}
  ],
  "alerts": [
    {
      "type": "grade_change",
      "message": "Grade maintained A+ for 3 consecutive months",
      "severity": "info"
    }
  ],
  "next_review_date": "2025-10-01T00:00:00Z"
}
```text
#### POST /batch-discover

Discover A+ opportunities across multiple asset types in a single request.

**Request Body:**

```json
{
  "asset_types": ["etf", "stock", "crypto"],
  "global_criteria": {
    "min_score": 0.95,
    "max_results_per_type": 10
  },
  "asset_specific_criteria": {
    "etf": {
      "max_expense_ratio": 0.15,
      "min_aum_billions": 1.0
    },
    "stock": {
      "min_roe": 0.20,
      "min_market_cap_billions": 5.0
    },
    "crypto": {
      "min_market_cap_billions": 10.0,
      "institutional_adoption_required": true
    }
  }
}
```text
#### GET /criteria/{asset_type}

Get current screening criteria for an asset type.

**Response:**

```json
{
  "asset_type": "etf",
  "criteria": {
    "max_expense_ratio": 0.15,
    "min_aum_billions": 1.0,
    "max_tracking_error": 0.002,
    "min_history_years": 3,
    "ucits_compliant": true
  },
  "market_adjustments": {
    "regime": "high_volatility",
    "quality_weight_multiplier": 1.2,
    "cost_sensitivity_increased": true
  },
  "last_updated": "2025-09-25T06:00:00Z"
}
```text
### Portfolio Integration Endpoints

#### POST /integrate-discoveries

Integrate A+ discoveries into an existing portfolio.

**Request Body:**

```json
{
  "current_portfolio": {
    "holdings": [
      {"symbol": "VTI", "shares": 100, "current_value": 24500},
      {"symbol": "BND", "shares": 200, "current_value": 16800}
    ],
    "cash": 5000,
    "total_value": 46300
  },
  "discoveries": [
    {
      "symbol": "VXUS",
      "recommended_allocation": 0.25,
      "replacement_for": "FTSE Developed Markets ETF"
    }
  ],
  "constraints": {
    "max_transaction_cost": 100,
    "tax_loss_harvesting": true,
    "rebalancing_threshold": 0.05
  }
}
```text
## Python API

### Core Classes

#### InvestmentDiscoveryCrew

Main class for orchestrating A+ discovery.

```pythonthon
from finwiz.crews.investment_discovery_crew import InvestmentDiscoveryCrew
from finwiz.schemas.investment_discovery import APlusDiscoveryResult

# Initialize discovery crew
crew = InvestmentDiscoveryCrew()

# Discover A+ ETFs
result: APlusDiscoveryResult = crew.discover_etfs(
    custom_criteria={
        'max_expense_ratio': 0.10,
        'min_aum_billions': 2.0
    }
)

# Discover across all asset types
all_results = crew.discover_all_assets(
    asset_types=['etf', 'stock', 'crypto'],
    max_results_per_type=15
)
```text
#### APlusScoringTool

Tool for calculating A+ scores.

```pythonthon
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool

# Initialize scoring tool
scorer = APlusScoringTool()

# Score an ETF
etf_score = scorer.score_etf(
    symbol='VXUS',
    fundamental_data={
        'expense_ratio': 0.08,
        'aum': 45_000_000_000,
        'tracking_error': 0.0012,
        'history_years': 8
    }
)

# Score a stock
stock_score = scorer.score_stock(
    symbol='AAPL',
    fundamental_data={
        'roe': 0.28,
        'revenue_growth_5y': 0.12,
        'debt_to_equity': 0.15,
        'free_cash_flow': 95_000_000_000
    }
)
```text
#### MarketScreeningTool

Tool for screening large universes of investments.

```pythonthon
from finwiz.tools.market_screening_tool import MarketScreeningTool
from finwiz.schemas.screening_criteria import ETFScreeningCriteria

# Initialize screening tool
screener = MarketScreeningTool()

# Screen ETFs
criteria = ETFScreeningCriteria(
    max_expense_ratio=0.12,
    min_aum_billions=1.5,
    ucits_compliant=True
)

candidates = screener.screen_etfs(
    criteria=criteria,
    market_region='global',
    max_results=50
)
```text
### Async API

```pythonthon
import asyncio
from finwiz.crews.investment_discovery_crew import InvestmentDiscoveryCrew

async def discover_async():
    crew = InvestmentDiscoveryCrew()

    # Parallel discovery across asset types
    results = await asyncio.gather(
        crew.discover_etfs_async(),
        crew.discover_stocks_async(),
        crew.discover_crypto_async()
    )

    return {
        'etfs': results[0],
        'stocks': results[1],
        'crypto': results[2]
    }

# Run async discovery
results = asyncio.run(discover_async())
```text
## Data Schemas

### Core Models

#### InvestmentCandidate

```pythonthon
{
  "symbol": "string",
  "name": "string",
  "asset_type": "etf|stock|crypto",
  "current_price": "number",
  "market_cap": "number|null",
  "preliminary_score": "number", # 0.0 to 1.0
  "discovery_date": "datetime"
}
```text
#### APlusAnalysis

```pythonthon
{
  "candidate": "InvestmentCandidate",
  "fundamental_score": "number", # 0.0 to 1.0
  "technical_score": "number",   # 0.0 to 1.0
  "quality_score": "number",     # 0.0 to 1.0
  "risk_score": "number",        # 0.0 to 1.0
  "final_grade": "A+|A|A-|B+|B|B-|C+|C|C-|D|F",
  "confidence_level": "number",  # 0.0 to 1.0
  "rationale": ["string"]        # Array of reasons
}
```text
#### PortfolioImprovement

```pythonthon
{
  "current_holding": "string|null",
  "recommended_replacement": "InvestmentCandidate",
  "expected_grade_improvement": "number",
  "risk_impact": {
    "volatility_change": "number",
    "sharpe_improvement": "number",
    "max_drawdown_change": "number"
  },
  "cost_analysis": {
    "current_expense_ratio": "number",
    "new_expense_ratio": "number",
    "annual_savings": "number",
    "transaction_costs": "number"
  },
  "implementation_priority": "integer" # 1-5, 1=highest
}
```text
### Screening Criteria Schemas

#### ETFScreeningCriteria

```pythonthon
{
  "max_expense_ratio": "number",      # Default: 0.15
  "min_aum_billions": "number",       # Default: 1.0
  "max_tracking_error": "number",     # Default: 0.002
  "min_history_years": "integer",     # Default: 3
  "required_regions": ["string"],     # Optional
  "ucits_compliant": "boolean"        # Default: true
}
```text
#### StockScreeningCriteria

```pythonthon
{
  "min_roe": "number",                # Default: 0.20
  "min_revenue_growth": "number",     # Default: 0.15
  "max_debt_to_equity": "number",     # Default: 0.3
  "min_market_cap_billions": "number", # Default: 1.0
  "required_free_cash_flow": "boolean", # Default: true
  "min_profit_margin": "number"       # Default: 0.10
}
```text
#### CryptoScreeningCriteria

```pythonthon
{
  "min_market_cap_billions": "number",        # Default: 10.0
  "min_daily_volume_millions": "number",      # Default: 500.0
  "min_age_months": "integer",                # Default: 36
  "required_institutional_adoption": "boolean", # Default: true
  "max_volatility_90d": "number"              # Default: 1.0
}
```text
## Error Handling

### HTTP Status Codes

| Code | Description | Example |
|------|-------------|---------|
| 200 | Success | Discovery completed successfully |
| 400 | Bad Request | Invalid asset_type parameter |
| 401 | Unauthorized | Missing or invalid API token |
| 403 | Forbidden | Insufficient permissions for discovery |
| 404 | Not Found | Symbol not found for monitoring |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Discovery service error |
| 503 | Service Unavailable | External data provider unavailable |

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_ASSET_TYPE",
    "message": "Asset type 'bond' is not supported. Supported types: etf, stock, crypto",
    "details": {
      "supported_types": ["etf", "stock", "crypto"],
      "provided_type": "bond"
    },
    "timestamp": "2025-09-25T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```text
### Python Exception Classes

```pythonthon
# Base exceptions
class DiscoveryError(Exception):
    """Base exception for discovery operations."""
    pass

class InvalidAssetTypeError(DiscoveryError):
    """Raised when unsupported asset type is provided."""
    pass

class InsufficientDataError(DiscoveryError):
    """Raised when insufficient data for analysis."""
    pass

class ScoringError(DiscoveryError):
    """Raised when scoring calculation fails."""
    pass

class MarketDataError(DiscoveryError):
    """Raised when market data is unavailable."""
    pass

# Usage example
try:
    result = crew.discover_etfs()
except InvalidAssetTypeError as e:
    print(f"Invalid asset type: {e}")
except InsufficientDataError as e:
    print(f"Insufficient data: {e}")
```text
## Rate Limits

### API Rate Limits

| Endpoint | Rate Limit | Window |
|----------|------------|--------|
| `/discover/*` | 10 requests | 1 hour |
| `/monitor/*` | 100 requests | 1 hour |
| `/batch-discover` | 5 requests | 1 hour |
| `/criteria/*` | 50 requests | 1 hour |

### Rate Limit Headers

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1695636600
X-RateLimit-Window: 3600
```text
## Webhooks

### Webhook Events

Subscribe to webhook events for real-time updates:

#### grade_change

Triggered when an investment's grade changes.

```json
{
  "event": "grade_change",
  "timestamp": "2025-09-25T10:30:00Z",
  "data": {
    "symbol": "VXUS",
    "previous_grade": "A+",
    "new_grade": "A",
    "previous_score": 0.96,
    "new_score": 0.93,
    "reason": "Increased tracking error due to market volatility"
  }
}
```text
#### new_discovery

Triggered when new A+ opportunities are discovered.

```json
{
  "event": "new_discovery",
  "timestamp": "2025-09-25T10:30:00Z",
  "data": {
    "asset_type": "etf",
    "discoveries_count": 3,
    "top_discovery": {
      "symbol": "SCHD",
      "name": "Schwab US Dividend Equity ETF",
      "score": 0.98,
      "grade": "A+"
    }
  }
}
```text
### Webhook Configuration

```pythonthon
# Configure webhooks
webhook_config = {
    "url": "https://your-app.com/webhooks/finwiz",
    "events": ["grade_change", "new_discovery"],
    "secret": "your-webhook-secret"
}

# Register webhook
response = requests.post(
    "https://api.finwiz.ai/v1/webhooks",
    json=webhook_config,
    headers={"Authorization": "Bearer <your-token>"}
)
```text
## SDK Examples

### Python SDK

```pythonthon
from finwiz_sdk import FinWizClient

# Initialize client
client = FinWizClient(api_key="your-api-key")

# Discover A+ ETFs
etf_discoveries = client.discovery.discover_etfs(
    max_expense_ratio=0.10,
    min_aum_billions=2.0,
    regions=["US", "EU"]
)

# Monitor investment
status = client.discovery.monitor_investment("VXUS")

# Set up webhook
client.webhooks.create(
    url="https://your-app.com/webhook",
    events=["grade_change", "new_discovery"]
)
```text
### JavaScript SDK

```javascript
import { FinWizClient } from '@finwiz/sdk';

const client = new FinWizClient({
  apiKey: 'your-api-key'
});

// Discover A+ stocks
const stockDiscoveries = await client.discovery.discoverStocks({
  minRoe: 0.25,
  minMarketCapBillions: 5.0,
  maxResults: 20
});

// Monitor multiple investments
const statuses = await client.discovery.monitorInvestments([
  'AAPL', 'MSFT', 'GOOGL'
]);
```text
## Testing

### Mock API Server

For testing purposes, use the mock API server:

```bash
# Start mock server
npm install -g @finwiz/mock-api
finwiz-mock-api --port 3001

# Use mock server
export FINWIZ_API_BASE_URL=http://localhost:3001
```text
### Test Data

Sample test data is available at:

- ETF test data: `/test-data/etfs.json`
- Stock test data: `/test-data/stocks.json`
- Crypto test data: `/test-data/crypto.json`

---

For more information, see:

- [User Guide](investment_discovery_user_guide.md)
- [Developer Guide](investment_discovery_developer_guide.md)
- [API Status Page](https://status.finwiz.ai)
