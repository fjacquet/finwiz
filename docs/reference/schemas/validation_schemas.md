# Validation Schemas

Schemas for input validation, error handling, and data quality assurance.

## ValidatedTicker

Validated ticker symbol with metadata and quality checks.

### Schema Definition

```python
class ValidatedTicker(BaseModel):
    symbol: str = Field(..., description="Validated ticker symbol")
    original_input: str = Field(..., description="Original user input")
    asset_class: Optional[str] = Field(None, description="Detected asset class")
    
    # Validation results
    is_valid: bool = Field(..., description="Whether ticker is valid")
    validation_source: str = Field(..., description="Source used for validation")
    
    # Market data
    exchange: Optional[str] = Field(None, description="Primary exchange")
    currency: Optional[str] = Field(None, description="Trading currency")
    market_cap: Optional[float] = Field(None, ge=0, description="Market capitalization")
    
    # Quality metrics
    data_availability: float = Field(..., ge=0.0, le=1.0, description="Data availability score")
    liquidity_score: float = Field(..., ge=0.0, le=1.0, description="Liquidity assessment")
    
    # Metadata
    company_name: Optional[str] = Field(None, description="Company/asset name")
    sector: Optional[str] = Field(None, description="Sector classification")
    industry: Optional[str] = Field(None, description="Industry classification")
    
    # Validation timestamp
    validated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
        "str_upper": True  # Automatically uppercase ticker symbols
    }
    
    @field_validator('symbol')
    @classmethod
    def validate_ticker_format(cls, v: str) -> str:
        # Remove common separators and validate
        clean_symbol = v.replace('-', '').replace('.', '')
        if not clean_symbol.isalnum():
            raise ValueError('Ticker must contain only alphanumeric characters, hyphens, and dots')
        if len(v) > 10:
            raise ValueError('Ticker symbol too long')
        return v.upper()
```

### Example

```json
{
  "symbol": "AAPL",
  "original_input": "aapl",
  "asset_class": "stock",
  "is_valid": true,
  "validation_source": "Yahoo Finance",
  "exchange": "NASDAQ",
  "currency": "USD",
  "market_cap": 3000000000000,
  "data_availability": 0.98,
  "liquidity_score": 1.0,
  "company_name": "Apple Inc.",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "validated_at": "2025-01-15T10:30:00Z"
}
```

## ValidationResult

Comprehensive validation result with error details and suggestions.

### Schema Definition

```python
class ValidationError(BaseModel):
    field_path: str = Field(..., description="Path to the field with error")
    message: str = Field(..., description="Human-readable error message")
    error_type: str = Field(..., description="Error type classification")
    input_value: Any = Field(..., description="The invalid input value")
    suggested_fix: Optional[str] = Field(None, description="Suggested correction")
    
    model_config = {"extra": "forbid"}

class ValidationResult(BaseModel):
    is_valid: bool = Field(..., description="Overall validation status")
    validation_timestamp: datetime = Field(default_factory=datetime.now)
    
    # Validation details
    schema_name: str = Field(..., description="Schema being validated against")
    schema_version: str = Field(default="1.0", description="Schema version")
    
    # Results
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationError] = Field(default_factory=list)
    
    # Processed data
    sanitized_data: Optional[Dict[str, Any]] = Field(None, description="Cleaned/sanitized data")
    original_data: Dict[str, Any] = Field(..., description="Original input data")
    
    # Quality metrics
    data_completeness: float = Field(..., ge=0.0, le=1.0, description="Completeness score")
    data_quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score")
    
    # Validation context
    validation_mode: Literal["strict", "lenient", "warn_only"] = Field(default="strict")
    validation_rules_applied: List[str] = Field(default_factory=list)
    
    model_config = {"extra": "forbid"}
    
    @property
    def error_count(self) -> int:
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        return len(self.warnings)
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
```

### Example

```json
{
  "is_valid": false,
  "validation_timestamp": "2025-01-15T10:30:00Z",
  "schema_name": "TenKInsight",
  "schema_version": "1.0",
  "errors": [
    {
      "field_path": "ticker",
      "message": "Ticker symbol format is invalid",
      "error_type": "FORMAT_ERROR",
      "input_value": "apple123",
      "suggested_fix": "Use standard ticker format like 'AAPL'"
    }
  ],
  "warnings": [
    {
      "field_path": "confidence_level",
      "message": "Confidence level is unusually low",
      "error_type": "QUALITY_WARNING",
      "input_value": 0.3,
      "suggested_fix": "Consider additional analysis to improve confidence"
    }
  ],
  "sanitized_data": {
    "ticker": "AAPL",
    "confidence_level": 0.85
  },
  "original_data": {
    "ticker": "apple123",
    "confidence_level": 0.3
  },
  "data_completeness": 0.85,
  "data_quality_score": 0.75,
  "validation_mode": "strict",
  "validation_rules_applied": [
    "ticker_format_validation",
    "confidence_range_validation",
    "required_fields_validation"
  ]
}
```

