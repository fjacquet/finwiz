# Deploying MkDocs to GitHub Pages

This guide explains how FinWiz documentation is deployed to GitHub Pages using MkDocs instead of Jekyll.

## The Problem

GitHub Pages automatically runs Jekyll on all repositories by default. This causes issues with MkDocs because:

1. Jekyll ignores directories starting with `_` (like `_static/`, `_images/`)
2. Jekyll processes files through its templating engine, which can break MkDocs output
3. Jekyll's processing adds unnecessary overhead

## The Solution: `.nojekyll` File

To disable Jekyll processing, we create a `.nojekyll` file in the root of the built site. This tells GitHub Pages to serve the files as-is without Jekyll processing.

### Automatic Creation

The `.nojekyll` file is automatically created during the build process:

**In `scripts/build_docs.py`:**
```python
# Create .nojekyll file to disable GitHub Pages Jekyll processing
nojekyll_file = self.build_dir / ".nojekyll"
nojekyll_file.touch()
```

**In `Makefile`:**
```makefile
docs-build:
	uv run mkdocs build --clean
	touch site/.nojekyll
```

### GitHub Actions Workflow

The `.github/workflows/deploy-docs.yml` workflow is already configured correctly:

1. **Build job**: Builds the site with `.nojekyll` file included
2. **Upload artifact**: Uploads the entire `site/` directory (including `.nojekyll`)
3. **Deploy job**: Deploys to GitHub Pages using `actions/deploy-pages@v4`

## Verification

After deployment, verify that GitHub Pages is serving MkDocs correctly:

1. **Check deployment**: Visit your GitHub Pages URL
2. **Verify assets**: Ensure CSS, JavaScript, and images load correctly
3. **Test navigation**: Confirm all links work properly
4. **Check search**: Verify the search functionality works

## Deployment Commands

### Local Build
```bash
# Standard build (includes .nojekyll)
make docs-build

# Production build with optimization
make docs-build-production
```

### Manual Deployment
```bash
# Deploy to GitHub Pages
make docs-deploy

# Deploy to production with validation
make docs-deploy-production
```

### Automatic Deployment

The documentation is automatically deployed when:

- **Push to main**: Triggers production deployment
- **Pull request**: Triggers staging deployment with preview URL
- **Manual trigger**: Use GitHub Actions workflow dispatch

## Troubleshooting

### Assets Not Loading

**Symptom**: CSS, JavaScript, or images return 404 errors

**Solution**: Verify `.nojekyll` file exists in deployed site:
```bash
# Check locally
ls -la site/.nojekyll

# Check deployed site
curl -I https://your-username.github.io/finwiz/.nojekyll
```

### Search Not Working

**Symptom**: Search returns no results or fails to load

**Solution**: 
1. Verify `search/search_index.json` exists in build
2. Check browser console for JavaScript errors
3. Ensure `.nojekyll` file is present

### Broken Links

**Symptom**: Internal links return 404 errors

**Solution**:
1. Run link validation: `make docs-validate`
2. Check `use_directory_urls` setting in `mkdocs.yml`
3. Verify relative paths in markdown files

## GitHub Pages Configuration

### Repository Settings

1. Go to **Settings** → **Pages**
2. **Source**: Deploy from a branch
3. **Branch**: `gh-pages` (or your deployment branch)
4. **Folder**: `/ (root)`

### Custom Domain (Optional)

If using a custom domain:

1. Add `CNAME` file to `docs/` directory
2. Configure DNS records with your domain provider
3. Enable HTTPS in repository settings

## Best Practices

1. **Always include `.nojekyll`**: Never deploy MkDocs to GitHub Pages without it
2. **Test locally first**: Run `make docs-serve` to preview changes
3. **Validate before deploy**: Run `make docs-validate` to catch issues
4. **Use staging**: Test changes in staging before production deployment
5. **Monitor deployments**: Check GitHub Actions logs for errors

## References

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [MkDocs Deployment Guide](https://www.mkdocs.org/user-guide/deploying-your-docs/)
- [Material for MkDocs Publishing](https://squidfunk.github.io/mkdocs-material/publishing-your-site/)

---

**Last Updated**: 2025-10-27
