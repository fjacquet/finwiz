---
title: Development Standards
inclusion: always
---

# Development Standards

## Dependency Management

- Use latest stable versions of all libraries and dependencies
- Leverage Context7 MCP server to verify compatibility before adding dependencies
- Justify each new dependency with clear business or technical value
- Prefer well-maintained libraries with active communities
- Document version constraints in project files
- Remove unused dependencies regularly
- Use lock files to ensure consistent installations across environments

## Code Quality Standards

- Never create duplicate files with suffixes like `_fixed`, `_clean`, `_backup`, etc.
- Work iteratively on existing files (hooks handle commits automatically)
- Include relevant documentation links in code comments
- Follow language-specific conventions (TypeScript for CDK, Python for Lambda)
- Use meaningful variable and function names
- Keep functions small and focused on single responsibilities
- Implement proper error handling and logging

## File Management

- Maintain clean directory structures
- Use consistent naming conventions across the project
- Avoid temporary or backup files in version control
- Organize code logically by feature or domain
- Keep configuration files at appropriate levels (project vs user)

## Documentation Approach

- Maintain single comprehensive README covering all aspects including deployment
- Reference official sources through MCP servers when available
- Update documentation when upgrading dependencies
- Keep documentation close to relevant code
- Use inline comments for complex business logic
- Document API endpoints and data structures
- Include setup and deployment instructions

## Version Control Integration

### Commit Messages

- Use conventional commit format: `type(scope): description`
- Types: feat, fix, docs, style, refactor, test, chore
- Keep first line under 50 characters
- Use imperative mood ("Add feature" not "Added feature")
- Include body for complex changes

### Branching Strategy

- Use feature branches for new development
- Keep main/master branch stable and deployable
- Use descriptive branch names (feature/user-auth, fix/login-bug)
- Delete merged branches to keep repository clean

### Workflow

- Pull latest changes before starting work
- Commit frequently with logical chunks
- Use interactive rebase to clean up history before merging
- Review code before merging (pull requests)
- Tag releases with semantic versioning

### Repository Management

- Use .gitignore to exclude build artifacts and secrets
- Keep repository size manageable (use Git LFS for large files)
- Document branching strategy in README
- Never commit secrets, API keys, or passwords
- Review commits for sensitive information
- Use signed commits when possible

## Quality Assurance

- Write tests for new functionality
- Run tests before committing changes
- Use linting and formatting tools consistently
- Perform code reviews for all changes
- Monitor code coverage and maintain high standards
