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

### Schema Documentation

- **[Schema Overview](schemas/index.md)** - Pydantic model documentation
<!-- - **Crew Export Schemas** - Analysis output schemas (TBD) -->
<!-- - **Portfolio Schemas** - Portfolio data models (TBD) -->
<!-- - **Quantitative Schemas** - Quantitative analysis models (TBD) -->
<!-- - **Validation Schemas** - Validation models (TBD) -->

### Migration and Compatibility

- **[Changelog](changelog.md)** - Version history

## Reference by Category

### For Developers

Technical reference for developers:

1. **[API Overview](api/index.md)** - Complete API documentation
2. **[Schema Documentation](schemas/index.md)** - Pydantic models

## Quick Reference Lookup

### Common Tasks

| Task | Reference |
|------|-----------|
| Validate data | [Schema Documentation](schemas/index.md) |

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

- [Operations Guide](../how-to/OPERATIONS_GUIDE.md) - Deployment, operations, and migration
- [Developer Guide](../development/DEVELOPER_GUIDE.md) - Architecture and development

### Tutorials

- [Getting Started](../tutorials/getting_started.md) - First-time setup
- [First Analysis](../tutorials/first_analysis.md) - Your first analysis

### How-To Guides

- [Setup Environment](../how-to/setup_environment.md) - Environment setup

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

See [Contributing Guidelines](../development/DEVELOPER_GUIDE.md#contributing) for details.

## Need Help?

- **Can't find something?** Check [Getting Started](../tutorials/getting_started.md) or the [Operations Guide](../how-to/OPERATIONS_GUIDE.md)
- **Need examples?** See [Tutorials](../tutorials/index.md)
- **Have questions?** Visit [GitHub Discussions](https://github.com/fjacquet/finwiz/discussions)
- **Found an error?** Report via [GitHub Issues](https://github.com/fjacquet/finwiz/issues)

---

*Looking for something specific? Use the navigation above or search the documentation.*
