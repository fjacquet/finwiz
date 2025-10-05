# Investment Discovery Developer Documentation Index

## Overview

This index provides a comprehensive guide to all developer documentation for the A+ Investment Discovery system. The documentation is organized by topic and complexity level to help developers quickly find the information they need.

## Documentation Structure

### 📚 Core Documentation

#### [Investment Discovery Developer Guide](investment_discovery_developer_guide.md)

**Audience**: Developers working with the discovery system  
**Content**: Architecture overview, components, integration patterns, testing strategies  
**When to use**: Starting development, understanding system architecture, implementing integrations

#### [A+ Scoring Methodology](investment_discovery_scoring_methodology.md)

**Audience**: Developers implementing scoring logic, data scientists, quantitative analysts  
**Content**: Detailed scoring algorithms, criteria, market regime adaptation, validation methods  
**When to use**: Understanding scoring logic, customizing criteria, implementing new scoring models

#### [Tools API Reference](investment_discovery_tools_api_reference.md)

**Audience**: Developers using discovery tools in agents or applications  
**Content**: Complete API documentation for all discovery tools, parameters, return values, examples  
**When to use**: Implementing tool usage, debugging tool calls, understanding tool capabilities

### 🔧 Operational Documentation

#### [Troubleshooting Guide](investment_discovery_troubleshooting_guide.md)

**Audience**: Developers, DevOps engineers, system administrators  
**Content**: Common issues, diagnostic procedures, solutions, performance optimization  
**When to use**: Debugging issues, performance problems, system maintenance

#### [Extension Guide](investment_discovery_extension_guide.md)

**Audience**: Developers adding new functionality, extending system capabilities  
**Content**: Extension architecture, adding asset classes, custom scoring models, new data providers  
**When to use**: Adding new asset types, implementing custom logic, integrating new data sources

### 📊 User-Facing Documentation

#### [Investment Discovery API Reference](investment_discovery_api_reference.md)

**Audience**: API consumers, frontend developers, integration partners  
**Content**: REST API endpoints, authentication, request/response formats, SDKs  
**When to use**: Building API integrations, consuming discovery services

#### [Investment Discovery User Guide](investment_discovery_user_guide.md)

**Audience**: End users, portfolio managers, investment analysts  
**Content**: Feature overview, usage instructions, interpretation of results  
**When to use**: Understanding discovery features, interpreting recommendations

## Quick Start Guides

### For New Developers

1. **Start Here**: [Developer Guide](investment_discovery_developer_guide.md) - Architecture Overview
2. **Understand Scoring**: [Scoring Methodology](investment_discovery_scoring_methodology.md) - Core Concepts
3. **Use Tools**: [Tools API Reference](investment_discovery_tools_api_reference.md) - Implementation Details
4. **Troubleshoot**: [Troubleshooting Guide](investment_discovery_troubleshooting_guide.md) - Common Issues

### For System Integrators

1. **API Integration**: [API Reference](investment_discovery_api_reference.md) - REST Endpoints
2. **Tool Usage**: [Tools API Reference](investment_discovery_tools_api_reference.md) - Direct Tool Access
3. **Error Handling**: [Troubleshooting Guide](investment_discovery_troubleshooting_guide.md) - Error Resolution
4. **Performance**: [Developer Guide](investment_discovery_developer_guide.md) - Optimization Patterns

### For System Extenders

1. **Extension Architecture**: [Extension Guide](investment_discovery_extension_guide.md) - Framework Overview
2. **Scoring Customization**: [Scoring Methodology](investment_discovery_scoring_methodology.md) - Custom Models
3. **Tool Development**: [Tools API Reference](investment_discovery_tools_api_reference.md) - Tool Interfaces
4. **Testing**: [Developer Guide](investment_discovery_developer_guide.md) - Testing Strategies

## Code Examples by Use Case

### Basic Tool Usage

