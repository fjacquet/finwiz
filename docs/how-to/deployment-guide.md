# Documentation Deployment Guide

This guide covers the comprehensive build system and deployment automation for FinWiz documentation.

## Overview

The documentation deployment system provides:

- **Production Build Pipeline**: Optimized static site generation with asset optimization
- **Deployment Automation**: Automated deployment to GitHub Pages with staging support
- **Zero-Downtime Deployment**: Blue-green deployment strategy for production
- **Build Validation**: Comprehensive validation and error reporting
- **Monitoring**: Deployment status monitoring and health checks

## Quick Start

### Basic Commands

```bash
# Install documentation dependencies
make docs-install

# Build documentation (development)
make docs-build

# Build for production (optimized)
make docs-build-production

# Deploy to production
make docs-deploy-production

# Deploy to staging
make docs-deploy-staging

# Check deployment status
make docs-status
```

## Build System

### Production Build Pipeline

The production build pipeline (`scripts/build_docs.py`) provides:

- **Optimized Static Site Generation**: Uses MkDocs with strict validation
- **Asset Optimization**: Minifies CSS and JavaScript files
- **Compression**: Creates gzip versions of assets for faster loading
- **Build Validation**: Validates HTML structure, links, and content
- **Performance Optimization**: Optimizes images and reduces file sizes

#### Build Options

```bash
# Full production build with optimization
python scripts/build_docs.py

# Fast build without optimization (development)
python scripts/build_docs.py --no-optimize

# Build without strict mode
python scripts/build_docs.py --no-strict

# Custom source and build directories
python scripts/build_docs.py --source docs --build site
```

#### Build Validation

The build system includes comprehensive validation:

- **HTML Structure**: Validates DOCTYPE, head, body, and meta tags
- **Link Checking**: Validates all internal links
- **Asset Validation**: Checks for large files and compression
- **Search Functionality**: Validates search index
- **Performance Metrics**: Monitors build size and file count
- **Accessibility**: Basic accessibility checks

### Makefile Targets

| Target | Description |
|--------|-------------|
| `docs-build` | Standard MkDocs build |
| `docs-build-production` | Optimized production build |
| `docs-build-fast` | Fast build without optimization |
| `docs-validate-build` | Validate built site |
| `docs-validate-build-strict` | Strict validation (fails on warnings) |

## Deployment Automation

### GitHub Pages Deployment

The deployment system supports multiple environments:

- **Production**: Main documentation site (`gh-pages` branch)
- **Staging**: Preview environment (`gh-pages-staging` branch)

#### Deployment Scripts

1. **Standard Deployment** (`scripts/deploy_docs.py`):
   - Pre-deployment validation
   - Automated build and deploy
   - Post-deployment verification
   - Rollback capabilities

2. **Zero-Downtime Deployment** (`scripts/zero_downtime_deploy.py`):
   - Blue-green deployment strategy
   - Backup creation before deployment
   - Comprehensive validation
   - Automatic rollback on failure

#### Deployment Commands

```bash
# Standard deployment
make docs-deploy-production
make docs-deploy-staging

# Zero-downtime deployment
make docs-deploy-zero-downtime
make docs-deploy-zero-downtime-staging

# Force deployment (skip validation)
make docs-deploy-force

# Rollback deployment
make docs-rollback
make docs-rollback-staging
```

### GitHub Actions Workflow

Automated deployment via GitHub Actions (`.github/workflows/deploy-docs.yml`):

- **Automatic Production Deployment**: Triggers on push to `main` branch
- **Staging Deployment**: Triggers on pull requests
- **Manual Deployment**: Workflow dispatch with environment selection
- **PR Comments**: Automatic staging URL comments on pull requests

#### Workflow Features

- **Multi-environment Support**: Production and staging deployments
- **Dependency Management**: Automatic uv and Python setup
- **Build Optimization**: Production-optimized builds
- **Status Reporting**: Deployment status and URLs

## Configuration

### Deployment Configuration

The deployment system uses `docs/deployment-config.yml` for environment settings:

```yaml
environments:
  production:
    name: "Production"
    branch: "gh-pages"
    validation:
      strict: true
      fail_on_warnings: false
    optimization:
      minify_assets: true
      compress_files: true
      
  staging:
    name: "Staging"
    branch: "gh-pages-staging"
    validation:
      strict: false
    optimization:
      minify_assets: false
```

### MkDocs Configuration