## ReporterInput

Input validation for report generation with template and data validation.

### Schema Definition

```python
class ReporterInput(BaseModel):
    # Report configuration
    report_type: Literal["stock_analysis", "etf_analysis", "crypto_analysis", "portfolio_review"]
    template_name: str = Field(..., description="Report template to use")
    output_format: Literal["html", "pdf", "json"] = Field(default="html")
    
    # Data inputs
    analysis_data: Dict[str, Any] = Field(..., description="Analysis results to include")
    portfolio_data: Optional[Dict[str, Any]] = Field(None, description="Portfolio context")
    
    # Report customization
    include_charts: bool = Field(default=True)
    include_risk_details: bool = Field(default=True)
    include_data_sources: bool = Field(default=True)
    language: str = Field(default="en", description="Report language")
    
    # Quality requirements
    min_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    require_recent_data: bool = Field(default=True)
    max_data_age_hours: int = Field(default=24, ge=1)
    
    # Validation settings
    strict_validation: bool = Field(default=True)
    allow_partial_data: bool = Field(default=False)
    
    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True
    }
    
    @field_validator('analysis_data')
    @classmethod
    def validate_analysis_data_structure(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ['ticker', 'recommendation', 'confidence_level']
        missing_fields = [field for field in required_fields if field not in v]
        if missing_fields:
            raise ValueError(f'Missing required analysis fields: {missing_fields}')
        return v
```

### Example

```json
{
  "report_type": "stock_analysis",
  "template_name": "comprehensive_stock_report",
  "output_format": "html",
  "analysis_data": {
    "ticker": "AAPL",
    "recommendation": "BUY",
    "confidence_level": 0.85,
    "price_target": 180.00
  },
  "portfolio_data": {
    "current_allocation": 0.15,
    "target_allocation": 0.20
  },
  "include_charts": true,
  "include_risk_details": true,
  "include_data_sources": true,
  "language": "en",
  "min_confidence_threshold": 0.7,
  "require_recent_data": true,
  "max_data_age_hours": 12,
  "strict_validation": true,
  "allow_partial_data": false
}
```

## DataQualityAssessment

Assessment of data quality for analysis inputs.

### Schema Definition

```python
class DataQualityIssue(BaseModel):
    issue_type: Literal["MISSING_DATA", "STALE_DATA", "INCONSISTENT_DATA", "LOW_CONFIDENCE", "SOURCE_UNAVAILABLE"]
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    field_path: str = Field(..., description="Path to affected field")
    description: str = Field(..., description="Issue description")
    impact: str = Field(..., description="Impact on analysis")
    suggested_action: Optional[str] = Field(None, description="Recommended action")

class DataQualityAssessment(BaseModel):
    assessment_timestamp: datetime = Field(default_factory=datetime.now)
    data_source: str = Field(..., description="Source of data being assessed")
    
    # Overall quality metrics
    overall_quality_score: float = Field(..., ge=0.0, le=1.0)
    completeness_score: float = Field(..., ge=0.0, le=1.0)
    freshness_score: float = Field(..., ge=0.0, le=1.0)
    accuracy_score: float = Field(..., ge=0.0, le=1.0)
    consistency_score: float = Field(..., ge=0.0, le=1.0)
    
    # Data characteristics
    total_fields: int = Field(..., ge=0)
    populated_fields: int = Field(..., ge=0)
    missing_fields: int = Field(..., ge=0)
    
    # Freshness analysis
    newest_data_age: Optional[timedelta] = None
    oldest_data_age: Optional[timedelta] = None
    avg_data_age: Optional[timedelta] = None
    
    # Quality issues
    issues: List[DataQualityIssue] = Field(default_factory=list)
    critical_issues: int = Field(default=0, ge=0)
    
    # Recommendations
    usable_for_analysis: bool = Field(..., description="Whether data is suitable for analysis")
    confidence_impact: float = Field(..., ge=0.0, le=1.0, description="Impact on analysis confidence")
    recommended_actions: List[str] = Field(default_factory=list)
    
    model_config = {"extra": "forbid"}
    
    @property
    def completion_rate(self) -> float:
        if self.total_fields == 0:
            return 0.0
        return self.populated_fields / self.total_fields
    
    @property
    def has_critical_issues(self) -> bool:
        return self.critical_issues > 0
```