```python
# Score an investment
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool

scorer = APlusScoringTool()
result = scorer._run(
    symbol='VTI',
    asset_type='etf',
    fundamental_data={'expense_ratio': 0.03, 'aum': 300e9}
)
print(f"Grade: {result['grade']}")
```

**Reference**: [Tools API Reference](investment_discovery_tools_api_reference.md#aplusscoringtool)

### Market Screening

```python
# Screen for A+ candidates
from finwiz.tools.market_screening_tool import MarketScreeningTool

screener = MarketScreeningTool()
candidates = screener._run(
    asset_type='etf',
    max_candidates=20,
    min_a_plus_score=0.90
)
print(f"Found {len(candidates['candidates'])} candidates")
```

**Reference**: [Tools API Reference](investment_discovery_tools_api_reference.md#marketscreeningtool)

### Custom Scoring Model

```python
# Implement custom ESG scoring
from finwiz.extensions.esg_scoring_model import ESGScoringModel

esg_model = ESGScoringModel(esg_weight=0.4)
analysis = esg_model.score_investment(candidate, market_context)
```

**Reference**: [Extension Guide](investment_discovery_extension_guide.md#custom-scoring-models)

### Adding New Asset Type

```python
# Add commodity support
from finwiz.extensions.commodities_extension import CommodityExtension
from finwiz.extensions.registry import extension_registry

commodity_ext = CommodityExtension()
extension_registry.register_extension(commodity_ext)
```

**Reference**: [Extension Guide](investment_discovery_extension_guide.md#adding-new-asset-classes)

## Testing Examples

### Unit Testing Tools

```python
def test_a_plus_scoring_tool(mocker):
    # Mock external data
    mock_data = mocker.patch('finwiz.tools.market_data.get_data')
    mock_data.return_value = {'expense_ratio': 0.05}
    
    # Test scoring
    scorer = APlusScoringTool()
    result = scorer._run('VTI', 'etf', {'expense_ratio': 0.05})
    
    assert result['grade'] in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
```

**Reference**: [Developer Guide](investment_discovery_developer_guide.md#testing-framework)

### Integration Testing

```python
def test_discovery_workflow():
    # Test complete discovery workflow
    crew = InvestmentDiscoveryCrew()
    result = crew.kickoff()
    
    assert result.a_plus_candidates
    assert len(result.a_plus_candidates) > 0
```

**Reference**: [Developer Guide](investment_discovery_developer_guide.md#integration-tests)

## Configuration Examples

### Basic Configuration

```yaml
# config/discovery.yaml
discovery:
  scoring:
    a_plus_threshold: 0.95
    confidence_threshold: 0.80
  
  screening:
    max_candidates_per_type: 50
    timeout_seconds: 600
  
  market_data:
    providers: ['yahoo', 'alpha_vantage']
    cache_ttl_hours: 24
```

**Reference**: [Developer Guide](investment_discovery_developer_guide.md#configuration-management)

### Extension Configuration

```yaml
# config/extensions.yaml
extensions:
  asset_types:
    - name: "commodity"
      enabled: true
      config:
        min_liquidity_millions: 100.0
  
  scoring_models:
    - name: "esg_focused"
      enabled: true
      config:
        esg_weight: 0.4
```

**Reference**: [Extension Guide](investment_discovery_extension_guide.md#configuration-and-deployment)

## Performance Optimization

### Caching Strategies

```python
from finwiz.utils.cache_manager import cache_with_ttl

@cache_with_ttl(hours=1)
def get_market_regime():
    return analyze_market_conditions()
```

**Reference**: [Developer Guide](investment_discovery_developer_guide.md#performance-optimization)

### Parallel Processing

```python
import asyncio

async def parallel_discovery():
    tasks = [
        discover_etfs_async(),
        discover_stocks_async(),
        discover_crypto_async()
    ]
    results = await asyncio.gather(*tasks)
    return results
```

**Reference**: [Developer Guide](investment_discovery_developer_guide.md#parallel-processing)

## Monitoring and Debugging

### Health Checks

```python
from finwiz.health.discovery_health import DiscoveryHealthChecker

checker = DiscoveryHealthChecker()
health_status = checker.run_all_checks()
```

**Reference**: [Troubleshooting Guide](investment_discovery_troubleshooting_guide.md#health-checks)

### Performance Monitoring

```python
from finwiz.monitoring.discovery_metrics import DiscoveryMetrics

metrics = DiscoveryMetrics()
performance_data = metrics.get_performance_summary()
```

**Reference**: [Troubleshooting Guide](investment_discovery_troubleshooting_guide.md#monitoring-and-alerting)

## Common Patterns

### Error Handling

```python
from finwiz.tools.exceptions import InsufficientDataError, MarketDataError

try:
    result = scorer._run(symbol, asset_type, data)
except InsufficientDataError:
    # Handle missing data
    result = use_partial_scoring(symbol, asset_type, data)
except MarketDataError:
    # Handle data source issues
    result = use_cached_data(symbol, asset_type)
```

**Reference**: [Tools API Reference](investment_discovery_tools_api_reference.md#error-handling)

### Graceful Degradation

```python
from finwiz.utils.graceful_degradation import GracefulDegradation

degradation = GracefulDegradation()
if degradation.is_market_data_unavailable():
    use_cached_data()
```

**Reference**: [Troubleshooting Guide](investment_discovery_troubleshooting_guide.md#graceful-degradation)

## Development Workflow

### 1. Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd finwiz

# Setup environment
uv sync
source .venv/bin/activate

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 2. Run Tests

```bash
# Run unit tests
uv run pytest tests/unit/ -v

# Run integration tests
uv run pytest tests/integration/ -v

# Run specific test
uv run pytest tests/unit/tools/test_a_plus_scoring_tool.py -v
```

### 3. Code Quality

```bash
# Format code
ruff format .

# Check code quality
ruff check .

# Type checking
mypy src/finwiz/
```

### 4. Documentation

```bash
# Generate API documentation
uv run python scripts/generate_docs.py

# Serve documentation locally
uv run mkdocs serve
```

## Troubleshooting Quick Reference

| Issue | Documentation | Quick Fix |
|-------|---------------|-----------|
| Tool not working | [Tools API Reference](investment_discovery_tools_api_reference.md) | Check parameters and data format |
| Scoring errors | [Scoring Methodology](investment_discovery_scoring_methodology.md) | Validate input data completeness |
| Performance issues | [Troubleshooting Guide](investment_discovery_troubleshooting_guide.md) | Enable caching and parallel processing |
| Integration failures | [Developer Guide](investment_discovery_developer_guide.md) | Check API keys and network connectivity |
| Extension not loading | [Extension Guide](investment_discovery_extension_guide.md) | Verify configuration and dependencies |

## Support and Resources

### Internal Resources

- **Code Repository**: Source code with inline documentation
- **Test Suite**: Comprehensive test examples in `tests/` directory
- **Configuration Examples**: Sample configurations in `config/` directory
- **Example Scripts**: Usage examples in `examples/` directory

### External Resources

- **CrewAI Documentation**: <https://docs.crewai.com/>
- **Pydantic Documentation**: <https://docs.pydantic.dev/>
- **FastAPI Documentation**: <https://fastapi.tiangolo.com/>

### Getting Help

1. **Check Documentation**: Start with relevant documentation section
2. **Review Examples**: Look at example code and test cases
3. **Debug Logs**: Enable debug logging for detailed error information
4. **Health Checks**: Run system health checks to identify issues
5. **Community**: Engage with development team for complex issues

---

This documentation index serves as the central hub for all developer resources related to the A+ Investment Discovery system. Use it to quickly navigate to the information you need for development, integration, extension, and troubleshooting.
