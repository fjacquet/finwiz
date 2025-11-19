# GitHub Pages Setup Guide

This guide explains how to configure GitHub Pages for the FinWiz documentation.

## Quick Setup

### 1. Enable GitHub Pages

1. Go to your GitHub repository settings
2. Navigate to **Settings → Pages**
3. Under **Build and deployment**:
   - **Source**: Deploy from a branch
   - **Branch**: `main`
   - **Folder**: `/docs`
4. Click **Save**

### 2. Verify Deployment

After enabling GitHub Pages, GitHub will automatically:

- Build your site using Jekyll
- Deploy to `https://[username].github.io/finwiz`
- Update the deployment status in the repository

You can check deployment status:

- Go to **Actions** tab to see build progress
- Check the **Environments** section for deployment history

### 3. Custom Domain (Optional)

To use a custom domain:

1. Add a `CNAME` file to the `docs/` directory:

   ```bash
   echo "docs.your-domain.com" > docs/CNAME
   ```

2. In GitHub Settings → Pages:
   - Enter your custom domain
   - Enable "Enforce HTTPS"

3. Configure DNS:
   - Add a `CNAME` record pointing to `[username].github.io`
   - Or add `A` records pointing to GitHub Pages IPs

## Local Development

### Preview Documentation

The Makefile provides convenient commands:

```bash
# Start local preview (uses Jekyll if installed, otherwise Python HTTP server)
make docs-serve

# View at http://localhost:8000 (HTTP server) or http://localhost:4000 (Jekyll)
```

### With Jekyll (Recommended)

Install Jekyll for full GitHub Pages compatibility:

```bash
# macOS
brew install ruby
gem install jekyll bundler

# Ubuntu/Debian
sudo apt-get install ruby-full build-essential zlib1g-dev
gem install jekyll bundler

# Then serve
cd docs
jekyll serve --baseurl '' --livereload
```

### Simple HTTP Server

If you don't want to install Jekyll:

```bash
cd docs
python3 -m http.server 8000
```

## Documentation Structure

```
docs/
├── _config.yml           # Jekyll configuration
├── index.md              # Homepage
├── README.md             # Project overview
├── DEVELOPER_GUIDE.md    # Development guide
├── tutorials/            # Learning-oriented guides
├── how-to/               # Problem-solving guides
├── reference/            # Technical references
└── explanations/         # Understanding-oriented content
```

## Key Files

### `_config.yml`

Jekyll configuration at the project root:

- Site metadata (title, description)
- Theme configuration
- Build settings
- Collections and navigation

### `.nojekyll`

Prevents GitHub from ignoring files starting with underscore.

### Front Matter

Add YAML front matter to markdown files:

```yaml
---
layout: default
title: Page Title
---

# Content starts here
```

## Validation

### Lint Markdown

```bash
make docs-lint
```

### Validate Structure

```bash
make docs-validate
```

### CI/CD Validation

GitHub Actions automatically validates documentation on every push:

- Markdown linting
- Broken link checking
- Structure validation
- MkDocs artifact detection

See `.github/workflows/docs-validation.yml`

## Troubleshooting

### Pages Not Building

1. Check **Actions** tab for build errors
2. Verify `docs/` directory contains `index.md`
3. Ensure `_config.yml` is valid YAML
4. Check that branch and folder are correctly configured

### 404 Errors

1. Verify all relative links use correct paths
2. Check file extensions (`.md` vs `.html`)
3. Ensure case sensitivity matches file names

### Styling Issues

1. GitHub Pages uses Jekyll with limited theme support
2. Use the `minima` theme (default) or add custom CSS
3. Test locally with Jekyll before deploying

### Local Preview Not Working

1. Install Jekyll: `gem install jekyll bundler`
2. Or use simple HTTP server: `python3 -m http.server 8000`
3. Check for port conflicts (default: 8000 or 4000)

## Best Practices

1. **Keep docs/ clean**: Remove build artifacts
2. **Use relative links**: For portability
3. **Test locally**: Before pushing
4. **Validate**: Run `make docs-validate`
5. **Follow Diátaxis**: Organize content by purpose

## Resources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [Diátaxis Framework](https://diataxis.fr/)
- [Markdown Guide](https://www.markdownguide.org/)

## Migration from MkDocs

FinWiz previously used MkDocs. The migration to GitHub Pages/Jekyll includes:

### Removed

- `mkdocs.yml` configuration
- `.pages` navigation files
- `docs/includes/` directory
- MkDocs-specific make targets

### Added

- `_config.yml` Jekyll configuration
- `.nojekyll` file
- Simplified make targets
- GitHub Actions validation

### Updated

- All documentation references
- Navigation structure
- Build and deployment process

No changes needed to existing markdown content!
