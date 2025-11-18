# Task Master 0.24.0 Quick Start Guide - FinWiz

**Status**: Ready for immediate use
**Agent Count**: 119 specialized agents (4 new FinWiz-specific agents added)
**Integration Level**: Enhanced with codebase-aware capabilities

---

## Immediate Usage - No Setup Required!

The Claude 007 Agents system with Task Master 0.24.0 is already configured and ready to use. Simply invoke agents using the @ mention pattern in your conversations.

---

## FinWiz-Specific Domain Agents (NEW)

### 1. @crewai-finwiz-architect

**Purpose**: CrewAI architecture compliance and pattern enforcement

**Use When**:

- Creating or modifying CrewAI crews
- Working with Flow orchestration
- Validating Pydantic schemas
- Reviewing tool factory usage
- Checking AI Minimalism compliance

**Example**:

```
"@crewai-finwiz-architect: Review the new portfolio analysis crew
and ensure it follows FinWiz architectural patterns"
```

### 2. @quantitative-finance-engineer

**Purpose**: Quantitative finance calculations and validation

**Use When**:

- Implementing Backtrader strategies
- Using TA-Lib indicators
- Pricing derivatives with QuantLib
- Portfolio optimization with PyPortfolioOpt
- Validating numerical stability

**Example**:

```
"@quantitative-finance-engineer: Validate the Sharpe ratio calculation
and ensure it handles edge cases properly"
```

### 3. @pytest-test-architect

**Purpose**: Test design, pytest-mock patterns, test suite stabilization

**Use When**:

- Writing or fixing tests
- Stabilizing test suite
- Removing unittest.mock violations
- Creating test fixtures
- Improving test coverage

**Example**:

```
"@pytest-test-architect: Fix the failing tests in quantitative/test_config.py
and ensure we use pytest-mock, not unittest.mock"
```

### 4. @ai-minimalism-validator

**Purpose**: Cost/performance optimization through Python vs AI decisions

**Use When**:

- Reviewing AI usage in crews
- Identifying deterministic tasks using AI
- Calculating cost/benefit of AI vs Python
- Suggesting Python alternatives
- Optimizing platform costs

**Example**:

```
"@ai-minimalism-validator: Review the HTML report generation process
and identify opportunities to replace AI with Python templates"
```

---

## Task Master Bridge Agents (Pre-Configured)

### @task-orchestrator

**Purpose**: High-level task planning and workflow orchestration

**Use When**:

- Starting a complex multi-step task
- Need systematic approach to problem
- Coordinating multiple agents
- Planning test suite stabilization
- Managing code modernization workflow

**Example**:

```
"@task-orchestrator: Create a plan to fix the 557 test failures
in the FinWiz test suite and coordinate the stabilization effort"
```

### @task-executor

**Purpose**: Actual implementation and completion of tasks

**Use When**:

- Implementing specific features
- Executing planned work
- Writing code with codebase awareness
- Following architectural patterns
- Ensuring quality during execution

**Example**:

```
"@task-executor: Split the quantitative/optimization.py file (689 lines)
following the code modernization workflow and FinWiz patterns"
```

### @task-checker

**Purpose**: Quality validation and continuous feedback

**Use When**:

- Validating completed work
- Checking test coverage
- Verifying architectural compliance
- Ensuring quality gates pass
- Pre-commit validation

**Example**:

```
"@task-checker: Validate that the recent refactoring maintains
test coverage >65% and doesn't introduce regressions"
```

---

## Common Workflows

### Workflow 1: Test Suite Stabilization (URGENT - Current Need)

**Problem**: 557 test failures blocking all refactoring work

**Solution**:

```
User: "We need to fix the test suite - 557 failures are blocking work"

System automatically invokes:
├── @task-orchestrator: Analyze failure patterns, create systematic plan
├── @pytest-test-architect: Identify root causes, design fixes
├── @task-executor: Implement fixes systematically
└── @task-checker: Validate no regressions, track progress

Workflow:
1. @task-orchestrator analyzes TEST_STATUS_REPORT.md
2. @pytest-test-architect identifies patterns in failures
3. @task-executor fixes quantitative/ tests (141 failures)
4. @task-checker validates all tests still pass
5. Repeat for flow/, crews/, utils/, etc.
6. @task-checker confirms >95% pass rate achieved
```