## Validation Utilities

### Custom Validators

```python
class TickerValidator:
    """Utility class for ticker validation"""
    
    @staticmethod
    def validate_format(ticker: str) -> bool:
        """Validate ticker format"""
        if not ticker:
            return False
        # Allow alphanumeric, hyphens, and dots
        clean_ticker = ticker.replace('-', '').replace('.', '')
        return clean_ticker.isalnum() and len(ticker) <= 10
    
    @staticmethod
    def normalize(ticker: str) -> str:
        """Normalize ticker format"""
        return ticker.strip().upper()
    
    @staticmethod
    def detect_asset_class(ticker: str) -> Optional[str]:
        """Detect asset class from ticker format"""
        if ticker.endswith('-USD') or ticker.endswith('USDT'):
            return "crypto"
        elif any(etf_suffix in ticker for etf_suffix in ['ETF', 'SPDR', 'VTI', 'QQQ']):
            return "etf"
        else:
            return "stock"

class ConfidenceValidator:
    """Utility class for confidence validation"""
    
    @staticmethod
    def validate_range(confidence: float) -> bool:
        """Validate confidence is in valid range"""
        return 0.0 <= confidence <= 1.0
    
    @staticmethod
    def assess_quality(confidence: float) -> str:
        """Assess confidence quality"""
        if confidence >= 0.8:
            return "HIGH"
        elif confidence >= 0.6:
            return "MEDIUM"
        elif confidence >= 0.4:
            return "LOW"
        else:
            return "VERY_LOW"
```

## Usage Examples

### Ticker Validation

```python
from finwiz.schemas.validation import ValidatedTicker

# Validate ticker
try:
    validated = ValidatedTicker(
        symbol="AAPL",
        original_input="aapl",
        is_valid=True,
        validation_source="Yahoo Finance",
        data_availability=0.98,
        liquidity_score=1.0
    )
    print(f"Validated ticker: {validated.symbol}")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Validation Result Processing

```python
from finwiz.schemas.validation import ValidationResult, ValidationError

# Create validation result
result = ValidationResult(
    is_valid=False,
    schema_name="TenKInsight",
    errors=[
        ValidationError(
            field_path="ticker",
            message="Invalid ticker format",
            error_type="FORMAT_ERROR",
            input_value="invalid123",
            suggested_fix="Use valid ticker symbol"
        )
    ],
    original_data={"ticker": "invalid123"},
    data_completeness=0.5,
    data_quality_score=0.3
)

# Process results
if result.has_errors:
    print(f"Validation failed with {result.error_count} errors:")
    for error in result.errors:
        print(f"  - {error.field_path}: {error.message}")
        if error.suggested_fix:
            print(f"    Suggestion: {error.suggested_fix}")
```

### Data Quality Assessment

```python
from finwiz.schemas.validation import DataQualityAssessment, DataQualityIssue

# Assess data quality
assessment = DataQualityAssessment(
    data_source="Yahoo Finance",
    overall_quality_score=0.85,
    completeness_score=0.90,
    freshness_score=0.95,
    accuracy_score=0.80,
    consistency_score=0.85,
    total_fields=20,
    populated_fields=18,
    missing_fields=2,
    issues=[
        DataQualityIssue(
            issue_type="MISSING_DATA",
            severity="MEDIUM",
            field_path="dividend_yield",
            description="Dividend yield data not available",
            impact="Cannot assess dividend income potential",
            suggested_action="Use alternative data source or estimate"
        )
    ],
    usable_for_analysis=True,
    confidence_impact=0.1
)

print(f"Data quality score: {assessment.overall_quality_score}")
print(f"Usable for analysis: {assessment.usable_for_analysis}")
```

## Integration with Validation Manager

```python
from finwiz.validation import get_validation_manager

# Get validation manager
manager = get_validation_manager()

# Validate crew output
result = manager.validate_crew_output(
    data=analysis_data,
    asset_class="stock",
    analysis_type="ten_k_insight"
)

if result.is_valid:
    # Use sanitized data
    clean_data = result.sanitized_data
    analysis = TenKInsight.model_validate(clean_data)
else:
    # Handle validation errors
    for error in result.errors:
        logger.error(f"Validation error: {error.message}")
```

## Related Documentation

- [Analysis Schemas](analysis_schemas.md) - Schemas being validated
- [Portfolio Schemas](portfolio_schemas.md) - Portfolio validation
- [Discovery Schemas](discovery_schemas.md) - Discovery validation
- [Schema Relationships](relationships.md) - How validation fits in the system
