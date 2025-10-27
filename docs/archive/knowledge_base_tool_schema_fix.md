# Knowledge Base Tool Schema Validation Fix

**Date:** 2025-10-02  
**Issue:** Pydantic validation error when using the Knowledge base tool  
**Status:** ✅ Fixed

## Problem

The `Knowledge base` tool (powered by `crewai_tools.RagTool`) was failing with Pydantic validation errors:

```
Arguments validation failed: 2 validation errors for RagToolSchema
similarity_threshold
  Field required [type=missing, ...]
limit
  Field required [type=missing, ...]
```

### Root Cause

The `crewai_tools.RagTool` has a bug in its auto-generated Pydantic schema where `similarity_threshold` and `limit` parameters are marked as `required=True` even though they have default values of `None` in the `_run()` method signature:

```python
def _run(self, query: str, similarity_threshold: float | None = None, limit: int | None = None) -> str
```

The schema incorrectly shows:

```python
{
    'query': FieldInfo(annotation=str, required=True),
    'similarity_threshold': FieldInfo(annotation=Union[float, NoneType], required=True),  # ❌ Should be False
    'limit': FieldInfo(annotation=Union[int, NoneType], required=True)  # ❌ Should be False
}
```

## Solution

Created a wrapper tool `KnowledgeBaseTool` that:

1. **Defines correct Pydantic schema** with optional parameters
2. **Delegates to the underlying RagTool** for actual functionality
3. **Maintains the same interface** for all crews

### Implementation

**File:** `src/finwiz/tools/rag_tools.py`

```python
class KnowledgeBaseInput(BaseModel):
    """Input schema for Knowledge Base tool with optional parameters."""

    query: str = Field(..., description="Search query for the knowledge base")
    similarity_threshold: float | None = Field(
        default=None,
        description="Minimum similarity score for results (0.0 to 1.0)",
    )
    limit: int | None = Field(
        default=None,
        description="Maximum number of results to return",
    )


class KnowledgeBaseTool(Tool):
    """
    Wrapper around RagTool that fixes the schema validation issue.
    """

    name: str = "Knowledge base"
    description: str = (
        "Use this tool to retrieve information from the FinWiz knowledge base. "
        "Ask questions about financial data, market trends, or previously "
        "researched information."
    )
    args_schema: type[BaseModel] = KnowledgeBaseInput
    _rag_tool: Any = None

    def __init__(self, rag_tool: RagTool) -> None:
        """Initialize with an underlying RagTool instance."""
        super().__init__()
        self._rag_tool = rag_tool

    def _run(
        self,
        query: str,
        similarity_threshold: float | None = None,
        limit: int | None = None,
    ) -> str:
        """Execute the RAG query with optional parameters."""
        return self._rag_tool._run(
            query=query,
            similarity_threshold=similarity_threshold,
            limit=limit,
        )
```

### Updated `get_rag_tools()` Function

```python
def get_rag_tools(collection_suffix: str | None = None) -> list[Tool]:
    # Create the underlying RAG tool for retrieval
    underlying_rag_tool = RagTool(config=config, summarize=True)

    # Wrap it with our custom tool that has the correct schema
    knowledge_base_tool = KnowledgeBaseTool(rag_tool=underlying_rag_tool)

    # Create the SaveToRag tool for storage
    save_to_rag_tool = SaveToRagTool(rag_tool=underlying_rag_tool)

    return [knowledge_base_tool, save_to_rag_tool]
```

## Testing

Created comprehensive unit tests in `tests/unit/tools/test_knowledge_base_tool.py`:

- ✅ Schema validation with only query parameter
- ✅ Schema validation with query and similarity_threshold
- ✅ Schema validation with all parameters
- ✅ Correct field definitions (required vs optional)
- ✅ Missing query parameter raises ValidationError
- ✅ Tool structure and naming

All tests pass successfully.

## Impact

### Affected Components

All crews using RAG tools are now fixed:

- ✅ Stock Crew (`collection_suffix="stock"`)
- ✅ ETF Crew (`collection_suffix="etf"`)
- ✅ Crypto Crew (`collection_suffix="crypto"`)
- ✅ Report Crew (`collection_suffix="report"`)
- ✅ Portfolio Rebalancing Crew (`collection_suffix="portfolio_rebalancing"`)
- ✅ Investment Discovery Crew (`collection_suffix="investment_discovery"`)

### Backward Compatibility

✅ **Fully backward compatible** - No changes required to existing crew configurations or agent definitions.

## Usage Examples

### Basic Query (Only Required Parameter)

```python
tools = get_rag_tools()
kb_tool = tools[0]

# This now works without validation errors
result = kb_tool._run(query="What are the technical indicators for Bitcoin?")
```

### Query with Similarity Threshold

```python
result = kb_tool._run(
    query="What are the technical indicators for Bitcoin?",
    similarity_threshold=0.75
)
```

### Query with All Parameters

```python
result = kb_tool._run(
    query="What are the technical indicators for Bitcoin?",
    similarity_threshold=0.75,
    limit=5
)
```

## Verification

Run the test suite to verify the fix:

```bash
# Run unit tests for the Knowledge Base tool
uv run pytest tests/unit/tools/test_knowledge_base_tool.py -v

# Run all RAG-related tests
uv run pytest tests/unit/tools/test_rag_tools.py -v
```

## Future Considerations

This is a **workaround** for a bug in the upstream `crewai_tools` library. Consider:

1. **Report the issue** to the crewai_tools maintainers
2. **Monitor for upstream fix** and remove wrapper when fixed
3. **Keep tests** to ensure the fix remains effective

## References

- **Issue:** Pydantic validation error for RagToolSchema
- **Files Modified:**
  - `src/finwiz/tools/rag_tools.py` (added KnowledgeBaseTool wrapper)
  - `tests/unit/tools/test_rag_tools.py` (added schema validation tests)
  - `tests/unit/tools/test_knowledge_base_tool.py` (new comprehensive test file)
- **Pydantic Documentation:** <https://errors.pydantic.dev/2.11/v/missing>
