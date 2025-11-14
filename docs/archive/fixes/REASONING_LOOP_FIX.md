# Reasoning Loop Issue - Fix Guide

## Problem Identified

Your **Portfolio Optimization Strategist** (rebalancing_strategist agent) is stuck in an infinite reasoning loop at attempt 49. This is a critical issue that needs immediate attention.

## Root Cause

The agent has `reasoning=True` enabled but **NO `max_reasoning_attempts` limit** configured. This allows it to loop indefinitely when it can't reach a conclusion.

### Current Configuration (BROKEN)

```python
# src/finwiz/crews/portfolio_rebalancing_crew/portfolio_rebalancing_crew.py:169
@agent
def rebalancing_strategist(self) -> Agent:
    """Agent that generates optimal rebalancing trade recommendations."""
    return Agent(
        config=self.agents_config["rebalancing_strategist"],
        verbose=True,
        tools=holding_analysis_tools,
        reasoning=True,  # ⚠️ ENABLED WITHOUT LIMIT
    )
```

## Immediate Fix (Apply Now)

### Option 1: Add Reasoning Limit (Recommended)

```python
@agent
def rebalancing_strategist(self) -> Agent:
    """Agent that generates optimal rebalancing trade recommendations."""
    return Agent(
        config=self.agents_config["rebalancing_strategist"],
        verbose=True,
        tools=holding_analysis_tools,
        reasoning=True,
        max_reasoning_attempts=3,  # ✅ ADD THIS LINE
    )
```

### Option 2: Disable Reasoning (Quick Fix)

```python
@agent
def rebalancing_strategist(self) -> Agent:
    """Agent that generates optimal rebalancing trade recommendations."""
    return Agent(
        config=self.agents_config["rebalancing_strategist"],
        verbose=True,
        tools=holding_analysis_tools,
        reasoning=False,  # ✅ DISABLE REASONING
    )
```

## All Affected Agents

The following agents in `portfolio_rebalancing_crew.py` have the same issue:

### 1. holding_analyzer (Line 127)
```python
# BEFORE (BROKEN)
reasoning=True,

# AFTER (FIXED)
reasoning=True,
max_reasoning_attempts=3,
```

### 2. price_target_specialist (Line 136)
```python
# BEFORE (BROKEN)
reasoning=True,

# AFTER (FIXED)
reasoning=True,
max_reasoning_attempts=3,
```

### 3. alternative_researcher (Line 145)
```python
# BEFORE (BROKEN)
reasoning=True,

# AFTER (FIXED)
reasoning=True,
max_reasoning_attempts=3,
```

### 4. portfolio_analyst (Line 154)
```python
# BEFORE (BROKEN)
reasoning=True,

# AFTER (FIXED)
reasoning=True,
max_reasoning_attempts=3,
```

### 5. rebalancing_strategist (Line 169)
```python
# BEFORE (BROKEN)
reasoning=True,

# AFTER (FIXED)
reasoning=True,
max_reasoning_attempts=3,
```

### 6. risk_manager (Line 178)
```python
# BEFORE (BROKEN)
reasoning=True,

# AFTER (FIXED)
reasoning=True,
max_reasoning_attempts=3,
```

## Why This Happens

### Reasoning Loop Causes:
1. **Ambiguous Task Description** - Agent can't determine when it's "done"
2. **Insufficient Context** - Missing data needed to complete reasoning
3. **Tool Failures** - Tools returning errors, agent keeps retrying
4. **Complex Decision Tree** - Too many possible paths to explore
5. **No Exit Condition** - Agent doesn't know when to stop reasoning

### Why max_reasoning_attempts=3 is Recommended:
- **Attempt 1:** Initial reasoning and tool selection
- **Attempt 2:** Refine approach based on tool results
- **Attempt 3:** Final decision with available data
- **After 3:** Force completion with best available answer

## Complete Fix Implementation

### Step 1: Update All Agents

Edit `src/finwiz/crews/portfolio_rebalancing_crew/portfolio_rebalancing_crew.py`:

