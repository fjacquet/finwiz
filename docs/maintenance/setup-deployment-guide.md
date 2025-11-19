# MkDocs Documentation Setup and Deployment Guide

This guide provides comprehensive instructions for setting up, maintaining, and deploying the FinWiz MkDocs documentation site.

## Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **uv**: Python package manager (recommended)
- **Git**: Version control
- **Node.js**: For additional tooling (optional)

### Environment Setup

1. **Install uv** (if not already installed):

   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Clone the repository**:

   ```bash
   git clone https://github.com/finwiz/finwiz.git
   cd finwiz
   ```

3. **Install dependencies**:

   ```bash
   make docs-install
   # or manually:
   uv sync --group docs
   ```

## Local Development

### Starting the Development Server

```bash
# Start MkDocs development server
make docs-serve

# Manual command
uv run mkdocs serve --dev-addr 127.0.0.1:8000
```

The documentation will be available at `http://127.0.0.1:8000` with hot reload enabled.

### Development Workflow

1. **Edit documentation files** in the `docs/` directory
2. **Preview changes** in your browser (auto-refreshes)
3. **Validate changes** before committing:

   ```bash
   make docs-validate
   ```

4. **Commit and push** your changes

### File Structure

```
docs/
├── index.md                    # Homepage
├── tutorials/                  # Learning-oriented content
├── how-to/                    # Problem-solving guides
├── reference/                 # Information-oriented content
├── explanations/              # Understanding-oriented content
├── assets/                    # Images, icons, etc.
├── stylesheets/              # Custom CSS
├── javascripts/              # Custom JavaScript
├── overrides/                # Theme customizations
└── includes/                 # Reusable content snippets
```

## Content Management

### Adding New Content

1. **Determine content type** using Diátaxis framework:
   - **Tutorials**: Step-by-step learning experiences
   - **How-to guides**: Problem-solving instructions
   - **Reference**: Information lookup (APIs, schemas)
   - **Explanations**: Conceptual understanding

2. **Create the file** in the appropriate directory:

   ```bash
   # Example: Adding a new tutorial
   touch docs/tutorials/new-feature-tutorial.md
   ```

3. **Add to navigation** in `.pages` file or `mkdocs.yml`

4. **Follow content standards** (see Content Creation Guide)

### Content Migration

For migrating existing documentation:

```bash
# Run migration script
make docs-migrate

# Manual migration
uv run python scripts/migrate_docs.py --source docs --target docs_new
```

### Schema Documentation

To add interactive schema documentation:

1. **Place schema files** in `docs/schemas/`
2. **Reference in markdown**:

   ```markdown
   ```schema:SchemaName
   {
     "description": "Schema description",
     "example": {...}
   }
   ```

   ```

## Build Process

### Local Build

```bash
# Standard build
make docs-build

# Production build (optimized)
make docs-build-production

# Fast build (no optimization)
make docs-build-fast
```

### Build Validation

```bash
# Standard validation
make docs-validate

# Strict validation (fails on warnings)
make docs-validate-strict

# Validate built site
make docs-validate-build
```

### Build Artifacts

- **Output directory**: `site/`
- **Static files**: HTML, CSS, JS, images
- **Search index**: For full-text search functionality

## Deployment

### GitHub Pages (Recommended)

**Automatic deployment** via GitHub Actions:

1. **Push to main branch** triggers automatic deployment
2. **Site URL**: `https://finwiz.github.io/finwiz/`
3. **Custom domain**: Configure in repository settings

**Manual deployment**:

```bash
# Deploy to GitHub Pages
make docs-deploy

# Force deployment
make docs-deploy-force
```

### Production Deployment

```bash
# Deploy to production
make docs-deploy-production

# Zero-downtime deployment
make docs-deploy-zero-downtime

# Check deployment status
make docs-status
```

### Staging Deployment

```bash
# Deploy to staging
make docs-deploy-staging

# Zero-downtime staging deployment
make docs-deploy-zero-downtime-staging

# Check staging status
make docs-status-staging
```

### Rollback Procedures

```bash
# Rollback production
make docs-rollback

# Rollback staging
make docs-rollback-staging
```

## Configuration Management

### MkDocs Configuration (`mkdocs.yml`)

Key configuration sections:

```yaml
site_name: FinWiz Documentation
site_description: AI-powered financial analysis platform documentation
site_url: https://finwiz-docs.example.com

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - search.highlight
    - content.code.copy

plugins:
  - search
  - awesome-pages
  - mermaid2

markdown_extensions:
  - pymdownx.superfences
  - pymdownx.tabbed
  - admonition
  - toc
```

