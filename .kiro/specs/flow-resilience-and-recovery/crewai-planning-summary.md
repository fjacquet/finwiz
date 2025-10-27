# CrewAI Crew Planning Summary

> Key patterns from CrewAI documentation for implementing crew-level planning

## Overview

Crew planning adds a planning phase before each crew iteration. An `AgentPlanner` analyzes all crew information and creates a step-by-step plan that is injected into each task description.

**Key Difference from Agent Reasoning:**
- **Agent Reasoning** (`reasoning=True` on Agent) - Individual agent plans its own task
- **Crew Planning** (`planning=True` on Crew) - Central planner creates plan for ALL tasks

## Basic Usage

```python
from crewai import Crew, Agent, Task, Process

my_crew = Crew(
    agents=self.agents,
    tasks=self.tasks,
    process=Process.sequential,
    planning=True,  # Enable crew-level planning
)
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `planning` | bool | False | Enable/disable crew planning |
| `planning_llm` | str | "gpt-5-mini" | LLM to use for planning |

### Custom Planning LLM

```python
my_crew = Crew(
    agents=self.agents,
    tasks=self.tasks,
    process=Process.sequential,
    planning=True,
    planning_llm="gpt-4o"  # Use more powerful model for planning
)
```

## How It Works

```
Crew.kickoff()
    ↓
[Planning Phase]
    ↓
AgentPlanner analyzes:
  - All agents (roles, goals, tools)
  - All tasks (descriptions, expected outputs)
  - Process type (sequential/hierarchical)
    ↓
Creates step-by-step plan for EACH task
    ↓
Injects plan into task descriptions
    ↓
[Execution Phase]
    ↓
Agents execute tasks with plans
```

## Example Planning Output

```markdown
**Step-by-Step Plan for Task Execution**

**Task Number 1: Conduct thorough research about AI LLMs**
**Agent:** AI LLMs Senior Data Researcher
**Agent Goal:** Uncover cutting-edge developments in AI LLMs
**Task Expected Output:** A list with 10 bullet points

**Step-by-Step Plan:**

1. **Define Research Scope:**
   - Determine specific areas to focus on

2. **Identify Reliable Sources:**
   - List reputable sources (journals, conferences, labs)

3. **Collect Data:**
   - Search for latest papers and reports
   - Use targeted keywords

4. **Analyze Findings:**
   - Read and summarize key points
   - Highlight new techniques and models

5. **Organize Information:**
   - Categorize into relevant topics
   - Ensure concise but informative points

6. **Create the List:**
   - Compile 10 most relevant pieces
   - Review for clarity and relevance

**Expected Output:**
A list with 10 bullet points of the most relevant information.
```

## Important Considerations

### ⚠️ OpenAI API Key Required

**Default behavior:**
- Planning uses `gpt-5-mini` by default
- Requires valid OpenAI API key
- Even if your agents use different LLMs!

**Potential issues:**
- Missing OpenAI key → Planning fails
- Unexpected API calls to OpenAI
- Cost implications (additional LLM calls)

### 💰 Cost Implications

**Per crew execution:**
- 1 planning call per crew iteration
- Tokens: ~1000-3000 per plan (depends on crew complexity)
- Model: gpt-5-mini (default) or custom

**For FinWiz deep analysis:**
- 66 holdings × 1 crew each = 66 planning calls
- Estimated: 66,000-200,000 tokens
- Cost: ~$0.01-0.03 per execution (gpt-5-mini)

## Agent Reasoning vs Crew Planning

| Feature | Agent Reasoning | Crew Planning |
|---------|----------------|---------------|
| **Scope** | Single agent, single task | All agents, all tasks |
| **When** | Before task execution | Before crew iteration |
| **Who plans** | The agent itself | Central AgentPlanner |
| **Configuration** | `Agent(reasoning=True)` | `Crew(planning=True)` |
| **LLM** | Agent's LLM | Separate planning LLM |
| **Overhead** | Per task | Per crew execution |
| **Use case** | Complex individual tasks | Coordinated multi-task workflows |

## When to Use in FinWiz

### ✅ Use Crew Planning For:
- **Multi-agent coordination** - Tasks depend on each other
- **Complex workflows** - Multiple tasks with dependencies
- **First-time execution** - No historical success patterns
- **Experimental crews** - Testing new crew configurations

### ❌ Don't Use Crew Planning For:
- **Single-agent crews** - Use agent reasoning instead
- **Well-established workflows** - Proven task sequences
- **High-volume operations** - 66 holdings = 66 planning calls
- **Cost-sensitive scenarios** - Additional API costs
- **Time-sensitive operations** - Planning adds overhead

## Recommendation for FinWiz Deep Analysis

### ❌ NOT RECOMMENDED for DeepAnalysisCrew

**Reasons:**
1. **Single-agent crew** - Only one agent per execution
2. **Well-defined workflow** - Tasks are sequential and proven
3. **High volume** - 66 holdings × planning overhead
4. **Cost** - Unnecessary API calls
5. **Agent reasoning sufficient** - Individual task planning is enough

### ✅ RECOMMENDED Approach

```python
# Use agent reasoning, NOT crew planning
class DeepAnalysisCrew(CrewBase):
    @agent
    def asset_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["asset_analyst"],
            tools=self.get_tools_for_asset_class(asset_class),
            reasoning=True,  # ✅ Agent-level reasoning
            max_reasoning_attempts=3
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            planning=False,  # ❌ No crew-level planning
            max_rpm=20
        )
