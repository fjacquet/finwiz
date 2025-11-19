# Switching from MkDocs to Jekyll

## Current Situation

Your GitHub Pages site is currently using **MkDocs Material** theme (pre-built HTML in `gh-pages` branch), but your repository is configured for **Jekyll** (with `_config.yml` and dark mode CSS).

## Why Dark Mode Doesn't Work

The dark mode CSS (`assets/css/style.scss`) is for Jekyll, but GitHub Pages is serving the MkDocs site from the `gh-pages` branch, which ignores Jekyll files.

## Solution

Switch GitHub Pages to use Jekyll from the `main` branch instead of the pre-built MkDocs site.

## Steps to Switch

### Option 1: Automated Script (Recommended)

```bash
./scripts/switch-to-jekyll.sh
```

This script will:
1. Delete the local `gh-pages` branch
2. Delete the remote `gh-pages` branch
3. Provide instructions for configuring GitHub Pages

### Option 2: Manual Steps

1. **Delete gh-pages branch:**
   ```bash
   git branch -D gh-pages  # Delete local
   git push origin --delete gh-pages  # Delete remote
   ```

2. **Configure GitHub Pages:**
   - Go to: https://github.com/fjacquet/finwiz/settings/pages
   - Under "Build and deployment":
     - Source: **Deploy from a branch**
     - Branch: **main**
     - Folder: **/docs**
   - Click **Save**

3. **Wait for rebuild:**
   - GitHub will rebuild your site (1-2 minutes)
   - Check the Actions tab for build status

4. **Verify:**
   - Visit: https://fjacquet.github.io/finwiz/
   - Dark mode should work automatically!

## What Changes

### Before (MkDocs)
- ✅ Pre-built HTML in `gh-pages` branch
- ✅ MkDocs Material theme
- ❌ No automatic dark mode
- ❌ Requires separate build process

### After (Jekyll)
- ✅ Built automatically by GitHub Pages
- ✅ Jekyll Minima theme
- ✅ Automatic dark mode (system preference)
- ✅ Simpler workflow (no separate build)

## Files Involved

### Jekyll Configuration
- `_config.yml` - Jekyll site configuration
- `assets/css/style.scss` - Custom CSS with dark mode
- `docs/` - Documentation source files

### Removed
- `gh-pages` branch - Pre-built MkDocs HTML
- No more separate build process

## Dark Mode Features

Once switched to Jekyll, dark mode will:
- ✅ Automatically detect system preference
- ✅ Switch without user interaction
- ✅ Smooth transitions between modes
- ✅ Complete styling (links, code, tables, etc.)
- ✅ GitHub-inspired color scheme

## Testing Dark Mode

After the switch:

1. **macOS**: System Preferences → General → Appearance → Dark
2. **Windows**: Settings → Personalization → Colors → Dark
3. **Browser DevTools**: Toggle dark mode in rendering panel

The site will automatically switch! 🌙

## Rollback (if needed)

If you want to go back to MkDocs:

1. Restore the `gh-pages` branch:
   ```bash
   git checkout -b gh-pages origin/gh-pages
   git push origin gh-pages
   ```

2. Change GitHub Pages settings back to `gh-pages` branch

## Questions?

- **Q: Will my documentation content change?**
  - A: No, the markdown files in `docs/` stay the same

- **Q: Will URLs break?**
  - A: Jekyll uses the same URL structure, so links should work

- **Q: Can I preview locally?**
  - A: Yes! Run `make docs-serve` (requires Jekyll installed)

- **Q: What about the MkDocs theme features?**
  - A: Jekyll Minima is simpler but has all essential features

## Ready to Switch?

Run the script:
```bash
./scripts/switch-to-jekyll.sh
```

Then follow the instructions to configure GitHub Pages settings.

---

**Created**: 2025-11-19  
**Status**: Ready to execute
