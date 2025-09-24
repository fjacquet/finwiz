# Design Document

## Overview

This design document outlines a practical approach to ensure consistent utilization of FinWiz's existing features across all CrewAI crews. The solution focuses on auditing current crew implementations, identifying gaps in tool usage, and implementing systematic corrections to ensure all crews leverage available analytical capabilities properly.

The design emphasizes pragmatic improvements over complex new features, ensuring that existing tools like the Quantitative Analysis Tool, Enhanced SEC Analysis Tool, and schema validation systems are used consistently across Stock, ETF, Crypto, Portfolio Rebalancing, and Report crews.

## Architecture

### Current State Analysis

The current FinWiz architecture has well-implemented tools and frameworks, but analysis reveals inconsistent usage patterns:

- **Tool Availability**: All crews have access to comprehensive tool suites, but not all crews use all relevant tools
- **Schema Compliance**: Some crews generate proper JSON appendices while others may skip this step
- **Risk Assessment**: Risk scoring methodology exists but may not be consistently applied
- **Translation**: Some crews have translation tasks while others may be missing them

### Target Architecture

The enhanced architecture will maintain the existing structure while ensuring systematic feature utilization:

```
┌─────────────────────────────────────────────────────────────┐
│                    FinWiz Flow Orchestrator                 │
└─────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
        │  Stock Crew  │ │  ETF Crew   │ │ Crypto Crew│
        │              │ │             │ │            │
        │ ✓ Quant Tool │ │ ✓ Quant Tool│ │ ✓ Quant Tool│
        │ ✓ SEC Tool   │ │ ✓ ETF Tool  │ │ ✓ Crypto Tool│
        │ ✓ Risk Score │ │ ✓ Risk Score│ │ ✓ Risk Score│
        │ ✓ Schema Out │ │ ✓ Schema Out│ │ ✓ Schema Out│
        │ ✓ Translation│ │ ✓ Translation│ │ ✓ Translation│
        └──────────────┘ └─────────────┘ └────────────┘
                                │
                        ┌───────▼──────┐
                        │ Report Crew  │
                        │              │
                        │ ✓ Tool Restrict│
                        │ ✓ Schema Valid │
                        │ ✓ Translation  │
                        └────────────────┘
```

## Components and Interfaces

### 1. CrewAI Task Configuration Enhancement

**Purpose**: Use CrewAI's built-in task configuration features to enforce proper tool usage and output validation.

**CrewAI Features to Leverage**:
- `output_pydantic`: Use existing FinWiz Pydantic schemas for automatic output validation
- `output_json`: Enforce structured JSON outputs for machine-readable appendices
- `expected_output`: Clear output specifications in task YAML configurations
- Task dependencies via `depends_on` to ensure proper workflow sequencing

**Implementation Approach**:
- Update task YAML configurations to include `output_pydantic` specifications
- Leverage existing FinWiz schemas (TenKInsight, MarketSentiment, RiskAssessmentStandardized)
- Use CrewAI's built-in validation rather than custom validation logic

### 2. CrewAI Agent Tool Management

**Purpose**: Ensure agents have proper tool configurations using CrewAI's agent management features.

**CrewAI Features to Leverage**:
- Agent `tools` parameter for proper tool assignment
- Tool validation at agent initialization
- CrewAI's built-in tool error handling and retry mechanisms
- Agent role-based tool restrictions

**Implementation Approach**:
- Audit current agent tool assignments in crew Python files
- Ensure all agents have access to required tools for their roles
- Use CrewAI's tool management rather than custom tool validation

### 3. CrewAI Crew Process Optimization

**Purpose**: Use CrewAI's process management features for better workflow coordination.

**CrewAI Features to Leverage**:
- `Process.sequential` for proper task ordering
- `async_execution=True` for I/O-bound tasks
- CrewAI's built-in error handling and retry mechanisms
- Crew-level configuration options (`max_rpm`, `respect_context_window`)

**Implementation Approach**:
- Review current crew process configurations
- Ensure proper use of async execution for parallel tasks
- Leverage CrewAI's built-in performance optimization features

### 4. CrewAI Flow Integration

**Purpose**: Use CrewAI Flow features for better orchestration and state management.

**CrewAI Features to Leverage**:
- Flow state management for cross-crew data sharing
- `@listen` decorators for proper flow coordination
- Built-in flow error handling and recovery
- Flow-level monitoring and logging

**Implementation Approach**:
- Enhance existing FinwizFlow to better utilize CrewAI Flow features
- Use flow state for sharing validated data between crews
- Leverage CrewAI's built-in flow orchestration rather than custom logic

## CrewAI Configuration Patterns