### Workflow 2: Code Refactoring with Safety

**Problem**: Need to split large file without breaking tests

**Solution**:

```
User: "Split quantitative/optimization.py (689 lines) into smaller modules"

System automatically invokes:
├── @task-orchestrator: Plan decomposition strategy
├── @crewai-finwiz-architect: Validate architectural compliance
├── @quantitative-finance-engineer: Review calculation logic
├── @task-executor: Execute split with re-export layer
├── @pytest-test-architect: Update test imports
└── @task-checker: Validate all tests pass 3x

Workflow:
1. @task-orchestrator checks test suite health (must be >95%)
2. @crewai-finwiz-architect reviews file structure
3. @quantitative-finance-engineer validates no calculation changes
4. @task-executor creates new modules, updates imports
5. @pytest-test-architect fixes test imports and mocks
6. @task-checker runs full suite 3x, confirms no regressions
```

### Workflow 3: AI Cost Optimization

**Problem**: High AI costs from deterministic tasks

**Solution**:

```
User: "Review AI usage in report generation and optimize costs"

System automatically invokes:
├── @task-orchestrator: Identify all AI usage points
├── @ai-minimalism-validator: Analyze each usage, calculate savings
├── @crewai-finwiz-architect: Ensure alternatives follow patterns
├── @task-executor: Implement Python alternatives
└── @task-checker: Validate output quality matches AI

Workflow:
1. @task-orchestrator scans for AI task usage
2. @ai-minimalism-validator categorizes (valid AI vs should-be-Python)
3. @ai-minimalism-validator calculates cost/benefit for each
4. @crewai-finwiz-architect validates Jinja2 template approach
5. @task-executor replaces AI with Python templates
6. @task-checker validates output quality and performance
```

### Workflow 4: New Crew Creation

**Problem**: Need to create a new analysis crew following best practices

**Solution**:

```
User: "Create a new sentiment analysis crew for crypto assets"

System automatically invokes:
├── @task-orchestrator: Plan crew structure
├── @crewai-finwiz-architect: Define architectural requirements
├── @task-executor: Implement crew with tool factories
├── @pytest-test-architect: Create test suite
└── @task-checker: Validate compliance

Workflow:
1. @task-orchestrator outlines crew requirements
2. @crewai-finwiz-architect provides template and patterns
3. @task-executor creates:
   - crews/crypto_sentiment_crew/crypto_sentiment_crew.py
   - config/agents.yaml and tasks.yaml
   - Tool factory integration
   - Pydantic export schema
4. @pytest-test-architect creates test suite
5. @task-checker validates:
   - No self.inputs usage (use self.state)
   - Final reporter has empty tools
   - Tool factories used (not hardcoded)
   - Pydantic schema in schemas/
   - Tests use pytest-mock
```

---

## Agent Invocation Patterns

### Direct Invocation

```
"@agent-name: specific task description"
```

**Example**:

```
"@pytest-test-architect: Fix the failing tests in test_config.py"
```

### Workflow Invocation

```
"@task-orchestrator: [complex multi-step goal]"
```

**Example**:

```
"@task-orchestrator: Stabilize the test suite to >95% pass rate"
```

### Validation Request

```
"@task-checker: validate [aspect] of [component]"
```

**Example**:

```
"@task-checker: validate test coverage after refactoring"
```

---

## Quality Gates (Automatic with @task-checker)

### Pre-Commit Quality Gates

- Code quality: ruff lint + format
- Type checking: mypy passes
- No unittest.mock imports
- Test suite >95% pass rate
- No new test failures
- File size <300 lines (warn >250)

### Pre-PR Quality Gates

- All tests pass (3x runs)
- Coverage maintained/improved
- Documentation updated
- Commit attribution complete
- Architectural compliance verified

---

## Key FinWiz Constraints

These are automatically enforced by domain agents:

### CrewAI Patterns (@crewai-finwiz-architect)

- Use `Flow[PydanticModel]` for type safety
- Access state via `self.state.field_name` (NOT self.inputs)
- Final reporters MUST have empty tools
- Use tool factories (not hardcoded tool lists)
- All outputs validated with Pydantic schemas

### Testing Standards (@pytest-test-architect)

- Use pytest-mock (mocker fixture) ONLY
- Generate test data with Faker
- Mock all external dependencies
- Coverage target: >65%, critical modules >80%
- Test config, not crew execution

