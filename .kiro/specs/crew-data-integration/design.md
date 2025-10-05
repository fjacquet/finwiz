# Design Document

## Overview

The FinWiz system currently suffers from data integration issues where individual crews (Stock, ETF, Crypto, Investment Discovery) generate outputs that are not properly accessible to downstream crews, particularly the Report crew. This results in incomplete reports with missing SEC/EDGAR citations, unavailable market sentiment data, unvalidated tickers, and stale data integration.

This design implements a comprehensive **Crew Data Integration System** that establishes standardized data contracts, centralized data storage, automated data validation, and robust error handling to ensure all crew outputs are properly collected, validated, and made available to downstream crews.

## Architecture

### Core Components

#### 1. Data Integration Manager

A centralized service that orchestrates data flow between crews and manages the integration lifecycle.

**Key Responsibilities:**

- Coordinate crew execution order based on data dependencies
- Validate data contracts between crews
- Monitor data freshness and trigger refresh when needed
- Provide unified access to all crew outputs
- Handle graceful degradation when data is unavailable

#### 2. Standardized Data Contracts

Enhanced Pydantic schemas that define strict contracts for inter-crew communication.

**Key Features:**

- Metadata inclusion (timestamps, validation status, data lineage)
- Backward compatibility versioning
- Validation status tracking
- Source attribution and citations

#### 3. Centralized Data Store

A structured file-based storage system that maintains crew outputs with proper metadata and accessibility.

**Structure:**

```
output/
├── integration/
│   ├── metadata/
│   │   ├── crew_execution_log.json
│   │   ├── data_lineage.json
│   │   └── validation_status.json
│   ├── contracts/
│   │   ├── stock_output.json
│   │   ├── etf_output.json
│   │   ├── crypto_output.json
│   │   └── discovery_output.json
│   └── consolidated/
│       └── reporter_input.json
├── stock/
├── etf/
├── crypto/
├── discovery/
└── portfolio/
```

#### 4. Data Validation Pipeline

Automated validation system that ensures data quality and contract compliance.

**Components:**

- Schema validation using Pydantic models
- Data freshness checks
- Cross-crew data consistency validation
- Missing data detection and reporting

#### 5. Error Recovery System

Robust error handling that provides clear diagnostics and recovery options.

**Features:**

- Detailed error reporting with specific file paths
- Data staleness warnings and refresh suggestions
- Graceful degradation with partial data
- Recovery recommendations for common issues

## Components and Interfaces

### 1. CrewDataIntegrationManager

```python
class CrewDataIntegrationManager:
    """Central manager for crew data integration and coordination."""
    
    def __init__(self, output_dir: Path = Path("output")):
        self.output_dir = output_dir
        self.integration_dir = output_dir / "integration"
        self.metadata_dir = self.integration_dir / "metadata"
        self.contracts_dir = self.integration_dir / "contracts"
        self.consolidated_dir = self.integration_dir / "consolidated"
        
    async def coordinate_crew_execution(self, crews: List[CrewConfig]) -> ExecutionResult
    def validate_crew_output(self, crew_name: str, output_data: dict) -> ValidationResult
    def get_upstream_data(self, requesting_crew: str) -> UpstreamDataCollection
    def check_data_freshness(self, max_age_hours: int = 24) -> FreshnessReport
    def consolidate_reporter_input(self) -> ReporterInput
```

### 2. Enhanced Data Schemas

