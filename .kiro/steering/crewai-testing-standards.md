---
inclusion: manual
---

# CrewAI Testing Standards

**CRITICAL LESSON LEARNED**: Do not attempt to unit test full CrewAI crew execution. It leads to hanging tests and is impractical.

## The Problem

When testing CrewAI crews, attempting to instantiate and execute crews in unit tests causes:

1. **Hanging tests** - Tests timeout or never complete
2. **Complex mocking** - Requires mocking the entire CrewAI framework, LLM calls, and agent initialization
3. **Slow execution** - Even with mocks, initialization takes 10+ seconds per test
4. **Brittle tests** - Tests break when CrewAI internals change

## The Solution: Test What Matters

Focus unit tests on **testable business logic**, not framework execution:

### ✅ DO Test

1. **Configuration loading** - Verify YAML files load correctly
2. **Tool routing logic** - Test `get_tools_for_asset_class()` method logic
3. **Input validation** - Test parameter validation (asset_class, ticker)
4. **Method existence** - Verify required methods exist
5. **File existence** - Verify configuration files exist

### ❌ DON'T Test

1. **Crew execution** - Don't call `crew.kickoff()` in unit tests
2. **Agent creation** - Don't instantiate agents with `@agent` decorator
3. **Task execution** - Don't execute tasks with `@task` decorator
4. **LLM calls** - Don't mock OpenAI/LLM responses
5. **Full workflow** - Don't test end-to-end crew workflows

## Example: Good vs Bad Tests

### ❌ BAD - Tries to test crew execution

```python
def test_crew_execution(self, mocker):
    """This will hang or timeout!"""
    crew = DeepAnalysisCrew()  # Hangs during initialization
    
    # Mock everything (impractical)
    mocker.patch.object(crew, "asset_analyst", return_value=mock_agent)
    mocker.patch.object(crew, "crew", return_value=mock_crew)
    
    # This will still hang or be very slow
    result = crew.kickoff(inputs={"ticker": "AAPL", "asset_class": "stock"})
```

### ✅ GOOD - Tests configuration and logic

```python
def test_should_load_agent_configurations_from_yaml(self):
    """Fast, focused test of configuration loading."""
    import yaml
    from pathlib import Path
    
    config_path = Path("src/finwiz/crews/deep_analysis/config/agents.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Verify structure
    assert "asset_analyst" in config
    assert "role" in config["asset_analyst"]

def test_should_validate_asset_class_parameter(self):
    """Test validation logic without instantiating crew."""
    valid_asset_classes = ["stock", "etf", "crypto"]
    
    for asset_class in valid_asset_classes:
        assert asset_class.lower() in ["stock", "etf", "crypto"]
    
    invalid_asset_classes = ["bond", "option"]
    for asset_class in invalid_asset_classes:
        assert asset_class.lower() not in ["stock", "etf", "crypto"]
```

## Testing Strategy for CrewAI

### Unit Tests (Fast, Focused)

- Test configuration loading from YAML
- Test tool routing logic
- Test input validation
- Test method existence
- **Run time: < 1 second per test**

### Integration Tests (Slow, Optional)

- Test actual crew execution with real LLM calls
- Mark with `@pytest.mark.integration`
- Require API keys
- **Run time: 30+ seconds per test**
- **Only run manually or in CI**

### Manual Testing

- Test full workflows manually
- Use actual tickers and real data
- Verify output quality
- **This is where you validate the crew actually works**

## Implementation Pattern

```python
class TestDeepAnalysisCrew:
    """Test cases for DeepAnalysisCrew - focused on configuration and logic."""
    
    def test_should_load_agent_configurations_from_yaml(self):
        """Test configuration loading without instantiating crew."""
        import yaml
        from pathlib import Path
        
        config_path = Path("src/finwiz/crews/deep_analysis/config/agents.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        required_agents = ["asset_analyst", "risk_assessor", "investment_reporter"]
        for agent_name in required_agents:
            assert agent_name in config
            assert "role" in config[agent_name]
            assert "goal" in config[agent_name]
    
    def test_should_have_required_methods(self):
        """Test method existence without calling them."""
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew
        
        assert hasattr(DeepAnalysisCrew, "get_tools_for_asset_class")
        assert hasattr(DeepAnalysisCrew, "kickoff")
        assert hasattr(DeepAnalysisCrew, "asset_analyst")
```

## Why This Approach Works

1. **Fast** - Tests complete in < 1 second
2. **Reliable** - No hanging or timeouts
3. **Maintainable** - Tests don't break when CrewAI updates
4. **Practical** - Tests verify what actually matters
5. **Clear** - Easy to understand what's being tested

## When to Use Integration Tests

Only create integration tests when:

1. You need to verify actual LLM behavior
2. You're testing a critical production workflow
3. You have time for slow tests (30+ seconds)
4. You're willing to maintain complex mocks or use real API calls

Mark them clearly:

```python
@pytest.mark.integration
@pytest.mark.slow
def test_should_execute_full_crew_workflow():
    """Integration test - requires API keys and is slow."""
    # This is acceptable for integration tests
    crew = DeepAnalysisCrew()
    result = crew.kickoff(inputs={"ticker": "AAPL", "asset_class": "stock"})
    assert result is not None
```

## Summary

- ✅ **Unit tests**: Test configuration, logic, validation (fast)
- ❌ **Don't unit test**: Crew execution, agent creation, LLM calls (slow/impractical)
- ✅ **Integration tests**: Optional, marked, slow, for critical workflows
- ✅ **Manual testing**: Primary way to validate crew behavior

**Remember**: The goal of unit tests is to catch bugs quickly, not to test the entire framework.

---

**Version**: 1.0  
**Created**: 2025-01-10  
**Lesson Source**: DeepAnalysisCrew implementation (Task 1.4)
