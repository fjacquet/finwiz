---
inclusion: always
---

# Context7 Integration Standards

## Automatic Documentation Lookup

When working with external libraries or APIs, **automatically use Context7 MCP tools** without waiting for explicit user 
requests.

### When to Use Context7

Use Context7 tools proactively for:

- **Code generation** involving external libraries (CrewAI, Pydantic, pytest, etc.)
- **Setup and configuration** steps for dependencies
- **Library/API documentation** lookups for accurate implementation
- **Version-specific features** to ensure compatibility
- **Best practices** for library usage patterns

### Context7 Workflow

1. **Resolve Library ID** first using `mcp_Context7_resolve_library_id`
   - Search for the library name (e.g., "crewai", "pydantic", "pytest-mock")
   - Select the most relevant match based on context

2. **Get Library Docs** using `mcp_Context7_get_library_docs`
   - Use the resolved library ID from step 1
   - Specify relevant topics when possible (e.g., "flow", "agents", "validation")
   - Adjust token limit based on complexity (default: 5000)

### FinWiz-Specific Libraries

Common libraries in this codebase that benefit from Context7:

- **CrewAI** (`/joaomdmoura/crewai`) - Flow, agents, tasks, crews
- **Pydantic** (`/pydantic/pydantic`) - Validation models, strict mode
- **pytest** (`/pytest-dev/pytest`) - Testing framework
- **pytest-mock** (`/pytest-dev/pytest-mock`) - Mocking (unittest.mock is BANNED)
- **FastAPI** (if used) - API endpoints
- **httpx** - Async HTTP client
- **pandas** - Data manipulation

### Example Usage Pattern

```python
# When implementing CrewAI Flow features:
# 1. Resolve: mcp_Context7_resolve_library_id("crewai")
# 2. Get docs: mcp_Context7_get_library_docs("/joaomdmoura/crewai", topic="flow state management")
# 3. Implement using accurate, up-to-date patterns
```

### Benefits

- **Accuracy**: Use current library APIs and patterns
- **Efficiency**: Avoid deprecated methods or incorrect usage
- **Compliance**: Follow library best practices automatically
- **Version Safety**: Ensure compatibility with installed versions

### Integration with Existing Standards

Context7 documentation should be used **in conjunction with** FinWiz steering rules:

- Validate Context7 patterns against `crewai-standards.md`
- Ensure testing patterns follow `testing-standards.md`
- Apply `validation.md` standards to Pydantic models
- Maintain `tech.md` code quality requirements

## Key Principle

**Proactive, not reactive**: Don't wait for the user to ask for documentation. If you're implementing something that 
involves an external library, automatically fetch the relevant documentation to ensure accuracy.