```python
class CrewOutputMetadata(BaseModel):
    """Metadata for all crew outputs."""
    crew_name: str
    execution_timestamp: datetime
    schema_version: int = 1
    validation_status: ValidationStatus
    data_sources: List[DataSource]
    dependencies_met: bool
    freshness_status: FreshnessStatus

class StockCrewOutput(BaseModel):
    """Enhanced stock crew output with integration metadata."""
    metadata: CrewOutputMetadata
    ten_k_insights: List[TenKInsight]
    validated_tickers: List[ValidatedTicker]
    market_sentiments: List[MarketSentiment]
    risk_assessments: List[RiskAssessmentStandardized]
    sec_citations: List[SECCitation]

class ETFCrewOutput(BaseModel):
    """Enhanced ETF crew output with integration metadata."""
    metadata: CrewOutputMetadata
    validated_etfs: List[ValidatedETF]
    factsheets: List[ETFFactsheet]
    holdings_analysis: List[ETFTopHolding]
    risk_assessments: List[RiskAssessmentStandardized]

class CryptoCrewOutput(BaseModel):
    """Enhanced crypto crew output with integration metadata."""
    metadata: CrewOutputMetadata
    validated_symbols: List[ValidatedCrypto]
    crypto_theses: List[CryptoThesis]
    risk_assessments: List[RiskAssessmentStandardized]
    market_analysis: List[CryptoMarketAnalysis]

class DiscoveryCrewOutput(BaseModel):
    """Enhanced discovery crew output with integration metadata."""
    metadata: CrewOutputMetadata
    a_plus_opportunities: APlusOpportunityCollection
    portfolio_improvements: List[PortfolioImprovement]
    optimization_results: List[OptimizationResult]
    validation_results: List[ValidationResult]
```

### 3. Data Access Layer

```python
class CrewDataAccessor:
    """Provides unified access to crew data with validation and error handling."""
    
    def __init__(self, integration_manager: CrewDataIntegrationManager):
        self.integration_manager = integration_manager
        
    def get_stock_data(self) -> Optional[StockCrewOutput]
    def get_etf_data(self) -> Optional[ETFCrewOutput]
    def get_crypto_data(self) -> Optional[CryptoCrewOutput]
    def get_discovery_data(self) -> Optional[DiscoveryCrewOutput]
    def get_consolidated_data(self) -> ReporterInput
    def check_data_availability(self) -> DataAvailabilityReport
```

### 4. Integration Middleware

```python
class CrewIntegrationMiddleware:
    """Middleware that intercepts crew outputs and ensures proper integration."""
    
    def pre_execution_hook(self, crew_name: str, inputs: dict) -> dict
    def post_execution_hook(self, crew_name: str, outputs: dict) -> dict
    def validate_dependencies(self, crew_name: str) -> DependencyValidationResult
    def store_crew_output(self, crew_name: str, output: BaseModel) -> StorageResult
```

## Data Models

### Core Integration Models

```python
class DataSource(BaseModel):
    """Information about data sources used by crews."""
    source_type: Literal["SEC_EDGAR", "YAHOO_FINANCE", "ALPHA_VANTAGE", "INTERNAL"]
    source_url: Optional[str]
    accessed_at: datetime
    data_quality: Literal["HIGH", "MEDIUM", "LOW"]

class ValidationStatus(BaseModel):
    """Validation status for crew outputs."""
    is_valid: bool
    validation_timestamp: datetime
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)

class FreshnessStatus(BaseModel):
    """Data freshness information."""
    is_fresh: bool
    age_hours: float
    max_age_hours: int = 24
    refresh_recommended: bool

class SECCitation(BaseModel):
    """Enhanced SEC citation with full provenance."""
    ticker: str
    filing_url: str
    filed_at: datetime
    section: str
    excerpt: str
    sec_citation: str
    extraction_timestamp: datetime
    validation_status: ValidationStatus

class ValidatedTicker(BaseModel):
    """Ticker validation result with metadata."""
    symbol: str
    is_valid: bool
    validation_source: str
    validation_timestamp: datetime
    market: Optional[str]
    sector: Optional[str]
    validation_errors: List[str] = Field(default_factory=list)

class APlusOpportunityCollection(BaseModel):
    """Collection of A+ opportunities with metadata."""
    etf_opportunities: List[str] = Field(default_factory=list)
    stock_opportunities: List[str] = Field(default_factory=list)
    crypto_opportunities: List[str] = Field(default_factory=list)
    discovery_summary: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    validation_timestamp: datetime
```

### Error Handling Models