### Environment Variables

Set these for production deployment:

```bash
# Google Analytics (optional)
export GOOGLE_ANALYTICS_KEY="G-XXXXXXXXXX"

# Custom domain (optional)
export DOCS_DOMAIN="docs.finwiz.com"
```

### Theme Customization

- **Custom CSS**: `docs/stylesheets/extra.css`
- **Custom JavaScript**: `docs/javascripts/`
- **Theme overrides**: `docs/overrides/`
- **Assets**: `docs/assets/`

## Performance Optimization

### Build Optimization

1. **Image optimization**: Compress images before adding
2. **CSS/JS minification**: Enabled in production builds
3. **Search index optimization**: Automatic in MkDocs Material

### Monitoring

```bash
# Check site performance
make docs-status-json

# Monitor deployment
python scripts/monitor_deployment.py production
```

### Performance Targets

- **Page load time**: < 2 seconds
- **Search response**: < 500ms
- **Build time**: < 30 seconds
- **Mobile performance**: 90+ Lighthouse score

## Troubleshooting

### Common Issues

#### Build Failures

**Symptom**: `mkdocs build` fails with errors

**Solutions**:

1. Check for broken links: `make docs-validate`
2. Validate markdown syntax: `make docs-lint`
3. Check plugin compatibility: Review `mkdocs.yml`

#### Navigation Issues

**Symptom**: Pages not appearing in navigation

**Solutions**:

1. Check `.pages` files in directories
2. Verify `nav` section in `mkdocs.yml`
3. Ensure files are in correct directories

#### Search Not Working

**Symptom**: Search returns no results

**Solutions**:

1. Rebuild site: `make docs-build`
2. Check search plugin configuration
3. Clear browser cache

#### Deployment Failures

**Symptom**: `make docs-deploy` fails

**Solutions**:

1. Check GitHub permissions
2. Verify repository settings
3. Check for large files (>100MB limit)

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Verbose build
uv run mkdocs build --verbose

# Debug serve
uv run mkdocs serve --verbose
```

### Log Files

Check these locations for error logs:

- **Build logs**: Terminal output during `mkdocs build`
- **Server logs**: Terminal output during `mkdocs serve`
- **GitHub Actions**: Repository Actions tab for deployment logs

## Maintenance Tasks

### Regular Maintenance

**Weekly**:

- [ ] Check for broken links: `make docs-validate`
- [ ] Review and update outdated content
- [ ] Monitor site performance

**Monthly**:

- [ ] Update dependencies: `uv sync --group docs`
- [ ] Review analytics and user feedback
- [ ] Audit content for accuracy

**Quarterly**:

- [ ] Full content audit and reorganization
- [ ] Performance optimization review
- [ ] Security updates and dependency upgrades

### Dependency Updates

```bash
# Update all dependencies
uv sync --group docs --upgrade

# Update specific package
uv add mkdocs-material@latest --group docs
```

### Backup Procedures

**Content backup**:

- Documentation is version-controlled in Git
- Regular repository backups via GitHub

**Site backup**:

- Built site is stored in `gh-pages` branch
- Can be restored from any commit

## Security Considerations

### Access Control

- **Repository access**: Managed via GitHub permissions
- **Deployment keys**: Stored as GitHub Secrets
- **Custom domains**: Configure HTTPS and security headers

### Content Security

- **Sensitive information**: Never commit API keys or secrets
- **External links**: Regularly audit for security
- **User-generated content**: Validate and sanitize

### HTTPS Configuration

For custom domains:

1. **Configure DNS**: Point domain to GitHub Pages
2. **Enable HTTPS**: In repository settings
3. **Force HTTPS**: Redirect HTTP to HTTPS

## Support and Resources

### Documentation

- **MkDocs**: <https://www.mkdocs.org/>
- **Material Theme**: <https://squidfunk.github.io/mkdocs-material/>
- **Diátaxis Framework**: <https://diataxis.fr/>

### Getting Help

1. **Internal documentation**: Check this guide and content standards
2. **GitHub Issues**: Report bugs and request features
3. **Team chat**: Ask questions in development channels
4. **External resources**: MkDocs and Material theme documentation

### Contributing

See the Content Creation Guide and Style Guide for detailed contribution guidelines.

---

**Last Updated**: 2025-10-26  
**Version**: 1.0  
**Maintainer**: FinWiz Documentation Team
