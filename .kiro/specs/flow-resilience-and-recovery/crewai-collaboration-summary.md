# CrewAI Agent Collaboration Summary

> Key patterns from CrewAI documentation for agent collaboration and delegation

## Overview

Collaboration enables agents to work together by delegating tasks and asking questions. When `allow_delegation=True`, agents automatically get collaboration tools.

**Key Concept:** Agents can leverage each other's expertise without manual coordination.

## Basic Usage

```python
from crewai import Agent

agent = Agent(
    role="Research Specialist",
    goal="Conduct thorough research",
    backstory="Expert researcher",
    allow_delegation=True,  # 🔑 Enables collaboration
    verbose=True
)
```

## Automatic Collaboration Tools

When `allow_delegation=True`, agents automatically get:

### 1. Delegate Work Tool

```python
# Automatically available:
# delegate_work(task: str, context: str, coworker: str)
```

### 2. Ask Question Tool

```python
# Automatically available:
# ask_question(question: str, context: str, coworker: str)
```

## Collaboration Patterns

### Pattern 1: Sequential Collaboration

```python
research_task = Task(
    description="Research quantum computing developments",
    agent=researcher
)

writing_task = Task(
    description="Write article based on research",
    agent=writer,
    context=[research_task]  # Gets research output
)

editing_task = Task(
    description="Edit and polish the article",
    agent=editor,
    context=[writing_task]  # Gets article draft
)
```

### Pattern 2: Collaborative Single Task

```python
collaborative_task = Task(
    description="""Create marketing strategy.

    Writer: Focus on messaging
    Researcher: Provide market analysis

    Work together to create comprehensive strategy.""",
    agent=writer  # Lead agent, can delegate to researcher
)
```

### Pattern 3: Hierarchical Collaboration

```python
from crewai import Process

manager = Agent(
    role="Project Manager",
    allow_delegation=True,  # Coordinates team
    verbose=True
)

specialist1 = Agent(
    role="Researcher",
    allow_delegation=False,  # Focuses on expertise
    verbose=True
)

specialist2 = Agent(
    role="Writer",
    allow_delegation=False,  # Focuses on expertise
    verbose=True
)

crew = Crew(
    agents=[manager, specialist1, specialist2],
    tasks=[project_task],
    process=Process.hierarchical,  # Manager coordinates
    manager_llm="gpt-4o"
)
```

## Best Practices

### 1. Clear Role Definition

```python
# ✅ GOOD - Specific, complementary roles
researcher = Agent(role="Market Research Analyst", ...)
writer = Agent(role="Technical Content Writer", ...)

# ❌ BAD - Overlapping or vague roles
agent1 = Agent(role="General Assistant", ...)
agent2 = Agent(role="Helper", ...)
```

### 2. Strategic Delegation Enabling

```python
# ✅ Enable for coordinators
lead_agent = Agent(
    role="Content Lead",
    allow_delegation=True,  # Can delegate
)

# ✅ Disable for focused specialists
specialist = Agent(
    role="Data Analyst",
    allow_delegation=False,  # Focuses on core work
)
```

### 3. Context Sharing

```python
# ✅ Use context parameter for dependencies
writing_task = Task(
    description="Write article",
    agent=writer,
    context=[research_task],  # Shares results
)
```

### 4. Clear Task Descriptions

```python
# ✅ GOOD - Specific, actionable
Task(
    description="""Research competitors in AI chatbot space.
    Focus on: pricing, features, target markets.
    Provide structured data."""
)

# ❌ BAD - Vague
Task(description="Do some research about chatbots")
```

## Troubleshooting

### Issue: Agents Not Collaborating

```python
# ✅ Solution: Enable delegation
agent = Agent(
    role="...",
    allow_delegation=True,  # Required!
)
```

### Issue: Too Much Back-and-Forth

```python
# ✅ Solution: Better context and specific roles
Task(
    description="""Write technical blog post.

    Context: Target audience is developers.
    Length: 1200 words
    Include: code examples, best practices

    Delegate research to researcher if needed."""
)
```

### Issue: Delegation Loops

```python
# ✅ Solution: Clear hierarchy
manager = Agent(role="Manager", allow_delegation=True)
specialist1 = Agent(role="Specialist A", allow_delegation=False)  # No re-delegation
specialist2 = Agent(role="Specialist B", allow_delegation=False)
```

## Advanced Features

### Custom Collaboration Rules

```python
agent = Agent(
    role="Senior Developer",
    backstory="""You lead development projects.

    Collaboration guidelines:
    - Delegate research to Research Analyst
    - Ask Designer for UI/UX guidance
    - Consult QA Engineer for testing
    - Escalate blocking issues to PM""",
    allow_delegation=True
)
```

### Monitoring Collaboration

