# CrewAI Feature Usage Guide

## Overview

This guide documents the proper usage of CrewAI features within FinWiz to ensure consistent, high-quality financial analysis across all crews. It establishes patterns for tool assignment, output validation, performance optimization, and configuration management.

## Table of Contents

1. [CrewAI Configuration Patterns](#crewai-configuration-patterns)
2. [Tool Assignment Guidelines](#tool-assignment-guidelines)
3. [Output Validation with Pydantic](#output-validation-with-pydantic)
4. [Performance Optimization](#performance-optimization)
5. [Error Handling and Validation](#error-handling-and-validation)
6. [Troubleshooting Guide](#troubleshooting-guide)

## CrewAI Configuration Patterns

### Standard Crew Structure

All FinWiz crews must follow this standardized structure:

```
src/finwiz/crews/{crew_name}/
├── {crew_name}.py          # @agent, @task, @crew decorators
└── config/
    ├── agents.yaml         # Agent configurations  
    └── tasks.yaml          # Task definitions
```

### Agent Configuration with Proper Tools

```python
@agent
def stock_analyst(self) -> Agent:
    return Agent(
        config=self.agents_config["stock_analyst"],
        tools=[
            # Essential analysis tools (REQUIRED)
            get_quantitative_analysis_tool(asset_class="stock"),
            enhanced_sec_tool,
            ticker_validation_tool,
            
            # RAG tools for knowledge management (REQUIRED)
            *get_rag_tools(),
            
            # Asset-specific tools
            yahoo_finance_ticker_tool,
            yahoo_finance_history_tool,
            
            # Research tools
            serper_search_tool,
            firecrawl_scrape_tool,
        ],
        verbose=True
    )
```

### Task Configuration with CrewAI Features

```yaml
# Example task configuration using CrewAI output validation
stock_analysis_task:
  description: "Analyze stock with quantitative metrics and risk assessment"
  expected_output: "Structured analysis with risk assessment and technical indicators"
  output_pydantic: "TenKInsight"  # Use existing FinWiz schema
  output_json: true               # Generate machine-readable appendix
  agent: stock_analyst
  async_execution: true           # Enable for I/O-bound tasks
  depends_on: 
    - ticker_validation_task      # Ensure proper task sequencing
```

### Crew Configuration with Performance Settings

```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        verbose=True,
        
        # Performance optimization (REQUIRED)
        respect_context_window=True,
        max_rpm=20,
        
        # Use existing FinWiz validation
        # Note: Final task must be synchronous per CrewAI requirements
    )
```

## Tool Assignment Guidelines

### Essential Tools by Crew Type

#### Stock Crew (REQUIRED Tools)

- `QuantitativeAnalysisTool(asset_class="stock")`
- `EnhancedSECAnalysisTool` (for 10-K extraction)
- `TickerValidationTool`
- `StandardizedSentimentTool`
- RAG tools (`get_rag_tools()`)

#### ETF Crew (REQUIRED Tools)

- `QuantitativeAnalysisTool(asset_class="etf")`
- `EnhancedETFAnalysisTool` (for factsheet extraction)
- `TickerValidationTool`
- `StandardizedSentimentTool`
- RAG tools (`get_rag_tools()`)

#### Crypto Crew (REQUIRED Tools)

- `QuantitativeAnalysisTool(asset_class="crypto")`
- `EnhancedCryptoAnalysisTool`
- `CoinMarketCapTool`
- `TickerValidationTool`
- RAG tools (`get_rag_tools()`)

#### Portfolio Rebalancing Crew (REQUIRED Tools)

- `PortfolioRebalancingTool`
- `PortfolioPriceService`
- `QuantitativeAnalysisTool(asset_class="portfolio")`
- RAG tools (`get_rag_tools()`)

#### Report Crew (SPECIAL RESTRICTIONS)

- **Investment Reporter Agent**: EMPTY tools list (no external calls)
- **Translation Agent**: EMPTY tools list (consumes upstream context only)
- Uses `ToolRestrictionValidator` for compliance

### Tool Factory Pattern

Use tool factories for consistent tool configuration:

```python
def get_stock_analysis_tools() -> list:
    """Return curated tool set for stock analysis."""
    return [
        get_quantitative_analysis_tool(asset_class="stock"),
        enhanced_sec_tool,
        ticker_validation_tool,
        *get_rag_tools(),
        yahoo_finance_ticker_tool,
        yahoo_finance_history_tool,
        serper_search_tool,
    ]
```

## Output Validation with Pydantic

### Using CrewAI's Built-in Output Validation

CrewAI provides native Pydantic integration for output validation. Use existing FinWiz schemas:

```yaml
# Task configuration with output validation
risk_assessment_task:
  description: "Assess investment risks using standardized methodology"
  expected_output: "Standardized risk assessment with 0-5 scale scoring"
  output_pydantic: "RiskAssessmentStandardized"  # Existing FinWiz schema
  output_json: true
  agent: risk_analyst
```

### Required FinWiz Schemas by Crew

#### Stock Crew Schemas

- `TenKInsight` - SEC filing analysis
- `MarketSentiment` - Sentiment analysis results
- `RiskAssessmentStandardized` - Risk scoring (0-5 scale)

#### ETF Crew Schemas

- `ETFFactsheet` - ETF analysis results
- `ETFTopHolding` - Holdings analysis
- `RiskAssessmentStandardized` - Risk scoring (0-5 scale)

#### Crypto Crew Schemas

- `CryptoThesis` - Cryptocurrency analysis
- `RiskAssessmentStandardized` - Risk scoring (0-5 scale)

#### Portfolio Rebalancing Crew Schemas

- `PortfolioReview` - Portfolio analysis results
- `RiskAssessmentStandardized` - Risk scoring (0-5 scale)

### Schema Validation Example

```python
from finwiz.schemas.stock import TenKInsight
from finwiz.schemas.common import RiskAssessmentStandardized

# CrewAI automatically validates against these schemas when output_pydantic is specified
# No additional validation code needed - CrewAI handles it natively
```

## Performance Optimization

### Async Execution Guidelines

Enable `async_execution=True` for I/O-bound tasks that can run in parallel:

```yaml
# Parallel I/O-bound tasks
market_analysis_task:
  async_execution: true  # Can run in parallel
  
technical_analysis_task:
  async_execution: true  # Can run in parallel
  
# Final task must be synchronous (CrewAI requirement)
final_report_task:
  async_execution: false  # MUST be synchronous
  depends_on:
    - market_analysis_task
    - technical_analysis_task
```

### Crew-Level Performance Settings

```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        
        # Performance optimization
        respect_context_window=True,  # Manage token limits
        max_rpm=20,                   # Rate limiting
        verbose=True,                 # Debugging support
    )
```

### Task Dependencies

Use `depends_on` for proper task sequencing:

```yaml
validation_task:
  description: "Validate ticker symbols"
  agent: validator
  
analysis_task:
  description: "Perform detailed analysis"
  agent: analyst
  depends_on:
    - validation_task  # Ensures validation completes first
  
report_task:
  description: "Generate final report"
  agent: reporter
  async_execution: false  # Final task must be synchronous
  depends_on:
    - analysis_task
```

## Error Handling and Validation

### CrewAI Built-in Error Handling

Leverage CrewAI's native error handling features:

```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        
        # Error handling configuration
        max_retries=3,                # Automatic retry on failures
        respect_context_window=True,  # Handle token limit errors
        
        # Use existing FinWiz validation systems
        # ToolRestrictionValidator, ConfigurationManager, etc.
    )
```

### Integration with FinWiz Validation Systems

```python
# Use existing FinWiz validation patterns
from finwiz.validation.tool_restrictions import ToolRestrictionValidator
from finwiz.utils.configuration_manager import ConfigurationManager

class ReportCrew(CrewBase):
    def __init__(self):
        super().__init__()
        
        # Integrate with existing validation
        self.tool_validator = ToolRestrictionValidator()
        self.config_manager = ConfigurationManager()
        
    @agent
    def investment_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_reporter"],
            tools=[],  # EMPTY - enforced by ToolRestrictionValidator
            verbose=True
        )
```

### Output Validation Patterns

```yaml
# Use CrewAI's output_pydantic for automatic validation
analysis_task:
  output_pydantic: "TenKInsight"
  output_json: true
  
# CrewAI will automatically:
# 1. Validate output against TenKInsight schema
# 2. Generate structured JSON appendix
# 3. Provide validation error messages
# 4. Retry on validation failures (if configured)
```

## Troubleshooting Guide

### Common CrewAI Configuration Issues

#### Issue: Agent Missing Required Tools

**Symptoms**: Analysis lacks quantitative metrics, risk assessment, or validation
**Solution**: Verify agent tool list includes all required tools for asset class

```python
# Check agent configuration
@agent
def stock_analyst(self) -> Agent:
    return Agent(
        config=self.agents_config["stock_analyst"],
        tools=[
            get_quantitative_analysis_tool(asset_class="stock"),  # REQUIRED
            enhanced_sec_tool,                                    # REQUIRED
            ticker_validation_tool,                               # REQUIRED
            *get_rag_tools(),                                     # REQUIRED
        ]
    )
```

#### Issue: Output Validation Failures

**Symptoms**: CrewAI reports schema validation errors
**Solution**: Ensure task uses correct `output_pydantic` schema

```yaml
# Correct schema specification
stock_analysis_task:
  output_pydantic: "TenKInsight"  # Must match existing FinWiz schema
  output_json: true
```

#### Issue: Final Task Async Execution Error

**Symptoms**: CrewAI fails with "final task cannot be async" error
**Solution**: Ensure final task has `async_execution: false`

```yaml
final_report_task:
  async_execution: false  # REQUIRED for final task
  depends_on:
    - all_previous_tasks
```

#### Issue: Tool Restriction Violations

**Symptoms**: Report crew agents making external API calls
**Solution**: Verify empty tools list and ToolRestrictionValidator integration

```python
@agent
def investment_reporter(self) -> Agent:
    return Agent(
        config=self.agents_config["investment_reporter"],
        tools=[],  # MUST be empty
        verbose=True
    )
```

#### Issue: Missing Translation Tasks

**Symptoms**: Reports not available in French
**Solution**: Add translation task with proper configuration

```yaml
translation_task:
  description: "Translate report to French preserving HTML structure"
  expected_output: "French translation with preserved HTML formatting"
  agent: translator
  tools: []  # Translation agent has no tools
  depends_on:
    - final_report_task
```

### Performance Issues

#### Issue: Slow Execution Times

**Solutions**:

1. Enable `async_execution=true` for I/O-bound tasks
2. Configure appropriate `max_rpm` settings
3. Use `respect_context_window=true` to manage token limits

#### Issue: Rate Limiting Errors

**Solutions**:

1. Reduce `max_rpm` setting
2. Implement exponential backoff in tools
3. Use caching for expensive operations

### Validation Issues

#### Issue: Schema Compliance Failures

**Solutions**:

1. Verify Pydantic schema matches task output requirements
2. Use `output_json: true` for machine-readable appendices
3. Check field types and validation rules

#### Issue: Risk Assessment Inconsistencies

**Solutions**:

1. Ensure all crews use `RiskAssessmentStandardized` schema
2. Verify 0-5 scale scoring methodology
3. Use `StandardizedRiskScoringTool` for consistency

### Configuration Validation Checklist

Before deploying crew changes, verify:

- [ ] All agents have required tools for their asset class
- [ ] Tasks use appropriate `output_pydantic` schemas
- [ ] Final task has `async_execution: false`
- [ ] Report crew agents have empty tools lists
- [ ] Translation tasks are present where required
- [ ] Performance settings are configured (`max_rpm`, `respect_context_window`)
- [ ] Task dependencies are properly specified with `depends_on`
- [ ] All crews generate `RiskAssessmentStandardized` objects

## Best Practices Summary

1. **Use Configuration-First Approach**: Define agents and tasks in YAML, use Python only for tool wiring
2. **Leverage CrewAI Native Features**: Use `output_pydantic`, `async_execution`, and `depends_on` rather than custom logic
3. **Follow Tool Assignment Guidelines**: Ensure all crews have required tools for their asset class
4. **Maintain Schema Compliance**: Use existing FinWiz schemas with CrewAI's built-in validation
5. **Optimize Performance**: Enable async execution for I/O-bound tasks, configure rate limiting
6. **Integrate with FinWiz Systems**: Use existing validation, configuration, and error handling patterns
7. **Test Configuration Changes**: Verify no regressions in existing test suite
8. **Document Deviations**: Clearly document any deviations from standard patterns with rationale

This guide ensures consistent, high-quality CrewAI feature usage across all FinWiz crews while maintaining compatibility with existing systems and patterns.
