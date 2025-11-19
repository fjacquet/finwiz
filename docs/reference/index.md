---
layout: default
title: Reference
nav_order: 6
has_children: true
---

# Reference Documentation

Technical reference material for FinWiz APIs, schemas, configuration, and commands.

## What Is Reference Documentation?

Reference documentation is **information-oriented** material that provides detailed technical specifications. It's designed for lookup rather than learning, offering complete and accurate information about FinWiz's components.

## Available Reference Material

### API Documentation

- **[API Overview](api/index.md)** - Complete API documentation
<!-- - **Data Access API** - Data fetching and integration (TBD) -->
<!-- - **Analysis API** - Analysis crew interfaces (TBD) -->
<!-- - **Scoring API** - Python scoring engine (TBD) -->
<!-- - **Reporting API** - Report generation (TBD) -->

### Command-Line Interface

- **[CLI Commands](cli_commands.md)** - Complete command reference
- **[CLI Options](cli_options.md)** - Command-line flags and options

### Schema Documentation

- **[Schema Overview](schemas/index.md)** - Pydantic model documentation
<!-- - **Crew Export Schemas** - Analysis output schemas (TBD) -->
<!-- - **Portfolio Schemas** - Portfolio data models (TBD) -->
<!-- - **Quantitative Schemas** - Quantitative analysis models (TBD) -->
<!-- - **Validation Schemas** - Validation models (TBD) -->

### Configuration

- **[Environment Variables](environment_variables.md)** - Complete configuration reference
- **[Agent Configuration](agent_configuration.md)** - Agent YAML configuration
- **[Task Configuration](task_configuration.md)** - Task YAML configuration
- **[Tool Configuration](tool_configuration.md)** - Tool configuration options

### Data Sources

- **[Data Sources](data_sources.md)** - Supported data providers
- **[Data Quality](data_quality.md)** - Data quality standards
- **[API Requirements](api_requirements.md)** - API key requirements

### Error Reference

- **[Error Codes](errors.md)** - Error code reference
- **[API Errors](api_errors.md)** - API error handling
- **[Validation Errors](validation_errors.md)** - Validation error types

### Performance

- **[Performance Metrics](performance.md)** - Performance benchmarks
- **[Resource Usage](resource_usage.md)** - Memory and CPU usage
- **[Rate Limits](rate_limits.md)** - API rate limits

### Migration and Compatibility

- **[Migration Guide](migration.md)** - Version migration guide
- **[Compatibility](compatibility.md)** - Version compatibility matrix
- **[Changelog](changelog.md)** - Version history

## Reference by Category

### For Users

Essential reference material for end users:

1. **[CLI Commands](cli_commands.md)** - Command-line reference
2. **[Environment Variables](environment_variables.md)** - Configuration options
3. **[Data Sources](data_sources.md)** - Data provider information
4. **[Error Codes](errors.md)** - Error troubleshooting

### For Developers

Technical reference for developers:

1. **[API Overview](api/index.md)** - Complete API documentation
2. **[Schema Documentation](schemas/index.md)** - Pydantic models
3. **[Agent Configuration](agent_configuration.md)** - Agent setup
4. **[Task Configuration](task_configuration.md)** - Task setup

### For System Administrators

Operations reference:

1. **[Environment Variables](environment_variables.md)** - Configuration
2. **[Performance Metrics](performance.md)** - Benchmarks
3. **[Resource Usage](resource_usage.md)** - Resource requirements
4. **[Rate Limits](rate_limits.md)** - API limits

## Quick Reference Lookup

### Common Tasks

