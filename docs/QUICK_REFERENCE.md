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

### With Jekyll (recommended)

```bash
cd docs
jekyll serve --baseurl '' --livereload
# Visit: http://localhost:4000
```

### With Python

```bash
cd docs
python3 -m http.server 8000
# Visit: http://localhost:8000
```

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

### Enable Pages

1. Settings → Pages
2. Source: Deploy from branch
3. Branch: `main`, Folder: `/docs`
4. Save

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