```python
@agent
def holding_analyzer(self) -> Agent:
    """Agent that coordinates deep analysis for individual holdings."""
    return Agent(
        config=self.agents_config["holding_analyzer"],
        verbose=True,
        reasoning=True,
        max_reasoning_attempts=3,  # ✅ ADD THIS
        tools=holding_analysis_tools,
    )

@agent
def price_target_specialist(self) -> Agent:
    """Agent that calculates actionable buy/sell price targets."""
    return Agent(
        config=self.agents_config["price_target_specialist"],
        verbose=True,
        reasoning=True,
        max_reasoning_attempts=3,  # ✅ ADD THIS
        tools=holding_analysis_tools,
    )

@agent
def alternative_researcher(self) -> Agent:
    """Agent that finds better alternatives for underperforming holdings."""
    return Agent(
        config=self.agents_config["alternative_researcher"],
        verbose=True,
        reasoning=True,
        max_reasoning_attempts=3,  # ✅ ADD THIS
        tools=holding_analysis_tools,
    )

@agent
def portfolio_analyst(self) -> Agent:
    """Agent that analyzes current portfolio composition and calculates weightings."""
    return Agent(
        config=self.agents_config["portfolio_analyst"],
        verbose=True,
        reasoning=True,
        max_reasoning_attempts=3,  # ✅ ADD THIS
        tools=holding_analysis_tools,
    )

@agent
def rebalancing_strategist(self) -> Agent:
    """Agent that generates optimal rebalancing trade recommendations."""
    return Agent(
        config=self.agents_config["rebalancing_strategist"],
        verbose=True,
        tools=holding_analysis_tools,
        reasoning=True,
        max_reasoning_attempts=3,  # ✅ ADD THIS
    )

@agent
def risk_manager(self) -> Agent:
    """Agent that validates rebalancing recommendations against risk constraints."""
    return Agent(
        config=self.agents_config["risk_manager"],
        verbose=True,
        tools=holding_analysis_tools,
        reasoning=True,
        max_reasoning_attempts=3,  # ✅ ADD THIS
    )
```

### Step 2: Kill Current Execution

```bash
# Find and kill the stuck process
ps aux | grep finwiz
kill -9 <PID>

# Or use Ctrl+C if running in terminal
```

### Step 3: Verify Fix

```bash
# Run with the fix applied
make dev

# Monitor for reasoning attempts
# Should see: "Reasoning (Attempt 1/3)" instead of "Attempt 49"
```

## Prevention Strategy

### 1. Add to Code Standards

Update `.kiro/steering/crewai-standards.md`:

```markdown
### Agent Reasoning Configuration

**MANDATORY RULE:** When enabling reasoning, ALWAYS set max_reasoning_attempts:

```python
# ✅ CORRECT
Agent(
    reasoning=True,
    max_reasoning_attempts=3,  # REQUIRED
)

# ❌ WRONG - Will cause infinite loops
Agent(
    reasoning=True,  # Missing max_reasoning_attempts
)
```

**Recommended Limits:**
- Simple tasks: `max_reasoning_attempts=2`
- Standard tasks: `max_reasoning_attempts=3`
- Complex tasks: `max_reasoning_attempts=5`
- Never exceed: `max_reasoning_attempts=10`
```

### 2. Add Pre-commit Check

Create `.pre-commit-config.yaml` hook:

```yaml
- repo: local
  hooks:
    - id: check-reasoning-limits
      name: Check reasoning limits
      entry: python scripts/check_reasoning_limits.py
      language: python
      files: \.py$
```

Create `scripts/check_reasoning_limits.py`:

```python
#!/usr/bin/env python
"""Check that all agents with reasoning=True have max_reasoning_attempts."""
import re
import sys
from pathlib import Path

def check_file(filepath):
    """Check a single file for reasoning without limits."""
    content = Path(filepath).read_text()
    
    # Find all Agent() calls with reasoning=True
    pattern = r'Agent\([^)]*reasoning\s*=\s*True[^)]*\)'
    matches = re.finditer(pattern, content, re.DOTALL)
    
    errors = []
    for match in matches:
        agent_def = match.group(0)
        if 'max_reasoning_attempts' not in agent_def:
            line_num = content[:match.start()].count('\n') + 1
            errors.append(f"{filepath}:{line_num}: Agent has reasoning=True without max_reasoning_attempts")
    
    return errors

def main():
    """Check all Python files."""
    errors = []
    for filepath in sys.argv[1:]:
        if filepath.endswith('.py'):
            errors.extend(check_file(filepath))
    
    if errors:
        print("❌ Reasoning limit check failed:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("✅ All agents with reasoning have max_reasoning_attempts")
        sys.exit(0)

if __name__ == '__main__':
    main()
```

### 3. Add to Testing

Create `tests/unit/test_reasoning_limits.py`:

```python
"""Test that all agents with reasoning have max_reasoning_attempts."""
import ast
import pytest
from pathlib import Path

def find_agent_definitions():
    """Find all Agent() instantiations in crew files."""
    crew_dir = Path("src/finwiz/crews")
    agent_defs = []
    
    for py_file in crew_dir.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if hasattr(node.func, 'id') and node.func.id == 'Agent':
                        agent_defs.append((str(py_file), node.lineno))
        except:
            pass
    
    return agent_defs

def test_reasoning_agents_have_limits():
    """Verify all agents with reasoning=True have max_reasoning_attempts."""
    crew_dir = Path("src/finwiz/crews")
    violations = []
    
    for py_file in crew_dir.rglob("*.py"):
        content = py_file.read_text()
        
        # Simple regex check (not perfect but catches most cases)
        import re
        pattern = r'Agent\([^)]*reasoning\s*=\s*True[^)]*\)'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            agent_def = match.group(0)
            if 'max_reasoning_attempts' not in agent_def:
                line_num = content[:match.start()].count('\n') + 1
                violations.append(f"{py_file}:{line_num}")
    
    assert not violations, (
        f"Found {len(violations)} agents with reasoning=True but no max_reasoning_attempts:\n" +
        "\n".join(violations)
    )
```

## Performance Considerations

### When to Use Reasoning

According to your codebase standards (`.kiro/steering/crewai-standards.md`):

**Enable reasoning for:**
- ✅ Complex multi-step analysis requiring planning
- ✅ Error-prone operations needing recovery strategies
- ✅ Tasks using multiple tools with dependencies
- ✅ Single-execution deep analysis

**Disable reasoning for:**
- ❌ Simple validation (ticker format checks)
- ❌ Direct API calls (single-step fetches)
- ❌ Final reporters (consolidation only)
- ❌ High-volume executions (66+ runs)
- ❌ Time-sensitive operations

**Performance Cost:**
- 5-15 seconds per reasoning cycle
- 1-3 LLM calls per attempt
- 500-2000 tokens per cycle

### Optimization for Portfolio Rebalancing

Since portfolio rebalancing runs **once per portfolio** (not 66+ times), reasoning is appropriate. However, consider:

```python
# For high-volume portfolio analysis (66+ holdings)
reasoning=False  # Disable for speed

# For single portfolio rebalancing (1 execution)
reasoning=True
max_reasoning_attempts=3  # Enable with limit
```

## Monitoring & Alerts

### Add Logging

```python
import logging
logger = logging.getLogger(__name__)

@agent
def rebalancing_strategist(self) -> Agent:
    """Agent that generates optimal rebalancing trade recommendations."""
    logger.info("Initializing rebalancing_strategist with reasoning limit=3")
    return Agent(
        config=self.agents_config["rebalancing_strategist"],
        verbose=True,
        tools=holding_analysis_tools,
        reasoning=True,
        max_reasoning_attempts=3,
    )
```

### Add Timeout

```python
# In crew configuration
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        verbose=True,
        respect_context_window=True,
        allow_delegation=False,
        max_rpm=20,
        max_retries=10,
        timeout=3600,  # ✅ ADD 1-hour timeout
    )
```

## Summary

### Immediate Actions (Do Now):
1. ✅ Add `max_reasoning_attempts=3` to all 6 agents
2. ✅ Kill current stuck process
3. ✅ Restart with fix applied
4. ✅ Monitor for successful completion

### Short-term (This Week):
1. Add pre-commit hook for reasoning limits
2. Add unit test for reasoning configuration
3. Update code standards documentation

### Long-term (This Month):
1. Review all crews for reasoning configuration
2. Add performance monitoring for reasoning cycles
3. Implement timeout safeguards

## Expected Outcome

After applying the fix:
- ✅ Reasoning will stop after 3 attempts
- ✅ Agent will complete with best available answer
- ✅ No more infinite loops
- ✅ Execution time: 5-45 seconds (instead of infinite)

## References

- **CrewAI Standards:** `.kiro/steering/crewai-standards.md`
- **Performance Optimization:** Section on Agent Reasoning
- **Affected File:** `src/finwiz/crews/portfolio_rebalancing_crew/portfolio_rebalancing_crew.py`

---

**Priority:** 🔴 CRITICAL - Fix Immediately  
**Impact:** HIGH - Blocks portfolio rebalancing execution  
**Effort:** LOW - 5 minutes to fix  
**Risk:** NONE - Safe change with immediate benefit
