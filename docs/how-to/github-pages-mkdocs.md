# Deploying MkDocs to GitHub Pages

This guide explains how FinWiz documentation is deployed to GitHub Pages using MkDocs instead of Jekyll.

## The Problem

GitHub Pages automatically runs Jekyll on all repositories by default. This causes issues with MkDocs because:

1. Jekyll ignores directories starting with `_` (like `_static/`, `_images/`)
2. Jekyll processes files through its templating engine, which can break MkDocs output
3. Jekyll's processing adds unnecessary overhead

## The Solution: `.nojekyll` File

To disable Jekyll processing, we create a `.nojekyll` file in the root of the built site. This tells GitHub Pages to serve the files as-is without Jekyll processing.

### Automatic Creation — not currently done locally

`make docs-build` does **not** create a `.nojekyll` file. The real target
is:

```makefile
docs-build:
    uv run mkdocs build
```

No `--clean` flag and no `touch site/.nojekyll`. If a `.nojekyll` file ends
up in the deployed site, it's produced by the GitHub Actions workflow
below, not by the local Makefile target.

### GitHub Actions Workflow

There is no `.github/workflows/deploy-docs.yml`. The real workflow is
`.github/workflows/docs.yml`, a 14-line file that defines no build/upload/
deploy jobs of its own — it delegates entirely to a reusable workflow:

```yaml
jobs:
  docs:
    uses: fjacquet/ci/.github/workflows/docs-publish.yml@v1.3.0
    with: { python-version: "3.13" }
```

The actual build/upload/deploy steps (including whether `actions/deploy-pages@v4`
is used) live in that external `fjacquet/ci` repo, not in this repository.

## Verification

After deployment, verify that GitHub Pages is serving MkDocs correctly:

1. **Check deployment**: Visit your GitHub Pages URL
2. **Verify assets**: Ensure CSS, JavaScript, and images load correctly
3. **Test navigation**: Confirm all links work properly
4. **Check search**: Verify the search functionality works

## Deployment Commands

### Local Build

```bash
# Standard build (does not create .nojekyll)
make docs-build

# Strict build — fails on broken refs/missing pages (used by CI)
make docs-build-strict
```

There is no `make docs-build-production` target — the Makefile defines only
`docs-serve`, `docs-build`, `docs-build-strict`, `docs-deploy`, `docs-lint`,
`docs-validate`, and `docs-clean`.

### Manual Deployment

```bash
# Deploy to GitHub Pages (runs `mkdocs gh-deploy --clean`, prompts for confirmation)
make docs-deploy
```

There is no `make docs-deploy-production` target and no staging environment
in this repo.

### Automatic Deployment

Per `.github/workflows/docs.yml`, the `docs` job (delegated to
`fjacquet/ci/.github/workflows/docs-publish.yml@v1.3.0`) runs on:

- **Push to `main`** (when `docs/**`, `mkdocs.yml`, or the workflow file change)
- **Pull requests to `main`** (same path filters)
- **Manual `workflow_dispatch`**

Whether pull-request runs produce a preview URL or a "staging" deployment
is determined inside the external `fjacquet/ci` reusable workflow, not
visible in this repository — don't assume a staging environment exists.

## Troubleshooting

### Assets Not Loading

**Symptom**: CSS, JavaScript, or images return 404 errors

**Solution**: A local `make docs-build` will never produce `site/.nojekyll`
(see "Automatic Creation" above), so checking for it locally isn't a useful
diagnostic. Check the deployed site instead — if this returns 404, Jekyll
processing may be interfering with the deployed output:

```bash
curl -I https://fjacquet.github.io/finwiz/.nojekyll
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
