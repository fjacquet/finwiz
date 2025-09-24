# CrewAI Feature Usage Compliance Checklist

## Overview

This checklist ensures that all FinWiz crews follow established CrewAI feature usage patterns and maintain consistent analysis quality. Use this checklist when developing new crews or modifying existing ones.

## Pre-Development Checklist

### Project Structure
- [ ] Crew directory follows standard structure: `src/finwiz/crews/{crew_name}/`
- [ ] Contains `{crew_name}.py` with @agent, @task, @crew decorators
- [ ] Contains `config/agents.yaml` for agent configurations
- [ ] Contains `config/tasks.yaml` for task definitions
- [ ] Follows naming conventions: snake_case for Python files, kebab-case for YAML

### Dependencies and Imports
- [ ] Uses CrewAI decorators: `@agent`, `@task`, `@crew`
- [ ] Imports required FinWiz schemas from `src/finwiz/schemas/`
- [ ] Imports appropriate tool factories from `src/finwiz/tools/`
- [ ] Follows import order: stdlib → third-party → local (with blank line separation)

## Agent Configuration Checklist

### Required Tools by Crew Type

#### Stock Crew Agents
- [ ] `QuantitativeAnalysisTool(asset_class="stock")`
- [ ] `EnhancedSECAnalysisTool` (for 10-K extraction)
- [ ] `TickerValidationTool`
- [ ] `StandardizedSentimentTool`
- [ ] RAG tools via `get_rag_tools()`
- [ ] Yahoo Finance tools (ticker, history, news, company info)
- [ ] Research tools (SerperDevTool, FirecrawlScrapeWebsiteTool)

#### ETF Crew Agents
- [ ] `QuantitativeAnalysisTool(asset_class="etf")`
- [ ] `EnhancedETFAnalysisTool` (for factsheet extraction)
- [ ] `TickerValidationTool`
- [ ] `StandardizedSentimentTool`
- [ ] RAG tools via `get_rag_tools()`
- [ ] Yahoo Finance ETF-specific tools
- [ ] Research tools for ETF analysis

#### Crypto Crew Agents
- [ ] `QuantitativeAnalysisTool(asset_class="crypto")`
- [ ] `EnhancedCryptoAnalysisTool`
- [ ] `CoinMarketCapTool`
- [ ] `TickerValidationTool`
- [ ] RAG tools via `get_rag_tools()`
- [ ] Crypto-specific data sources (Kraken, Coinbase)

#### Portfolio Rebalancing Crew Agents
- [ ] `PortfolioRebalancingTool`
- [ ] `PortfolioPriceService`
- [ ] `QuantitativeAnalysisTool(asset_class="portfolio")`
- [ ] RAG tools via `get_rag_tools()`
- [ ] Portfolio analysis tools

#### Report Crew Agents (SPECIAL RESTRICTIONS)
- [ ] **Investment Reporter Agent**: Empty tools list (`tools=[]`)
- [ ] **Translation Agent**: Empty tools list (`tools=[]`)
- [ ] Uses `ToolRestrictionValidator` for compliance checking
- [ ] Only consumes upstream context, no external API calls

### Agent Configuration Pattern
- [ ] Uses `config=self.agents_config["{agent_name}"]` pattern
- [ ] Sets `verbose=True` for debugging
- [ ] Tools list includes all required tools for asset class
- [ ] No hardcoded configurations in Python code

## Task Configuration Checklist

### Required Task Features
- [ ] `description` field with clear task objectives
- [ ] `expected_output` field describing output format
- [ ] `agent` field specifying responsible agent
- [ ] `output_file` field for file output (where applicable)

### CrewAI Output Validation
- [ ] Uses `output_pydantic` with existing FinWiz schemas:
  - Stock: `TenKInsight`, `MarketSentiment`, `RiskAssessmentStandardized`
  - ETF: `ETFFactsheet`, `ETFTopHolding`, `RiskAssessmentStandardized`
  - Crypto: `CryptoThesis`, `RiskAssessmentStandardized`
  - Portfolio: `PortfolioReview`, `RiskAssessmentStandardized`
- [ ] Uses `output_json: true` for machine-readable appendices
- [ ] Schema names match exactly with FinWiz schema classes

### Performance Optimization
- [ ] I/O-bound tasks have `async_execution: true`
- [ ] Final task has `async_execution: false` (CrewAI requirement)
- [ ] Uses `depends_on` for proper task sequencing
- [ ] No circular dependencies in task graph

### Risk Assessment Requirements
- [ ] All crews generate `RiskAssessmentStandardized` objects
- [ ] Uses 0-5 scale scoring methodology
- [ ] Includes systematic and idiosyncratic risk components
- [ ] Follows standardized risk taxonomy

## Crew Configuration Checklist

### Process Configuration
- [ ] Uses `Process.sequential` for workflow coordination
- [ ] Sets `verbose=True` for debugging support
- [ ] Includes all required agents in `agents` list
- [ ] Includes all required tasks in `tasks` list

