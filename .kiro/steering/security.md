---
inclusion: always
---

# Security & Type Safety Standards

## Type Safety with mypy

FinWiz uses strict `mypy` configuration to catch bugs before runtime and improve code maintainability.

### Required Type Annotations

All public functions and methods must have complete type annotations:

```python
# ✅ CORRECT - Full type annotations
def analyze_stock(ticker: str, period: int = 365) -> StockAnalysis:
    """Analyze stock with specified lookback period."""
    return StockAnalysis(ticker=ticker, period=period)

# ✅ CORRECT - Explicit None return
def log_analysis(ticker: str) -> None:
    """Log analysis to file."""
    logger.info(f"Analyzing {ticker}")

# ❌ INCORRECT - Missing return type
def analyze_stock(ticker: str):
    return StockAnalysis(ticker=ticker)
```

### Type Annotation Rules

- **Return types required**: All functions must specify return type, use `-> None` if no return value
- **Parameter types required**: All parameters must have type hints
- **Complex types**: Use `typing` module for `Optional`, `Union`, `List`, `Dict`, etc.
- **Type stubs**: Prefer type stubs for third-party libraries without types
- **Last resort**: Use `# type: ignore` only when necessary, with explanatory comment

### Benefits

- **Bug prevention**: Catch `TypeError` and `AttributeError` before runtime
- **Self-documenting**: Function signatures serve as always-current documentation
- **IDE support**: Better autocomplete, navigation, and error detection
- **Safe refactoring**: Type checker identifies all affected code when changing interfaces

## API Key Security

### Environment Variables (Required)

All API keys must be stored in environment variables, never hardcoded:

```python
# ✅ CORRECT - Load from environment
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

# ❌ INCORRECT - Hardcoded key
api_key = "sk-proj-abc123..."
```

### Required API Keys

- `OPENAI_API_KEY` - OpenAI API access
- `SERPER_API_KEY` - Serper search API
- `FIRECRAWL_API_KEY` - Firecrawl web scraping
- `ALPHA_VANTAGE_API_KEY` - Alpha Vantage financial data
- `TWELVE_DATA_API_KEY` - Twelve Data market data
- `PERPLEXITY_API_KEY` - Perplexity search API

### Logging Security

Never log sensitive information:

```python
# ✅ CORRECT - Mask sensitive data
logger.info(f"API call with key: {api_key[:8]}...")

# ❌ INCORRECT - Exposes full key
logger.info(f"API call with key: {api_key}")
```

## Input Validation

### Pydantic Models (Required)

All external inputs must be validated using Pydantic v2 strict models:

```python
from pydantic import BaseModel, Field, field_validator

class TickerInput(BaseModel):
    """Validated ticker input."""
    symbol: str = Field(..., pattern=r'^[A-Z]{1,5}$', description="Stock ticker")
    
    model_config = {
        "str_strip_whitespace": True,
        "str_upper": True,
        "extra": "forbid"  # Reject unknown fields
    }
    
    @field_validator('symbol')
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not v.isalpha():
            raise ValueError('Ticker must contain only letters')
        return v.upper()
```

### Validation Rules

- **Strict mode**: Use `extra='forbid'` to reject unknown fields
- **Field validation**: Use `Field()` with constraints (pattern, min_length, ge, le)
- **Custom validators**: Use `@field_validator` for complex validation logic
- **Sanitization**: Strip whitespace, normalize case, remove special characters
- **Error messages**: Provide clear, actionable error messages

## Data Privacy

### Personal Financial Information

Never log or expose personal financial data:

```python
# ✅ CORRECT - Anonymized logging
logger.info(f"Analyzing portfolio with {len(holdings)} holdings")

# ❌ INCORRECT - Exposes personal data
logger.info(f"Analyzing portfolio: {holdings}")
```

### Error Messages

Provide generic error messages to users, detailed logs internally:

```python
# ✅ CORRECT - Generic user message, detailed internal log
try:
    result = api_call(ticker)
except Exception as e:
    logger.error(f"API call failed for {ticker}: {e}", exc_info=True)
    raise ValueError("Unable to fetch data. Please try again later.")

# ❌ INCORRECT - Exposes internal details
except Exception as e:
    raise ValueError(f"API call to {api_url} failed: {e}")
```

## Rate Limiting & API Safety

### Implement Rate Limiting

Respect API rate limits to avoid service disruption:

```python
from finwiz.utils.rate_limiter import RateLimiter

# Configure rate limiter
limiter = RateLimiter(max_calls=20, period=60)  # 20 calls per minute

@limiter.limit
async def fetch_stock_data(ticker: str) -> dict:
    """Fetch stock data with rate limiting."""
    return await api_client.get(f"/stock/{ticker}")
```

### Timeout Configuration

Always set timeouts for external API calls:

```python
import httpx

# ✅ CORRECT - Explicit timeout
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.get(url)

# ❌ INCORRECT - No timeout (can hang indefinitely)
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

## Dependency Security

### Regular Updates

Keep dependencies updated to patch security vulnerabilities:

```bash
# Update dependencies
uv sync --upgrade

# Check for security vulnerabilities
uv pip list --outdated
```

### Trusted Sources

Only use dependencies from trusted sources (PyPI, verified publishers).

## Security Checklist

Before committing code:

- [ ] All API keys in environment variables
- [ ] No sensitive data in logs
- [ ] All inputs validated with Pydantic models
- [ ] All functions have type annotations
- [ ] Rate limiting configured for API calls
- [ ] Timeouts set for external requests
- [ ] Error messages don't expose internal details
- [ ] No hardcoded credentials or secrets
- [ ] Dependencies are up to date
- [ ] `mypy` passes with no errors