### AI Minimalism (@ai-minimalism-validator)

- Use AI ONLY for reasoning, synthesis, insights
- Use Python for calculations, templates, validation
- Cost/benefit analysis for each AI usage
- Target: <30% of tasks should be AI

### Quantitative Standards (@quantitative-finance-engineer)

- Use float64 for all financial calculations
- Handle NaN values explicitly
- Validate input data before calculations
- Document formulas and assumptions
- Ensure numerical stability

---

## Measuring Success

### Test Suite Health

- **Current**: 82.4% pass rate (2,608/3,165)
- **Target**: >95% pass rate (<50 failures)
- **Tracking**: TEST_STATUS_REPORT.md

### Code Quality

- **Current**: 17 files >600 lines
- **Target**: 0 files >300 lines
- **Tracking**: CLAUDE_007_TASKMASTER_SETUP.md

### AI Cost Optimization

- **Current**: Baseline being established
- **Target**: <30% of tasks using AI
- **Tracking**: AI Minimalism score calculation

---

## Getting Help

### Consult Specific Agent

```
"@agent-name: I need help with [specific issue]"
```

### Ask for Agent Recommendation

```
"Which agent should I use for [task description]?"
```

### Request Workflow Guidance

```
"@task-orchestrator: What's the best approach for [complex goal]?"
```

---

## Next Immediate Actions

### URGENT: Test Suite Stabilization (Week 1-2)

```
"@task-orchestrator: Initiate test suite stabilization workflow.
We have 557 test failures blocking all refactoring work. Priority order:
1. quantitative/ (141 failures)
2. flow/ + flows/ (36 failures)
3. crews/ (48 failures)
4. Others (82 failures)

Target: >95% pass rate within 2 weeks"
```

### After Test Stabilization: Code Modernization

```
"@task-orchestrator: Resume code modernization workflow.
Split 17 files >600 lines following FinWiz patterns.
Ensure test suite stays >95% throughout process."
```

### Continuous: AI Cost Optimization

```
"@ai-minimalism-validator: Scan codebase for AI usage
and identify top 10 cost-saving opportunities by replacing
deterministic AI tasks with Python alternatives"
```

---

## Resources

### Documentation

- **Complete Setup**: CLAUDE_007_TASKMASTER_SETUP.md (comprehensive analysis)
- **Architecture**: CLAUDE.md (FinWiz standards and patterns)
- **Test Status**: TEST_STATUS_REPORT.md (current test health)
- **Modernization**: .kiro/specs/finwiz-codebase-modernization/tasks.md

### Agent Definitions

- **Location**: .claude/agents/
- **Count**: 119 specialized agents
- **Categories**: 16 domains (orchestration, business, testing, etc.)

### Steering Documents

- **Location**: .kiro/steering/
- **Key Files**:
  - crewai-standards.md - CrewAI patterns
  - ai-minimalism.md - Cost optimization
  - testing-standards.md - Test patterns
  - backtrader-standards.md - Quant libraries
  - python-abc-strategy-pattern.md - Refactoring patterns

---

## FAQ

**Q: Do I need to configure anything?**
A: No, the system is ready to use immediately. Just use @ mentions.

**Q: How do I know which agent to use?**
A: Ask "@task-orchestrator: Which agent should handle [task]?" or consult this guide.

**Q: What if I make a mistake?**
A: @task-checker will validate your work and provide feedback before committing.

**Q: Can I use multiple agents together?**
A: Yes! @task-orchestrator will automatically coordinate multiple agents for complex tasks.

**Q: How do I track progress?**
A: Check the markdown reports (TEST_STATUS_REPORT.md, etc.) and ask @task-checker for updates.

**Q: What's the most urgent task right now?**
A: Test suite stabilization - 557 failures are blocking all refactoring work. Start with:

```
"@task-orchestrator: Initiate test suite stabilization workflow"
```

---

**Status**: Ready for Production Use
**Last Updated**: 2025-01-18
**Agent System Version**: Claude 007 + Task Master 0.24.0
**FinWiz Version**: Active development (enhance-readability branch)

**Get Started Now**:

```
"@task-orchestrator: Show me the top 3 priority tasks for FinWiz
based on the current state and guide me through the best approach"
```