```python
def track_collaboration(output):
    if "Delegate work to coworker" in output.raw:
        print("🤝 Delegation occurred")
    if "Ask question to coworker" in output.raw:
        print("❓ Question asked")

crew = Crew(
    agents=[...],
    tasks=[...],
    step_callback=track_collaboration,
    verbose=True
)
```

### Memory and Learning

```python
agent = Agent(
    role="Content Lead",
    memory=True,  # Remembers past interactions
    allow_delegation=True
)
```

## Relevance to FinWiz

### DeepAnalysisCrew (3 agents)

**Current Structure:**

- asset_analyst (research + analysis)
- risk_assessor (risk evaluation)
- investment_reporter (consolidation)

**Collaboration Decision:**

```python
# ✅ RECOMMENDED: Enable selective delegation
asset_analyst = Agent(
    role="Asset Analyst",
    allow_delegation=True,  # Can ask risk_assessor questions
    reasoning=True
)

risk_assessor = Agent(
    role="Risk Assessor",
    allow_delegation=False,  # Focused specialist
    reasoning=True
)

investment_reporter = Agent(
    role="Investment Reporter",
    allow_delegation=False,  # Consolidates only
    tools=[]  # No tools, no delegation needed
)
```

**Rationale:**

- asset_analyst might need risk clarification
- risk_assessor focuses on risk metrics
- investment_reporter just consolidates (no delegation needed)

### Alternative: No Delegation

```python
# ❌ ALTERNATIVE: Disable all delegation
# Simpler, faster, but less flexible

asset_analyst = Agent(
    role="Asset Analyst",
    allow_delegation=False,  # Independent work
    reasoning=True
)

risk_assessor = Agent(
    role="Risk Assessor",
    allow_delegation=False,
    reasoning=True
)

investment_reporter = Agent(
    role="Investment Reporter",
    allow_delegation=False,
    tools=[]
)
```

**Rationale:**

- Tasks are well-defined and sequential
- Context passing via task dependencies is sufficient
- Reduces complexity and API calls
- Faster execution (no delegation overhead)

## Performance Considerations

### Collaboration Overhead

- **Time**: 5-15 seconds per delegation/question
- **API Calls**: 1-2 additional LLM calls per collaboration
- **Tokens**: ~200-500 tokens per interaction
- **Cost**: \$0.0001-0.0003 per interaction (gpt-4o-mini)

### For FinWiz Deep Analysis (66 holdings)

- If 10% of analyses involve delegation: 6-7 collaborations
- Additional time: 30-105 seconds
- Additional cost: \$0.0006-0.0021
- **Impact: Minimal** for occasional use

## Recommendation for FinWiz

### DeepAnalysisCrew: Selective Delegation

```python
# ✅ RECOMMENDED APPROACH
class DeepAnalysisCrew(CrewBase):
    @agent
    def asset_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["asset_analyst"],
            tools=self.get_tools_for_asset_class(asset_class),
            reasoning=True,  # Plan complex analysis
            allow_delegation=True,  # Can ask risk_assessor
            verbose=True
        )

    @agent
    def risk_assessor(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_assessor"],
            tools=self.get_tools_for_asset_class(asset_class),
            reasoning=True,  # Plan risk assessment
            allow_delegation=False,  # Focused specialist
            verbose=True
        )

    @final_reporter
    @agent
    def investment_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_reporter"],
            tools=[],  # No tools
            allow_delegation=False,  # Just consolidates
            verbose=True
        )
```

**Benefits:**

- asset_analyst can clarify risk questions
- Maintains focus for specialists
- Minimal overhead (rare delegation)
- Flexibility for edge cases

**Alternative (Simpler):**

- Set `allow_delegation=False` for all agents
- Rely on task context passing
- Faster, simpler, but less flexible

## Implementation Checklist

- [ ] Decide delegation strategy per crew
- [ ] Enable delegation for coordinators/leads
- [ ] Disable delegation for focused specialists
- [ ] Test collaboration patterns
- [ ] Monitor delegation frequency
- [ ] Measure performance impact
- [ ] Document collaboration guidelines in backstories
- [ ] Set up collaboration monitoring
- [ ] Consider memory for learning
- [ ] Review collaboration logs

## Key Takeaways

1. **Delegation is optional** - Not required for all agents
2. **Strategic enabling** - Coordinators yes, specialists maybe not
3. **Minimal overhead** - 5-15 seconds per collaboration
4. **Context passing works** - Task dependencies often sufficient
5. **Hierarchical for complex** - Manager pattern for coordination
6. **Clear roles matter** - Specific roles reduce confusion
7. **Monitor and measure** - Track collaboration patterns

## References

- CrewAI Agent Collaboration Documentation (provided)
- FinWiz DeepAnalysisCrew: `src/finwiz/crews/deep_analysis/deep_analysis.py`
- Task context patterns: `config/tasks.yaml`

---

**Version**: 1.0
**Created**: 2025-01-11
**Purpose**: Guide collaboration decisions for FinWiz crews