Key MkDocs settings for deployment (`mkdocs.yml`):

- **Strict Mode**: Enabled for production builds
- **Site URL**: Configured for GitHub Pages
- **Theme Features**: Optimized for performance
- **Plugin Configuration**: Search, navigation, and schema plugins

## Monitoring and Status

### Deployment Monitoring

The monitoring system (`scripts/monitor_deployment.py`) provides:

- **Site Health Checks**: Accessibility and performance monitoring
- **Deployment History**: Git commit history for deployments
- **Content Validation**: Checks for expected content and structure
- **Response Time Monitoring**: Performance metrics

#### Monitoring Commands

```bash
# Check production status
make docs-status

# Check staging status
make docs-status-staging

# Get status as JSON
make docs-status-json
```

#### Status Information

The monitoring system reports:

- **Site Accessibility**: HTTP status and response time
- **Content Checks**: Title, navigation, search functionality
- **Git Information**: Last commit details and deployment history
- **Health Checks**: Main page, search index, and sitemap validation

### Status Output Example

```
📊 DEPLOYMENT STATUS - PRODUCTION
============================================================
✅ Site is accessible
⚡ Response time: 0.234s
🌐 Status code: 200
📝 Last commit: a1b2c3d4
👤 Author: Developer Name
📅 Date: 2025-01-11 10:30:00
💬 Message: Update documentation

📋 Content Checks:
  ✅ has_title
  ✅ has_navigation
  ✅ has_search
  ✅ has_footer
  ℹ️  content_size_kb: 45.2

🏥 Health Checks:
  ✅ main_page (0.234s)
  ✅ search_index (0.156s)
  ✅ sitemap (0.089s)
```

## Troubleshooting

### Common Issues

1. **Build Failures**:
   - Check MkDocs configuration syntax
   - Validate markdown files for errors
   - Ensure all required dependencies are installed

2. **Deployment Failures**:
   - Verify GitHub Pages is enabled
   - Check repository permissions
   - Validate Git configuration

3. **Site Not Accessible**:
   - Wait for GitHub Pages propagation (up to 10 minutes)
   - Check custom domain configuration
   - Verify HTTPS settings

### Debug Commands

```bash
# Validate documentation before building
make docs-validate

# Build with verbose output
uv run mkdocs build --verbose

# Check Git status
git status
git log --oneline -10

# Test site locally
make docs-serve
```

### Log Files and Reports

The system generates several report files:

- `site/build_report.json`: Build statistics and metrics
- `site/validation_report.json`: Validation results and issues
- `deployment_status.json`: Current deployment status
- `deployment_report_production.json`: Production deployment report
- `deployment_report_staging.json`: Staging deployment report

## Best Practices

### Development Workflow

1. **Local Development**:
   ```bash
   make docs-serve  # Start development server
   # Make changes to documentation
   make docs-validate  # Validate changes
   ```

2. **Testing Changes**:
   ```bash
   make docs-build-production  # Test production build
   make docs-validate-build    # Validate build output
   ```

3. **Deployment**:
   ```bash
   # For major changes, use staging first
   make docs-deploy-staging
   make docs-status-staging
   
   # Then deploy to production
   make docs-deploy-production
   make docs-status
   ```

### Performance Optimization

- **Enable Asset Compression**: Use production build for deployment
- **Monitor File Sizes**: Check build reports for large files
- **Optimize Images**: Compress images before adding to documentation
- **Use Caching**: Enable browser caching for static assets

### Security Considerations

- **Branch Protection**: Protect `gh-pages` branches from direct pushes
- **Access Control**: Limit deployment permissions to authorized users
- **Validation**: Always validate builds before deployment
- **Monitoring**: Regular health checks and status monitoring

## Advanced Features

### Custom Deployment Environments

To add new deployment environments:

1. Update `docs/deployment-config.yml`
2. Create new GitHub Pages branch
3. Update deployment scripts
4. Add Makefile targets

### Integration with CI/CD

The system integrates with:

- **GitHub Actions**: Automated deployment workflows
- **Pre-commit Hooks**: Documentation validation
- **Status Checks**: Build and deployment validation

### Monitoring Integration

Future enhancements may include:

- **Uptime Monitoring**: External service integration
- **Performance Tracking**: Core Web Vitals monitoring
- **Error Tracking**: Automated error detection and reporting
- **Notifications**: Slack/email notifications for deployment events

---

For more information, see the individual script documentation and configuration files.