### Task Configuration with Output Validation
```yaml
# Example task configuration using CrewAI features
stock_analysis_task:
  description: "Analyze stock with quantitative metrics"
  expected_output: "Structured analysis with risk assessment and technical indicators"
  output_pydantic: "StockAnalysisResult"  # Use existing FinWiz schema
  output_json: true
  agent: stock_analyst
  async_execution: true
  depends_on: 
    - ticker_validation_task
```

### Agent Configuration with Proper Tools
```python
@agent
def stock_analyst(self) -> Agent:
    return Agent(
        config=self.agents_config["stock_analyst"],
        tools=[
            quantitative_analysis_tool,  # Ensure this is included
            enhanced_sec_tool,           # Ensure this is included
            ticker_validation_tool,      # Ensure this is included
            *rag_tools                   # Ensure RAG tools are included
        ],
        verbose=True
    )
```

### Crew Configuration with CrewAI Features
```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        verbose=True,
        respect_context_window=True,  # Use CrewAI feature
        max_rpm=20,                   # Use CrewAI feature
        # Use existing FinWiz validation instead of custom logic
    )
```

## Error Handling

### CrewAI Built-in Error Handling

**Leverage CrewAI's Native Features**:
1. **Tool Failures**: Use CrewAI's built-in tool error handling and retry mechanisms
2. **Output Validation**: Use `output_pydantic` for automatic schema validation with CrewAI error reporting
3. **Task Dependencies**: Use CrewAI's `depends_on` for proper error propagation
4. **Crew-level Retries**: Use CrewAI's `max_retries` configuration for automatic retry handling

### Configuration Validation

**Use Existing FinWiz Patterns**:
- Leverage existing `ConfigurationManager` for API key validation
- Use existing `ToolRestrictionValidator` for tool compliance
- Integrate with existing `SessionManager` for state management
- Build upon existing validation patterns rather than creating new ones

## Testing Strategy

### CrewAI Testing Integration

**Use Existing FinWiz Testing Patterns**:
1. **Crew Configuration Tests**: Extend existing pytest-based tests to validate tool configurations
2. **Schema Compliance Tests**: Use existing Pydantic validation tests with CrewAI output validation
3. **Tool Integration Tests**: Leverage existing pytest-mock patterns for tool testing
4. **CrewAI Feature Tests**: Test CrewAI-specific features like `output_pydantic` and `async_execution`

### Practical Testing Approach

**Focus on Configuration Validation**:
- Test that agents have required tools in their tool lists
- Validate that tasks use appropriate CrewAI output features
- Ensure crew configurations use proper CrewAI process settings
- Test integration with existing FinWiz validation systems

**Avoid Over-Engineering**:
- Use existing test infrastructure rather than creating new test frameworks
- Focus on configuration correctness rather than complex validation logic
- Leverage CrewAI's built-in testing capabilities where available

## Implementation Approach

### Simple Configuration Updates

**Phase 1: Manual Audit (1-2 days)**
- Review current crew configurations manually
- Identify missing tools in agent configurations
- Check for missing CrewAI features in task configurations
- Document gaps in a simple spreadsheet or markdown file

**Phase 2: Configuration Fixes (2-3 days)**
- Update agent tool lists to include missing essential tools
- Add `output_pydantic` to tasks that should generate schema-compliant outputs
- Enable `async_execution=True` for appropriate I/O-bound tasks
- Ensure all crews have translation tasks where missing

**Phase 3: CrewAI Feature Enhancement (2-3 days)**
- Update task YAML files to use `expected_output` specifications
- Add proper `depends_on` relationships for task sequencing
- Configure crew-level settings like `max_rpm` and `respect_context_window`
- Integrate with existing FinWiz validation systems

**Phase 4: Testing and Validation (1-2 days)**
- Run existing test suite to ensure no regressions
- Test crew execution to verify proper tool usage
- Validate output formats match expected schemas
- Document any remaining gaps or limitations

## Monitoring and Maintenance

### Simple Monitoring Approach

**Use Existing FinWiz Logging**:
- Leverage existing logger infrastructure to track tool usage
- Monitor CrewAI execution logs for validation errors
- Use existing error handling patterns for failure detection
- Integrate with existing performance monitoring

### Practical Maintenance

**Manual Review Process**:
1. **Quarterly Configuration Review**: Manual review of crew configurations for drift
2. **Tool Usage Verification**: Periodic checks that crews are using assigned tools
3. **Output Quality Assessment**: Regular review of generated outputs for schema compliance
4. **Performance Impact Monitoring**: Track execution times to ensure no degradation

**Avoid Over-Engineering**:
- Use existing monitoring infrastructure rather than building new systems
- Focus on manual processes that can be easily maintained
- Leverage CrewAI's built-in logging and error reporting
- Keep monitoring simple and actionable