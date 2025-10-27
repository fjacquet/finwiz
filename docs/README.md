# FinWiz Documentation

Welcome to the FinWiz MkDocs documentation site. This professional documentation system follows the [Diátaxis framework](https://diataxis.fr/) for clear, organized technical documentation.

## 🌐 Documentation Site Features

### Professional Documentation System
- **Interactive Schema Documentation**: Live examples and validation for all Pydantic models
- **Full-Text Search**: Advanced search with highlighting and result filtering
- **Mobile Responsive**: Optimized experience across all devices with dark/light theme support
- **Professional Navigation**: Hierarchical navigation with breadcrumbs and cross-references
- **Development Integration**: Live development server with hot reload and automated validation

### Quick Commands
```bash
# Install documentation dependencies
make docs-install

# Start development server (http://127.0.0.1:8000)
make docs-serve

# Build static documentation site
make docs-build

# Validate documentation quality
make docs-validate

# Deploy to GitHub Pages
make docs-deploy
```

## 📚 Documentation Categories

### 🎓 [Tutorials](tutorials/)
**Learning-oriented** guides that help you get started:
- [Getting Started](tutorials/getting_started.md) - Complete setup and first analysis
- [First Analysis](tutorials/first_analysis.md) - Step-by-step analysis walkthrough
- [Portfolio Analysis](tutorials/portfolio_analysis.md) - Comprehensive portfolio review

### 🔧 [How-to Guides](how-to/)
**Problem-solving** guides for specific tasks:
- [Setup Environment](how-to/setup_environment.md) - Environment configuration and API keys
- [Performance Optimization](how-to/PERFORMANCE_OPTIMIZATION_GUIDE.md) - Speed up analysis with batch processing
- [Template Configuration](how-to/template_configuration.md) - Customize Jinja2 report templates
- [Troubleshooting](how-to/troubleshooting.md) - Common issues and solutions

### 📖 [Reference](reference/)
**Information-oriented** reference material:
- [API Reference](reference/API_REFERENCE.md) - Complete API documentation for tools and schemas
- [CLI Commands](reference/cli_commands.md) - Command-line interface reference
- [Schema Documentation](reference/schemas/index.md) - Interactive Pydantic model documentation
- [Configuration Reference](reference/configuration.md) - Complete configuration options

### 💡 [Explanations](explanations/)
**Understanding-oriented** explanations of concepts:
- [Architecture](explanations/ARCHITECTURE.md) - System design and component relationships
- [Design Principles](explanations/design_principles.md) - Core design philosophy and decisions
- [Data Flow](explanations/data_flow.md) - Data processing and validation architecture
- [AI vs Rules](explanations/ai_vs_rules.md) - When to use AI agents vs deterministic code

## 🚀 Quick Start

1. **New to FinWiz?** Start with [Getting Started Tutorial](tutorials/getting_started.md)
2. **Need to solve a problem?** Check [How-to Guides](how-to/)
3. **Looking for specific information?** Browse [Reference](reference/)
4. **Want to understand concepts?** Read [Explanations](explanations/)

## 📋 Documentation Maintenance

### Content Governance
- **[Content Governance](maintenance/content-governance.md)**: Review processes and quality standards
- **[Style Guide](maintenance/style-guide.md)**: Writing standards and formatting guidelines
- **[Content Creation Guide](maintenance/content-creation-guide.md)**: Workflows for creating documentation
- **[Setup & Deployment](maintenance/setup-deployment-guide.md)**: Technical setup and deployment procedures

### Quality Assurance
- **[Troubleshooting Guide](maintenance/troubleshooting-guide.md)**: Common issues and solutions
- **[Content Audit Schedule](maintenance/content-audit-schedule.md)**: Regular review and update processes

## 🛠️ Development

- **Code Standards**: See [Developer Guide](reference/DEVELOPER_GUIDE.md)
- **Architecture**: See [Architecture](explanations/ARCHITECTURE.md)
- **Performance**: See [Performance Optimization](how-to/PERFORMANCE_OPTIMIZATION_GUIDE.md)
- **Documentation Development**: See [Setup & Deployment Guide](maintenance/setup-deployment-guide.md)

---

**Last Updated**: 2025-10-26  
**Documentation System**: MkDocs with Material Theme  
**Framework**: Diátaxis (Tutorials, How-to, Reference, Explanations)