| Task | Reference |
|------|-----------|
| Run analysis | [CLI Commands](cli_commands.md#analysis-commands) |
| Configure API keys | [Environment Variables](environment_variables.md) |
| Customize agents | [Agent Configuration](agent_configuration.md) |
| Validate data | [Schema Documentation](schemas/index.md) |
| Check errors | [Error Codes](errors.md) |
| Optimize performance | [Performance Metrics](performance.md) |

### API Quick Reference
<!--  -->
<!-- | Component | API Reference | -->
<!-- |-----------|---------------| -->
<!-- | Data Access | [Data Access API](api/data_access.md) | -->
<!-- | Stock Analysis | [Analysis API](api/analysis.md#stock-analysis) | -->
<!-- | ETF Analysis | [Analysis API](api/analysis.md#etf-analysis) | -->
<!-- | Crypto Analysis | [Analysis API](api/analysis.md#crypto-analysis) | -->
<!-- | Portfolio Review | [Analysis API](api/analysis.md#portfolio-review) | -->
<!-- | Scoring Engine | [Scoring API](api/scoring.md) | -->
<!-- | Report Generation | [Reporting API](api/reporting.md) | -->
<!--  -->
### Schema Quick Reference
<!--  -->
<!-- | Schema Type | Documentation | -->
<!-- |-------------|---------------| -->
<!-- | Stock Analysis | [Crew Export Schemas](schemas/crew_exports.md#stock-analysis) | -->
<!-- | ETF Analysis | [Crew Export Schemas](schemas/crew_exports.md#etf-analysis) | -->
<!-- | Crypto Analysis | [Crew Export Schemas](schemas/crew_exports.md#crypto-analysis) | -->
<!-- | Portfolio | [Portfolio Schemas](schemas/portfolio.md) | -->
<!-- | Quantitative | [Quantitative Schemas](schemas/quantitative.md) | -->
<!--  -->
## Reference Documentation Standards

All reference material follows these standards:

### Completeness

- **Every parameter documented**: No undocumented options
- **Every return value specified**: Clear return types
- **Every error listed**: Comprehensive error coverage

### Accuracy

- **Version-specific**: Clearly marked version information
- **Type-safe**: Precise type annotations
- **Tested**: All examples are tested and verified

### Structure

- **Consistent format**: Uniform structure across all reference docs
- **Easy lookup**: Organized for quick information retrieval
- **Cross-referenced**: Links to related documentation

## Additional Resources

### Core Documentation

- [User Guide](../USER_GUIDE.md) - Complete user documentation
- [Developer Guide](../DEVELOPER_GUIDE.md) - Architecture and development

### Tutorials

- [Getting Started](../tutorials/getting_started.md) - First-time setup
- [First Analysis](../tutorials/first_analysis.md) - Your first analysis

### How-To Guides

- [Setup Environment](../how-to/setup_environment.md) - Environment setup
- [Performance Optimization](../how-to/performance_optimization.md) - Optimization

### Explanations

- [Architecture](../explanations/ARCHITECTURE.md) - System design
- [Design Principles](../explanations/design_principles.md) - Core philosophy

## Using Reference Documentation

### Best Practices

1. **Use Search**: Use Ctrl+F to find specific information quickly
2. **Check Version**: Ensure documentation matches your FinWiz version
3. **Follow Types**: Pay attention to type annotations and constraints
4. **Try Examples**: Test code examples in your environment
5. **Report Issues**: Submit corrections via GitHub Issues

### When to Use Reference

Use reference documentation when you:

- ✅ Need exact parameter specifications
- ✅ Want to understand return values
- ✅ Need to look up error codes
- ✅ Want to verify configuration options
- ✅ Need API signatures

**Don't use reference for**:

- ❌ Learning FinWiz (use [Tutorials](../tutorials/index.md))
- ❌ Solving specific problems (use [How-To Guides](../how-to/index.md))
- ❌ Understanding concepts (use [Explanations](../explanations/index.md))

## Contributing to Reference

Reference documentation should be:

- **Accurate**: Verified against code
- **Complete**: No missing information
- **Concise**: Clear and to the point
- **Current**: Updated with each release

See [Contributing Guidelines](../DEVELOPER_GUIDE.md#contributing) for details.

## Need Help?

- **Can't find something?** Check [User Guide](../USER_GUIDE.md)
- **Need examples?** See [Tutorials](../tutorials/index.md)
- **Have questions?** Visit [GitHub Discussions](https://github.com/fjacquet/finwiz/discussions)
- **Found an error?** Report via [GitHub Issues](https://github.com/fjacquet/finwiz/issues)

---

*Looking for something specific? Use the navigation above or search the documentation.*
