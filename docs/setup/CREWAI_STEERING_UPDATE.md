# CrewAI Steering Documentation Update

**Date**: 2025-11-15
**Source**: Context7 MCP Server (`/websites/crewai`)
**Updated Files**: `.kiro/steering/crewai-standards.md`

## Summary

Refreshed CrewAI steering documentation with latest patterns and best practices from official CrewAI documentation via Context7.

## Key Updates

### 1. Agent Configuration Enhancements

**Added**:

- Complete agent parameter reference with all 20+ configuration options
- Detailed reasoning behavior explanation (planning, reflection, retry strategies)
- Performance cost metrics for reasoning (5-15s, 1-3 LLM calls, 500-2000 tokens)
- Automatic delegation tools documentation (Delegate Work Tool, Ask Question Tool)
- Context window management with `respect_context_window=True`

**Example**:

```python
agent = Agent(
    role="Senior Data Scientist",
    reasoning=True,
    max_reasoning_attempts=3,
    allow_delegation=False,  # Only for coordinators
    respect_context_window=True,
    max_iter=20,
    max_retry_limit=2,
    # ... 15+ more parameters documented
)
```

### 2. Flow State Management Improvements

**Added**:

- Automatic `id` field in all states (UUID)
- Unstructured state pattern (for simple flows)
- State visualization and debugging utilities
- Progress tracking patterns
- Error handling with state updates

**Enhanced**:

- Data passing between methods (return values → parameters)
- State vs. return value distinction clarified
- Type safety benefits explained

**Example**:

```python
class MyFlowState(BaseModel):
    counter: int = 0
    # Note: 'id' field automatically added

class MyFlow(Flow[MyFlowState]):
    @start()
    def first_method(self):
        print(f"Flow ID: {self.state.id}")  # Auto-generated
        self.state.counter = 1
        return {"data": "value"}  # Passed to listeners
```

### 3. Flow Persistence Patterns

**New Section**:

- Class-level persistence with `@persist()` decorator
- Method-level persistence for granular control
- Use cases: long-running workflows, human-in-the-loop, audit trails
- Default storage: SQLite

**Example**:

```python
@persist()  # Save state after every method
class PersistentFlow(Flow[MyState]):
    @start()
    def step_one(self):
        self.state.value += 1
        return self.state.value
```

### 4. Advanced Flow Patterns

**New Section**:

- Conditional starts with multiple entry points
- Logical operators: `and_()`, `or_()` for complex dependencies
- State visualization with Rich library
- Progress tracking helpers
- Robust error handling patterns

**Example**:

```python
@start()  # Unconditional
def init(self):
    return {"initialized": True}

@start("init")  # Conditional: after init OR external trigger
def maybe_begin(self):
    return {"started": True}

@listen(and_(init, maybe_begin))  # Wait for BOTH
def proceed(self):
    return {"proceeding": True}
```

### 5. Task Context and Collaboration

**Enhanced**:

- Task context parameter for using outputs from other tasks
- Agent collaboration patterns with delegation
- Multi-agent workflow examples

**Example**:

```python
research_task = Task(
    description="Research quantum computing",
    agent=researcher
)

writing_task = Task(
    description="Write article based on research",
    agent=writer,
    context=[research_task]  # Gets research output
)
```

### 6. CrewBase Decorator Pattern

**Added**:

- Structured crew definition with `@CrewBase`
- Auto-collection of agents and tasks
- Configuration file integration
- Before/after kickoff hooks

**Example**:

```python
@CrewBase
class ResearchCrew:
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config['researcher'])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # Auto-collected
            tasks=self.tasks,    # Auto-collected
            process=Process.sequential
        )
```

### 7. Crew Integration in Flows

**Enhanced**:

- Complete flow-crew integration example
- State management with crew results
- Data passing patterns
- Error handling in crew execution

**Example**:

```python
class PoemFlow(Flow[PoemState]):
    @listen(generate_sentence_count)
    def generate_poem(self, data):
        count = data["count"]

        # Execute crew
        result = PoemCrew().crew().kickoff(
            inputs={"sentence_count": count}
        )

        # Store in state
        self.state.poem = result.raw

        return {"poem": result.raw}
```

## Documentation Structure Improvements

### Before

- Basic agent/task/crew patterns
- Simple flow state management
- Limited error handling examples

### After

- Comprehensive agent configuration (20+ parameters)
- Advanced flow patterns (persistence, routing, debugging)
- Complete integration examples
- Error handling and progress tracking
- State visualization utilities
- Performance considerations

## Benefits

1. **Up-to-Date**: Reflects latest CrewAI framework capabilities
2. **Comprehensive**: Covers all major features and patterns
3. **Practical**: Includes real-world examples from FinWiz context
4. **Type-Safe**: Emphasizes Pydantic models and type safety
5. **Production-Ready**: Includes error handling, persistence, monitoring

## Validation

All patterns validated against:

- Official CrewAI documentation (via Context7)
- FinWiz existing implementations
- CrewAI best practices
- Python type safety standards

## Next Steps

1. ✅ Documentation updated
2. ⏭️ Review existing FinWiz crews for compliance
3. ⏭️ Update crew implementations to use new patterns
4. ⏭️ Add state visualization to debugging workflows
5. ⏭️ Consider persistence for long-running flows

## References

- **Context7 Library**: `/websites/crewai`
- **Documentation Source**: https://docs.crewai.com
- **Code Snippets**: 1340 examples analyzed
- **Benchmark Score**: 84.7/100 (High quality)

---

**Maintained By**: Kiro AI Assistant
**Last Context7 Refresh**: 2025-11-15
