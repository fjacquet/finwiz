# Phase 2 Consolidation Plan

## Overview

After Phase 1 consolidation (60+ → ~30 files), we can further optimize by:

1. **Additional cleanup**: Merge/archive more redundant docs
2. **Move to steering**: Developer standards that should guide AI behavior

## 1. Additional Cleanup Opportunities

### A. Consolidate User Guides

**Create `docs/USER_GUIDE.md`** consolidating:

- `deployment_guide.md` - Deployment instructions
- `operational_runbook.md` - Operations guide
- `migration_guide.md` - Migration guide

**Result**: 3 files → 1 file

### B. Archive Redundant Files

**Move to `docs/archive/`**:

- `reference.md` - Superseded by `API_REFERENCE.md`
- `schema_enhancements_guide.md` - Merged into `API_REFERENCE.md`
- `CONSOLIDATION_QUICK_START.md` - Meta-doc, no longer needed
- `DOCUMENTATION_CONSOLIDATION_PLAN.md` - Meta-doc, no longer needed
- `finwiz_family_financial_plan.html` - Example output, not documentation
- `crewai-rag-tool.lock` - Lock file, not documentation

**Result**: 6 files archived

### C. Consolidate A+ Documentation

**Create `docs/APLUS_SYSTEM.md`** consolidating:

- `a_plus_monitoring_system.md` - A+ monitoring
- `a_plus_scoring_tool.md` - A+ scoring
- `portfolio_holdings_analysis_a_plus_strategy.md` - A+ strategy

**Result**: 3 files → 1 file

### D. Consolidate System Documentation

**Create `docs/SYSTEM_OPERATIONS.md`** consolidating:

- `feedback_learning_system.md` - Feedback system
- `portfolio_monitoring_system.md` - Portfolio monitoring
- `knowledge_base_maintenance.md` - KB maintenance
- `integration_system_configuration.md` - Integration config

**Result**: 4 files → 1 file

### E. Keep Focused Docs

These remain as single-purpose docs:

- `agent_handbook.md` - Agent guidelines (also in steering)
- `output_formatting_guide.md` - Output standards
- `validation_criteria.md` - Validation rules
- `perplexity_sonar_integration_spec.md` - Perplexity integration
- `quantitative_analysis.md` - Quantitative guide
- `portfolio_holdings_analysis_user_guide.md` - Portfolio analysis guide

## 2. Move to Steering

Steering files guide AI behavior during development. These docs should be in steering:

### A. Already in Steering ✅

- `tech.md` - Technical standards
- `quality.md` - Code quality
- `security.md` - Security standards
- `structure.md` - Code structure
- `product.md` - Product requirements
- `finance.md` - Financial analysis standards
- `finwiz-guide.md` - FinWiz development guide

### B. Should Move to Steering

**1. `agent_handbook.md` → `.kiro/steering/agents.md`**

- Agent code of conduct
- Research guidelines
- Tool usage guidelines
- Output quality standards

**Rationale**: Guides AI agent behavior during development

**2. `output_formatting_guide.md` → `.kiro/steering/output-standards.md`**

- HTML formatting standards
- Report structure
- French language requirements
- Emoji usage

**Rationale**: Guides AI when generating outputs

**3. `validation_criteria.md` → `.kiro/steering/validation.md`**

- Validation rules
- Schema requirements
- Data quality standards

**Rationale**: Guides AI when validating data

**4. Parts of `DEVELOPER_GUIDE.md` → `.kiro/steering/development.md`**

- CrewAI standards
- Testing standards
- Code quality standards
- Common patterns

**Rationale**: Guides AI during development

**Note**: Keep `DEVELOPER_GUIDE.md` for human developers, but extract AI-relevant parts to steering

### C. New Steering Files to Create

**`.kiro/steering/crewai-standards.md`**
Extract from `DEVELOPER_GUIDE.md`:

- CrewAI configuration patterns
- Agent/task/crew structure
- Tool assignment guidelines
- Output validation requirements

**`.kiro/steering/testing-standards.md`**
Extract from `DEVELOPER_GUIDE.md`:

- Test naming conventions
- Mocking strategy
- Test requirements
- Coverage expectations

## Expected Results

### File Count Reduction

| Category | Current | After Phase 2 | Reduction |
|----------|---------|---------------|-----------|
| User Guides | 3 | 1 | -67% |
| A+ Docs | 3 | 1 | -67% |
| System Docs | 4 | 1 | -75% |
| Archived | 6 | - | Moved |
| **Total Docs** | **~30** | **~20** | **-33%** |

### Steering Files

| Current | After Phase 2 | Addition |
|---------|---------------|----------|
| 7 files | 11 files | +4 files |

**New steering files**:

- `agents.md` (from agent_handbook.md)
- `output-standards.md` (from output_formatting_guide.md)
- `validation.md` (from validation_criteria.md)
- `crewai-standards.md` (extracted from DEVELOPER_GUIDE.md)
- `testing-standards.md` (extracted from DEVELOPER_GUIDE.md)