```

## Alternative Use Cases in FinWiz

### ✅ Could Use for Portfolio Rebalancing Crew

```python
# Multi-agent crew with complex coordination
class PortfolioRebalancingCrew(CrewBase):
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.portfolio_analyzer(),
                self.risk_assessor(),
                self.trade_optimizer(),
                self.cost_calculator()
            ],
            tasks=self.tasks,
            process=Process.sequential,
            planning=True,  # ✅ Helps coordinate multiple agents
            planning_llm="gpt-4o"  # More powerful for complex planning
        )
```

### ✅ Could Use for Investment Discovery Crew

```python
# Multi-agent crew screening multiple assets
class InvestmentDiscoveryCrew(CrewBase):
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.market_screener(),
                self.fundamental_analyst(),
                self.technical_analyst(),
                self.opportunity_ranker()
            ],
            tasks=self.tasks,
            process=Process.sequential,
            planning=True,  # ✅ Coordinates screening workflow
            planning_llm="gpt-5-mini"
        )
```

## Performance Considerations

### Planning Overhead
- **Time**: Adds 10-30 seconds per crew execution
- **API Calls**: 1 additional LLM call per execution
- **Tokens**: ~1000-3000 tokens per plan
- **Cost**: $0.0001-0.0003 per plan (gpt-5-mini)

### Optimization Strategies

```python
# Strategy 1: Conditional planning based on complexity
if crew_complexity == "high":
    planning = True
else:
    planning = False

# Strategy 2: Planning for first execution only
if is_first_execution:
    planning = True
else:
    planning = False  # Use cached patterns

# Strategy 3: Planning for experimental crews
if crew_version == "experimental":
    planning = True
else:
    planning = False  # Proven workflow
```

## Monitoring Planning

```python
import logging

logging.basicConfig(level=logging.INFO)

# Planning output is logged automatically
crew = Crew(
    agents=agents,
    tasks=tasks,
    planning=True,
    planning_llm="gpt-5-mini"
)

# Look for log entries like:
# [INFO]: Planning the crew execution
# **Step-by-Step Plan for Task Execution**
# ...

result = crew.kickoff()
```

## Implementation Checklist for FinWiz

- [ ] **Evaluate crew complexity** - Multi-agent or single-agent?
- [ ] **Assess coordination needs** - Do tasks depend on each other?
- [ ] **Consider volume** - How many crew executions?
- [ ] **Calculate cost** - Planning overhead × execution count
- [ ] **Test with planning** - Compare with/without planning
- [ ] **Monitor performance** - Time and cost impact
- [ ] **Document decision** - Why planning is enabled/disabled
- [ ] **Configure planning LLM** - Choose appropriate model
- [ ] **Set up OpenAI key** - Required for default planning
- [ ] **Review planning output** - Ensure plans are useful

## Decision Matrix for FinWiz

| Crew | Agents | Tasks | Coordination | Volume | Planning? | Reason |
|------|--------|-------|--------------|--------|-----------|--------|
| DeepAnalysisCrew | 3 | 4 | Low | High (66×) | ❌ No | Use agent reasoning |
| PortfolioRebalancingCrew | 4+ | 6+ | High | Low (1×) | ✅ Yes | Complex coordination |
| InvestmentDiscoveryCrew | 4+ | 5+ | High | Low (3×) | ✅ Yes | Multi-agent screening |
| ReportCrew | 1 | 1 | None | Low (1×) | ❌ No | Single consolidation task |

## Key Takeaways

1. **Crew planning ≠ Agent reasoning** - Different scopes and purposes
2. **OpenAI key required** - Default planning uses gpt-5-mini
3. **Cost implications** - Additional API calls per execution
4. **Use selectively** - Best for multi-agent coordination
5. **Not for high-volume** - Overhead multiplies with executions
6. **Agent reasoning preferred** - For single-agent crews
7. **Monitor and measure** - Test impact before production use

## References

- CrewAI Crew Planning Documentation (provided)
- FinWiz existing crews: `deep_analysis.py`, `portfolio_rebalancing_crew/`
- Cost analysis: OpenAI pricing for gpt-5-mini

---

**Version**: 1.0  
**Created**: 2025-01-11  
**Purpose**: Guide decision-making on crew planning vs agent reasoning for FinWiz
