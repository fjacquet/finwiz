---
inclusion: always
---

# FinWiz Security Standards

## Credential Management (Critical)

### Environment Variables
- **Required Keys**: `OPENAI_API_KEY`, `SERPER_API_KEY`, `FIRECRAWL_API_KEY`, `ALPHA_VANTAGE_API_KEY`
- **Storage**: Use `.env` file for local development (never commit to git)
- **Validation**: Check all required API keys at application startup
- **Error Handling**: Fail fast with clear messages if keys are missing

### Code Rules
```python
# ✅ Correct - Use environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not found")

# ❌ Never do this - Hard-coded secrets
api_key = "sk-1234567890abcdef"  # NEVER
```

## Input Validation & Data Protection

### Financial Data Security
- **Pydantic Validation**: All inputs must use strict Pydantic models
- **Sanitization**: Strip/validate all ticker symbols, amounts, dates
- **PII Handling**: Never log personal financial information
- **Data Sources**: Always validate external API responses before processing

### Schema Enforcement
```python
from pydantic import BaseModel, Field, validator

class SecureTickerInput(BaseModel):
    symbol: str = Field(..., regex=r'^[A-Z]{1,5}$')
    
    @validator('symbol')
    def sanitize_ticker(cls, v):
        return v.upper().strip()
```

## Logging & Error Handling

### Security Logging Rules
- **Never Log**: API keys, tokens, personal data, full error traces in production
- **Log Structure**: Use structured logging with sanitized data only
- **Error Messages**: Generic user-facing messages, detailed logs for debugging

```python
# ✅ Secure logging
logger.info("Stock analysis completed", extra={"ticker": ticker, "status": "success"})

# ❌ Insecure logging  
logger.info(f"API call with key {api_key} failed: {full_error}")
```

## External API Security

### API Call Standards
- **Timeout Limits**: Set reasonable timeouts for all external calls
- **Rate Limiting**: Implement backoff strategies for API limits
- **SSL/TLS**: Verify certificates for all HTTPS requests
- **Response Validation**: Validate all external API responses before use

### Error Recovery
```python
async def secure_api_call(url: str, headers: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError:
        logger.warning("API request failed", extra={"url": url})
        raise APIConnectionError("External service unavailable")
```

## Dependency Security

### Package Management
- **Lock Files**: Always commit `uv.lock` to ensure reproducible builds
- **Updates**: Regular security updates via `uv sync --upgrade`
- **Scanning**: Use `safety check` or similar tools for vulnerability scanning
- **Minimal Dependencies**: Only include necessary packages

## Testing Security

### Mock External Services
- **API Mocking**: Never make real API calls in tests
- **Credential Isolation**: Use fake credentials in test environments
- **Data Sanitization**: Ensure test data contains no real PII

```python
def test_stock_analysis_security(mocker):
    # Mock external API to prevent real calls
    mock_api = mocker.patch('finwiz.tools.yahoo_finance_tool.get_stock_data')
    mock_api.return_value = {'symbol': 'TEST', 'price': 100.0}
    
    # Test with sanitized inputs only
    result = analyze_stock('TEST')
    assert 'TEST' in result.symbol
```

## File System Security

### Safe File Operations
- **Path Validation**: Validate all file paths to prevent directory traversal
- **Permissions**: Use minimal file permissions (read-only when possible)
- **Cleanup**: Always clean up temporary files and close file handles
- **Output Directory**: Restrict file writes to designated output directories only

```python
from pathlib import Path

def safe_file_write(filename: str, content: str) -> None:
    # Validate filename to prevent path traversal
    safe_path = Path("output") / Path(filename).name
    if not safe_path.is_relative_to(Path("output")):
        raise SecurityError("Invalid file path")
    
    safe_path.write_text(content, encoding="utf-8")
```