```python
class IntegrationError(BaseModel):
    """Detailed error information for integration issues."""
    error_type: Literal["MISSING_DATA", "STALE_DATA", "VALIDATION_ERROR", "ACCESS_ERROR"]
    crew_name: str
    error_message: str
    expected_path: Optional[str]
    actual_path: Optional[str]
    recovery_suggestions: List[str]
    timestamp: datetime

class DataAvailabilityReport(BaseModel):
    """Report on data availability across all crews."""
    stock_available: bool
    etf_available: bool
    crypto_available: bool
    discovery_available: bool
    portfolio_available: bool
    missing_data: List[str]
    stale_data: List[str]
    integration_errors: List[IntegrationError]
    overall_status: Literal["COMPLETE", "PARTIAL", "INSUFFICIENT"]
```

## Error Handling

### 1. Data Staleness Detection

```python
class DataFreshnessChecker:
    """Monitors data freshness and triggers refresh when needed."""
    
    def check_file_freshness(self, file_path: Path, max_age_hours: int = 24) -> FreshnessStatus
    def get_stale_files(self) -> List[Path]
    def recommend_refresh_order(self) -> List[str]  # Crew execution order
    def generate_freshness_report(self) -> FreshnessReport
```

### 2. Missing Data Handling

```python
class MissingDataHandler:
    """Handles missing data scenarios with graceful degradation."""
    
    def detect_missing_data(self, required_data: List[str]) -> List[str]
    def provide_fallback_data(self, missing_data_type: str) -> Optional[dict]
    def generate_missing_data_warnings(self) -> List[str]
    def suggest_recovery_actions(self) -> List[str]
```

### 3. Validation Error Recovery

```python
class ValidationErrorRecovery:
    """Handles validation errors with recovery suggestions."""
    
    def analyze_validation_error(self, error: ValidationError) -> ErrorAnalysis
    def suggest_data_fixes(self, error: ValidationError) -> List[str]
    def attempt_data_repair(self, corrupted_data: dict) -> Optional[dict]
    def generate_error_report(self) -> ValidationErrorReport
```

## Testing Strategy

### 1. Unit Tests

**Data Integration Manager Tests:**

- Test crew coordination logic
- Test data validation pipeline
- Test error handling scenarios
- Test data freshness checking

**Schema Validation Tests:**

- Test enhanced Pydantic models
- Test backward compatibility
- Test validation error scenarios
- Test metadata handling

**Data Access Layer Tests:**

- Test data retrieval methods
- Test error handling for missing data
- Test graceful degradation
- Test data consolidation logic

### 2. Integration Tests

**End-to-End Data Flow Tests:**

- Test complete crew execution pipeline
- Test data propagation between crews
- Test report generation with integrated data
- Test error recovery scenarios

**Cross-Crew Communication Tests:**

- Test data contract compliance
- Test dependency resolution
- Test data freshness coordination
- Test validation status propagation

### 3. Performance Tests

**Data Processing Performance:**

- Test large dataset handling
- Test concurrent crew execution
- Test data consolidation performance
- Test memory usage optimization

**Error Recovery Performance:**

- Test error detection speed
- Test recovery action execution
- Test graceful degradation performance
- Test system resilience under load

### 4. Mock Strategy

**External Dependencies:**

- Mock file system operations
- Mock crew execution results
- Mock validation services
- Mock data source APIs

**Test Data Generation:**

- Generate valid crew outputs
- Generate invalid/corrupted data
- Generate stale data scenarios
- Generate missing data scenarios

## Implementation Phases

### Phase 1: Core Infrastructure

1. Implement CrewDataIntegrationManager
2. Create enhanced data schemas
3. Set up centralized data storage structure
4. Implement basic validation pipeline

### Phase 2: Data Access Layer

1. Implement CrewDataAccessor
2. Create integration middleware
3. Add data freshness checking
4. Implement error detection and reporting

### Phase 3: Enhanced Features

1. Add A+ opportunity integration
2. Implement SEC citation handling
3. Add market sentiment consolidation
4. Create ticker validation system

### Phase 4: Error Recovery

1. Implement missing data handlers
2. Add validation error recovery
3. Create comprehensive error reporting
4. Add recovery suggestion system

### Phase 5: Integration and Testing

1. Integrate with existing crews
2. Update Report crew to use new system
3. Add comprehensive test coverage
4. Performance optimization and monitoring