### Performance Settings
- [ ] `respect_context_window=True` for token management
- [ ] `max_rpm` configured appropriately (typically 20)
- [ ] No custom retry logic (uses CrewAI built-in features)

### Integration with FinWiz Systems
- [ ] Uses existing `ConfigurationManager` for API keys
- [ ] Integrates with `ToolRestrictionValidator` (Report crew)
- [ ] Uses existing `SessionManager` for state management
- [ ] Leverages existing error handling patterns

## Translation Task Requirements

### Translation Task Configuration
- [ ] All crews include translation tasks for French output
- [ ] Translation agent has empty tools list (`tools=[]`)
- [ ] Translation task depends on final report task
- [ ] Preserves HTML structure and CSS styling
- [ ] Only translates text content, not markup

### Translation Task Pattern
```yaml
translation_task:
  description: "Translate report to French preserving HTML structure"
  expected_output: "French translation with preserved HTML formatting"
  agent: translator
  depends_on:
    - final_report_task
```

## Validation and Testing Checklist

### Configuration Validation
- [ ] All required environment variables are checked at startup
- [ ] API keys validated before crew execution
- [ ] Tool configurations tested with mock data
- [ ] Schema validation tested with sample outputs

### Testing Requirements
- [ ] Unit tests cover all agent configurations
- [ ] Integration tests verify tool usage
- [ ] Mock all external API calls in tests
- [ ] Test execution time < 5 seconds per test suite
- [ ] No shared state between tests

### Output Quality Validation
- [ ] Generated outputs match expected schemas
- [ ] JSON appendices are properly formatted
- [ ] Risk assessments use standardized 0-5 scale
- [ ] All required fields are populated
- [ ] Source citations include as-of dates

## Deployment Checklist

### Pre-Deployment Validation
- [ ] Run existing FinWiz test suite with no regressions
- [ ] Verify crew execution with sample inputs
- [ ] Check output format compliance
- [ ] Validate performance impact (execution times)
- [ ] Confirm no tool restriction violations

### Documentation Updates
- [ ] Update crew-specific documentation
- [ ] Document any deviations from standard patterns
- [ ] Include troubleshooting notes for common issues
- [ ] Update API documentation if new endpoints added

### Monitoring Setup
- [ ] Configure logging for new crew
- [ ] Set up error tracking and alerting
- [ ] Monitor execution times and resource usage
- [ ] Track output quality metrics

## Common Configuration Examples

### Standard Agent Configuration
```python
@agent
def {asset_class}_analyst(self) -> Agent:
    return Agent(
        config=self.agents_config["{asset_class}_analyst"],
        tools=[
            get_quantitative_analysis_tool(asset_class="{asset_class}"),
            enhanced_{asset_class}_tool,
            ticker_validation_tool,
            *get_rag_tools(),
            # Asset-specific tools...
        ],
        verbose=True
    )
```

### Standard Task Configuration
```yaml
{asset_class}_analysis_task:
  description: "Analyze {asset_class} with quantitative metrics"
  expected_output: "Structured analysis with risk assessment"
  output_pydantic: "{AssetClass}AnalysisResult"
  output_json: true
  agent: {asset_class}_analyst
  async_execution: true
  depends_on:
    - validation_task
```

### Standard Crew Configuration
```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        verbose=True,
        respect_context_window=True,
        max_rpm=20,
    )
```

## Maintenance Procedures

### Quarterly Review Process
1. **Configuration Audit**: Review all crew configurations for drift from standards
2. **Tool Usage Verification**: Confirm crews use assigned tools properly
3. **Output Quality Assessment**: Review generated outputs for schema compliance
4. **Performance Monitoring**: Check execution times and resource usage
5. **Documentation Updates**: Update guides based on lessons learned

### Issue Resolution Process
1. **Identify Issue**: Use troubleshooting guide to diagnose problems
2. **Apply Fix**: Follow standard configuration patterns
3. **Test Changes**: Run test suite to verify no regressions
4. **Document Solution**: Update troubleshooting guide if needed
5. **Monitor Results**: Verify fix resolves issue in production

### Continuous Improvement
- [ ] Collect feedback from crew execution logs
- [ ] Identify common configuration mistakes
- [ ] Update checklist based on new patterns
- [ ] Share best practices across development team
- [ ] Regular training on CrewAI feature updates

## Quick Reference

### Essential Commands
```bash
# Run crew with validation
uv run python src/finwiz/main.py

# Test configuration changes
uv run pytest -m "not integration"

# Lint and format code
ruff check . && ruff format .

# Check schema compliance
uv run python -m finwiz.validation.schema_validator
```

### Key Files to Check
- `src/finwiz/crews/{crew_name}/{crew_name}.py` - Agent and task definitions
- `src/finwiz/crews/{crew_name}/config/agents.yaml` - Agent configurations
- `src/finwiz/crews/{crew_name}/config/tasks.yaml` - Task definitions
- `src/finwiz/schemas/` - Pydantic schema definitions
- `tests/` - Test coverage for crew configurations

This checklist ensures consistent, high-quality CrewAI implementations across all FinWiz crews while maintaining compatibility with existing systems and following established best practices.