## Implementation Steps

### Step 1: Create Consolidated Docs (30 min)

```bash
# Create USER_GUIDE.md
# Create APLUS_SYSTEM.md
# Create SYSTEM_OPERATIONS.md
```

### Step 2: Archive Redundant Files (5 min)

```bash
mv docs/reference.md docs/archive/
mv docs/schema_enhancements_guide.md docs/archive/
mv docs/CONSOLIDATION_QUICK_START.md docs/archive/
mv docs/DOCUMENTATION_CONSOLIDATION_PLAN.md docs/archive/
mv docs/finwiz_family_financial_plan.html docs/archive/
mv docs/crewai-rag-tool.lock docs/archive/
```

### Step 3: Move to Steering (20 min)

```bash
# Copy and adapt for AI consumption
cp docs/agent_handbook.md .kiro/steering/agents.md
cp docs/output_formatting_guide.md .kiro/steering/output-standards.md
cp docs/validation_criteria.md .kiro/steering/validation.md

# Extract from DEVELOPER_GUIDE.md
# Create .kiro/steering/crewai-standards.md
# Create .kiro/steering/testing-standards.md
```

### Step 4: Update Navigation (10 min)

```bash
# Update docs/README.md
# Update main README.md
# Add steering file references
```

### Step 5: Clean Up (5 min)

```bash
# Remove original files that were moved to steering
rm docs/agent_handbook.md
rm docs/output_formatting_guide.md
rm docs/validation_criteria.md

# Remove consolidated files
rm docs/deployment_guide.md
rm docs/operational_runbook.md
rm docs/migration_guide.md
rm docs/a_plus_monitoring_system.md
rm docs/a_plus_scoring_tool.md
rm docs/portfolio_holdings_analysis_a_plus_strategy.md
rm docs/feedback_learning_system.md
rm docs/portfolio_monitoring_system.md
rm docs/knowledge_base_maintenance.md
rm docs/integration_system_configuration.md
```

## Benefits

### 1. Cleaner Documentation

- **~20 core docs** (down from ~30)
- Clear purpose for each doc
- Less redundancy

### 2. Better AI Guidance

- **11 steering files** (up from 7)
- AI has clear standards during development
- Consistent behavior across sessions

### 3. Separation of Concerns

- **Docs**: For human developers and users
- **Steering**: For AI behavior and standards

### 4. Easier Maintenance

- Standards in one place (steering)
- Less duplication between docs and steering
- Single source of truth for AI behavior

## Final Structure

### Documentation (`docs/`)

```
docs/
├── README.md (navigation hub)
├── DEVELOPER_GUIDE.md (human developers)
├── ARCHITECTURE.md (system design)
├── API_REFERENCE.md (API docs)
├── USER_GUIDE.md (operations & deployment) ⭐ NEW
├── APLUS_SYSTEM.md (A+ system) ⭐ NEW
├── SYSTEM_OPERATIONS.md (system ops) ⭐ NEW
├── quantitative_analysis.md
├── portfolio_holdings_analysis_user_guide.md
├── perplexity_sonar_integration_spec.md
├── investment_discovery/ (4 files)
├── portfolio_rebalancing/ (4 files)
├── schemas/ (reference)
├── change_requests/ (historical)
└── archive/ (30+ historical docs)

Total: ~20 core files
```

### Steering (`.kiro/steering/`)

```
.kiro/steering/
├── tech.md (technical standards)
├── quality.md (code quality)
├── security.md (security)
├── structure.md (code structure)
├── product.md (product requirements)
├── finance.md (financial analysis)
├── finwiz-guide.md (FinWiz guide)
├── agents.md (agent guidelines) ⭐ NEW
├── output-standards.md (output formatting) ⭐ NEW
├── validation.md (validation rules) ⭐ NEW
├── crewai-standards.md (CrewAI patterns) ⭐ NEW
└── testing-standards.md (testing patterns) ⭐ NEW

Total: 12 files
```

## Rationale: Why Move to Steering

### What Belongs in Steering

**Standards that guide AI behavior**:

- ✅ Code quality standards
- ✅ Testing patterns
- ✅ Security requirements
- ✅ Output formatting rules
- ✅ Agent behavior guidelines
- ✅ Validation requirements

### What Stays in Docs

**Information for humans**:

- ✅ Architecture explanations
- ✅ User guides
- ✅ API reference
- ✅ Feature documentation
- ✅ Troubleshooting guides

### The Key Difference

- **Steering**: "How to do things" (prescriptive)
- **Docs**: "What things are" (descriptive)

## Next Steps

1. **Review this plan** - Approve or adjust
2. **Execute Phase 2** - ~70 minutes total
3. **Test AI behavior** - Verify steering files work
4. **Update references** - Fix any broken links

---

**Status**: PROPOSED  
**Estimated Time**: 70 minutes  
**Expected Reduction**: 30 → 20 docs (33%)  
**Steering Addition**: 7 → 12 files (+5)
