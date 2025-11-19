# MkDocs Quick Start Guide

## TL;DR

```bash
# Preview docs locally
make docs-serve

# Build docs
make docs-build

# Deploy to GitHub Pages
make docs-deploy
```

## Common Tasks

### Start Local Server

```bash
make docs-serve
# Open http://127.0.0.1:8000
```

### Add New Page

1. Create markdown file in `docs/`
2. Add to `mkdocs.yml` nav section
3. Preview with `make docs-serve`

### Deploy Changes

Push to main branch - GitHub Actions deploys automatically!

Or manually:

```bash
make docs-deploy
```

## Writing Tips

### Callout Boxes

```markdown
!!! note "Title (optional)"
    Important information

!!! tip
    Helpful hint

!!! warning
    Caution advised

!!! danger
    Critical warning
```

### Code Blocks

````markdown
```python
def example():
    return "Code with syntax highlighting"
```
````

### Diagrams

````markdown
```mermaid
graph LR
    A[Start] --> B[End]
```
````

### Tabs

```markdown
=== "Python"
    Python code here

=== "JavaScript"
    JS code here
```

### Links

```markdown
[Internal link](../reference/api.md)
[External link](https://example.com)
```

## Features

- ✅ Light/Dark mode
- ✅ Live reload
- ✅ Search
- ✅ Code highlighting
- ✅ Mermaid diagrams
- ✅ Math support
- ✅ Mobile responsive
- ✅ Auto-deploy

## Help

- Full docs: [MKDOCS_SETUP.md](MKDOCS_SETUP.md)
- Migration guide: [MKDOCS_MIGRATION.md](MKDOCS_SETUP.md)
- Material theme: https://squidfunk.github.io/mkdocs-material/
