# MkDocs Troubleshooting Guide

This guide provides solutions to common issues encountered when working with the FinWiz MkDocs documentation site.

## Quick Diagnostics

### Health Check Commands

Run these commands to quickly identify issues:

```bash
# Check documentation health
make docs-validate

# Validate build
make docs-build

# Check for linting issues
make docs-lint

# Verbose build for detailed errors
uv run mkdocs build --verbose
```

### Common Error Patterns

| Error Type | Quick Fix | Section |
|------------|-----------|---------|
| Build fails | Check syntax, links | [Build Issues](#build-issues) |
| Navigation missing | Check `.pages` files | [Navigation Issues](#navigation-issues) |
| Search not working | Rebuild site | [Search Issues](#search-issues) |
| Deployment fails | Check permissions | [Deployment Issues](#deployment-issues) |
| Slow performance | Optimize images | [Performance Issues](#performance-issues) |

## Build Issues

### Build Fails with Syntax Errors

#### Symptom

```
Error: Invalid YAML syntax in mkdocs.yml
```

#### Diagnosis

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('mkdocs.yml'))"

# Check markdown syntax
make docs-lint
```

#### Solutions

1. **YAML syntax errors**:

   ```bash
   # Common issues:
   # - Missing quotes around special characters
   # - Incorrect indentation
   # - Missing colons or dashes

   # Fix example:
   # Wrong:
   site_name: FinWiz Documentation: AI Platform

   # Correct:
   site_name: "FinWiz Documentation: AI Platform"
   ```

2. **Markdown syntax errors**:

   ```bash
   # Check specific file
   markdownlint docs/path/to/file.md

   # Common fixes:
   # - Add language to code blocks
   # - Fix heading hierarchy
   # - Close unclosed elements
   ```

### Build Fails with Missing Files

#### Symptom

```
Error: Documentation file 'path/to/file.md' does not exist
```

#### Diagnosis

```bash
# Check if file exists
ls -la docs/path/to/file.md

# Check navigation configuration
grep -r "file.md" docs/.pages mkdocs.yml
```

#### Solutions

1. **Create missing file**:

   ```bash
   touch docs/path/to/file.md
   echo "# Placeholder" > docs/path/to/file.md
   ```

2. **Remove from navigation**:

   ```yaml
   # In .pages or mkdocs.yml, remove or comment out:
   # - missing-file.md
   ```

3. **Fix file path**:

   ```yaml
   # Check for typos in navigation
   nav:
     - "Correct Path": correct-path.md
   ```

### Plugin Errors

#### Symptom

```
Error: Plugin 'plugin-name' not found
```

#### Diagnosis

```bash
# Check installed plugins
uv run pip list | grep mkdocs

# Check plugin configuration
grep -A 5 "plugins:" mkdocs.yml
```

#### Solutions

1. **Install missing plugin**:

   ```bash
   uv add mkdocs-plugin-name --group docs
   ```

2. **Remove unused plugin**:

   ```yaml
   # In mkdocs.yml, comment out or remove:
   plugins:
     # - unused-plugin
   ```

3. **Check plugin compatibility**:

   ```bash
   # Update to compatible version
   uv add mkdocs-material@latest --group docs
   ```

## Navigation Issues

### Pages Not Appearing in Navigation

#### Symptom

- Files exist but don't show in site navigation
- Navigation structure doesn't match expected layout

#### Diagnosis

```bash
# Check .pages files
find docs -name ".pages" -exec cat {} \;

# Check mkdocs.yml navigation
grep -A 20 "nav:" mkdocs.yml

# Verify file locations
find docs -name "*.md" | head -20
```

#### Solutions

1. **Add to .pages file**:

   ```yaml
   # docs/tutorials/.pages
   nav:
     - Getting Started: getting-started.md
     - New Tutorial: new-tutorial.md
   ```

2. **Add to mkdocs.yml**:

   ```yaml
   nav:
     - Home: index.md
     - Tutorials:
       - tutorials/getting-started.md
       - tutorials/new-tutorial.md
   ```

3. **Check file naming**:

   ```bash
   # Ensure files use correct naming convention
   # Use hyphens, not underscores or spaces
   mv "file name.md" "file-name.md"
   ```

### Navigation Order Issues

#### Symptom

- Pages appear in wrong order
- Navigation doesn't follow intended hierarchy

#### Solutions

1. **Use .pages for custom ordering**:

   ```yaml
   # docs/.pages
   nav:
     - index.md
     - Tutorials: tutorials/
     - How-to Guides: how-to/
     - Reference: reference/
     - Explanations: explanations/
   ```

2. **Use explicit ordering in subdirectories**:

   ```yaml
   # docs/tutorials/.pages
   nav:
     - "Getting Started": getting-started.md
     - "First Analysis": first-analysis.md
     - "Advanced Topics": advanced-topics.md
   ```

## Search Issues

### Search Returns No Results

#### Symptom

- Search box appears but returns no results
- Search functionality completely broken

#### Diagnosis

```bash
# Check search plugin configuration
grep -A 5 "search:" mkdocs.yml

# Check if search index was built
ls -la site/search/

# Test build process
make docs-build
```

#### Solutions

1. **Rebuild search index**:

   ```bash
   # Clean and rebuild
   make docs-clean
   make docs-build
   ```

2. **Check search plugin configuration**:

   ```yaml
   plugins:
     - search:
         separator: '[\s\-,:!=\[\]()"`/]+|\.(?!\d)|&[lg]t;|(?!\b)(?=[A-Z][a-z])'
         lang: en
   ```

3. **Clear browser cache**:

   ```bash
   # Hard refresh in browser
   # Ctrl+Shift+R (Windows/Linux)
   # Cmd+Shift+R (macOS)
   ```

### Search Results Incomplete

#### Symptom

- Some pages don't appear in search results
- Search results seem outdated

#### Solutions

1. **Check content indexing**:

   ```bash
   # Ensure all markdown files are valid
   find docs -name "*.md" -exec head -1 {} \;
   ```

2. **Verify search configuration**:

   ```yaml
   plugins:
     - search:
         prebuild_index: true  # For better performance
   ```

3. **Check for search exclusions**:

   ```yaml
   # Remove search exclusions if present
   plugins:
     - search:
         # exclude:
         #   - archive/*
   ```

## Deployment Issues

### GitHub Pages Deployment Fails

#### Symptom

```
Error: Permission denied (publickey)
Error: Failed to deploy to GitHub Pages
```

#### Diagnosis

```bash
# Check repository permissions
git remote -v

# Check GitHub Pages settings
# Visit: https://github.com/username/repo/settings/pages

# Check deployment logs
# Visit: https://github.com/username/repo/actions
```

#### Solutions

1. **Fix repository permissions**:

   ```bash
   # Ensure you have write access to repository
   # Check GitHub Pages source branch setting
   ```

2. **Configure deployment key**:

   ```bash
   # Generate SSH key if needed
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

   # Add to GitHub repository deploy keys
   ```

3. **Use HTTPS instead of SSH**:

   ```bash
   git remote set-url origin https://github.com/username/repo.git
   ```

### Custom Domain Issues

#### Symptom

- Custom domain not working
- SSL certificate errors
- DNS resolution failures

#### Solutions

1. **Configure DNS records**:

   ```
   # Add CNAME record pointing to username.github.io
   # Or A records pointing to GitHub Pages IPs:
   185.199.108.153
   185.199.109.153
   185.199.110.153
   185.199.111.153
   ```

2. **Configure CNAME file**:

   ```bash
   # Create docs/CNAME file
   echo "docs.finwiz.com" > docs/CNAME
   ```

3. **Enable HTTPS**:

   ```bash
   # In GitHub repository settings:
   # Settings > Pages > Enforce HTTPS
   ```

### Deployment Timeout

#### Symptom

```
Error: Deployment timed out
Error: Build process exceeded time limit
```

#### Solutions

1. **Optimize build process**:

   ```bash
   # There is no `make docs-build-fast` target — the only build targets are
   # docs-build and docs-build-strict
   make docs-build

   # Optimize images
   find docs -name "*.png" -exec optipng {} \;
   ```

2. **Reduce site size**:

   ```bash
   # Check site size
   du -sh site/

   # Remove large files
   find docs -size +1M -type f
   ```

## Performance Issues

### Slow Page Load Times

#### Symptom

- Pages take > 3 seconds to load
- Poor Lighthouse scores
- Users report slow experience

#### Diagnosis

```bash
# Check site size
du -sh site/

# Check image sizes
find docs -name "*.png" -o -name "*.jpg" | xargs ls -lh

# Test build time
time make docs-build
```

#### Solutions

1. **Optimize images**:

   ```bash
   # Compress PNG images
   find docs -name "*.png" -exec optipng -o2 {} \;

   # Compress JPEG images
   find docs -name "*.jpg" -exec jpegoptim --max=85 {} \;

   # Convert to WebP (if supported)
   find docs -name "*.png" -exec cwebp -q 80 {} -o {}.webp \;
   ```

2. **Enable compression**:

   ```yaml
   # In mkdocs.yml
   plugins:
     - minify:
         minify_html: true
         minify_css: true
         minify_js: true
   ```

3. **Optimize theme configuration**:

   ```yaml
   theme:
     features:
       - navigation.instant      # Faster navigation
       - navigation.prefetch     # Prefetch pages
   ```

### Slow Build Times

#### Symptom

- `mkdocs build` takes > 30 seconds
- Development server slow to start
- CI/CD builds timeout

#### Solutions

1. **Use incremental builds**:

   ```bash
   # Development server with auto-reload
   mkdocs serve --dirtyreload
   ```

2. **Optimize plugin configuration**:

   ```yaml
   plugins:
     - search:
         prebuild_index: false  # Faster builds
   ```

3. **Exclude unnecessary files**:

   ```yaml
   # In mkdocs.yml
   exclude_docs: |
     archive/
     drafts/
     *.tmp
   ```

## Content Issues

### Broken Links

#### Symptom

- Links return 404 errors
- Internal links don't work
- External links are dead

#### Diagnosis

```bash
# Check for broken links
make docs-validate

# Manual link checking
grep -r "](.*\.md)" docs/

# Check external links
grep -r "](http" docs/
```

#### Solutions

1. **Fix internal links**:

   ```markdown
   # Use relative paths
   [Link text](../reference/api.md)

   # Include file extensions
   [Link text](guide.md) not [Link text](guide)
   ```

2. **Update external links**:

   ```bash
   # Check if external sites moved
   curl -I https://example.com/old-url

   # Update to new URLs
   ```

3. **Use link checking tools**:

   ```bash
   # Install link checker
   npm install -g markdown-link-check

   # Check specific file
   markdown-link-check docs/path/to/file.md
   ```

### Images Not Displaying

#### Symptom

- Images show as broken links
- Alt text displays instead of images
- Images work locally but not in production

#### Solutions

1. **Check image paths**:

   ```markdown
   # Use relative paths from current file
   ![Alt text](../assets/image.png)

   # Not absolute paths
   ![Alt text](/assets/image.png)
   ```

2. **Verify image files exist**:

   ```bash
   # Check if image files are committed
   git ls-files | grep -E "\.(png|jpg|jpeg|gif|svg)$"
   ```

3. **Check image formats**:

   ```bash
   # Ensure supported formats
   # Supported: PNG, JPG, JPEG, GIF, SVG, WebP
   ```

### Code Examples Not Working

#### Symptom

- Code blocks not syntax highlighted
- Code examples produce errors when run
- Copy button not working

#### Solutions

1. **Add language specification**:

   ```markdown
   ```python
   # Python code here
   def example():
       return "Hello"
   ```

   ```bash
   # Shell commands here
   make docs-serve
   ```

   ```

2. **Test code examples**:

   ```bash
   # Extract and test code blocks
   grep -A 10 "```python" docs/file.md
   ```

3. **Enable code copy feature**:

   ```yaml
   theme:
     features:
       - content.code.copy
   ```

## Development Environment Issues

### Dependencies Not Installing

#### Symptom

```
Error: Could not find a version that satisfies the requirement
Error: Package not found
```

#### Solutions

1. **Update package manager**:

   ```bash
   # Update uv
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Sync dependencies
   uv sync --group docs
   ```

2. **Clear cache**:

   ```bash
   # Clear uv cache
   uv cache clean

   # Reinstall dependencies
   uv sync --group docs --reinstall
   ```

3. **Check Python version**:

   ```bash
   # Ensure compatible Python version
   python --version

   # Must be 3.13.x — pyproject.toml pins requires-python = ">=3.13,<3.14"
   ```

### Development Server Issues

#### Symptom

- Server won't start
- Hot reload not working
- Port conflicts

#### Solutions

1. **Check port availability**:

   ```bash
   # Check if port 8000 is in use
   lsof -i :8000

   # Use different port
   mkdocs serve --dev-addr 127.0.0.1:8001
   ```

2. **Fix file watching**:

   ```bash
   # Increase file watch limit (Linux)
   echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
   sudo sysctl -p
   ```

3. **Clear browser cache**:

   ```bash
   # Hard refresh browser
   # Check browser developer tools for errors
   ```

## Getting Help

### Diagnostic Information

When reporting issues, include:

```bash
# System information
uv --version
python --version
mkdocs --version

# Project information
cat mkdocs.yml | head -20
ls -la docs/

# Error output
make docs-build 2>&1 | tee build-error.log
```

### Support Channels

1. **Internal Documentation**:
   - Check this troubleshooting guide
   - Review setup and deployment guide
   - Consult content creation guide

2. **Team Support**:
   - Create GitHub issue with diagnostic information
   - Ask in team chat with error details
   - Request pair debugging session

3. **External Resources**:
   - [MkDocs Documentation](https://www.mkdocs.org/)
   - [Material Theme Docs](https://squidfunk.github.io/mkdocs-material/)
   - [GitHub Pages Documentation](https://docs.github.com/en/pages)

### Escalation Process

1. **Self-service**: Check this guide and documentation
2. **Team help**: Ask team members or create issue
3. **Maintainer support**: Contact documentation maintainer
4. **External support**: Consult official documentation and communities

---

**Last Updated**: 2025-10-26
**Version**: 1.0
**Maintainer**: FinWiz Documentation Team
