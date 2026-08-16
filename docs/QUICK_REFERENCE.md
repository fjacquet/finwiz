# Documentation Quick Reference

Quick reference for working with FinWiz documentation.

## Commands

```bash
# Preview documentation locally
make docs-serve

# Lint markdown files
make docs-lint

# Validate structure and links
make docs-validate

# Clean build artifacts
make docs-clean
```

## Local Preview

```bash
make docs-serve
# Visit: http://127.0.0.1:8000
```

This runs `mkdocs serve` with live reload. Serving the raw `docs/` directory
over `python3 -m http.server` will not work — the site needs building, since
the nav, the Material theme, and the mermaid diagrams all come from
`mkdocs.yml`.

## File Organization

```
docs/
├── index.md              # Homepage
├── tutorials/            # Learning guides
├── how-to/               # Problem-solving
├── reference/            # Technical docs
└── explanations/         # Concepts
```

## Adding Documentation

### 1. Create Markdown File

```bash
# Choose the right category
docs/tutorials/my-tutorial.md
docs/how-to/my-guide.md
docs/reference/my-api.md
docs/explanations/my-concept.md
```

### 2. Add Front Matter

```yaml
---
layout: default
title: My Page Title
---

# Content starts here
```

### 3. Link from Index

Update `docs/index.md` to link to your new page.

## Writing Guidelines

### Diátaxis Framework

- **Tutorials**: Step-by-step lessons ("How to get started")
- **How-To**: Problem-solving guides ("How to configure X")
- **Reference**: Technical specifications ("API documentation")
- **Explanations**: Concepts and discussions ("Why we use X")

### Markdown Best Practices

```markdown
# Use ATX-style headers

- Use hyphens for lists
- Not asterisks

Use `backticks` for inline code

```python
# Use fenced code blocks
def hello():
    print("World")
```

[Use descriptive link text](index.md)

```

## Links

### Internal Links (Relative)
```markdown
[Developer Guide](development/DEVELOPER_GUIDE.md)
[Tutorial](tutorials/getting_started.md)
[Reference](reference/API_REFERENCE.md)
```

### External Links

```markdown
[GitHub](https://github.com/fjacquet/finwiz)
```

## GitHub Pages

### How publishing works

Pages is published by the `Docs` workflow
(`.github/workflows/docs.yml`), which builds the MkDocs site and uploads it as
a Pages artifact. It runs on pushes to `main` that touch `docs/**` or
`mkdocs.yml`, and can be triggered manually.

Set **Settings → Pages → Source** to **GitHub Actions**, not "Deploy from
branch". Serving `/docs` from a branch would publish raw markdown instead of
the built site.

### Check Deployment

- Actions tab → See build progress
- Environments → Deployment history
- Visit: `https://[username].github.io/finwiz`

## Validation

### Before Commit

```bash
# Check markdown style
make docs-lint

# Validate structure
make docs-validate

# Preview changes
make docs-serve
```

### CI/CD

- Automatic validation on push
- Check Actions tab for status
- Fix any errors before merging

## Common Issues

### 404 Errors

- Check file paths are correct
- Ensure case sensitivity matches
- Use relative links without leading `/`

### Styling Issues

- Test locally with Jekyll
- Add custom CSS if needed
- Keep styling simple

### Build Failures

- Check Actions tab for errors
- Validate YAML front matter
- Ensure all links are valid

## Resources

- [Setup Guide](how-to/github-pages-mkdocs.md) - Detailed setup instructions
- [Developer Guide](development/DEVELOPER_GUIDE.md) - Development guidelines
- [GitHub Pages Docs](https://docs.github.com/en/pages)
- [Diátaxis Framework](https://diataxis.fr/)
