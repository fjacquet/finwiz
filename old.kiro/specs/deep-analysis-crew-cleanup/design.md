# Design Document: Deep Analysis Crew Cleanup

## Overview

This design addresses the production bug where `DeepAnalysisCrew` fails with `KeyError: 'risk_assessor'`. The issue stems from incomplete cleanup during the Python/AI Hybrid refactoring, where the `risk_assessor` agent was deprecated but not fully removed from the codebase.

## Architecture

### Current State (Broken)

```
DeepAnalysisCrew
├── asset_analyst() ✅ - Defined in agents.yaml
├── investment_reporter() ✅ - Defined in agents.yaml  
└── risk_assessor() ❌ - Method exists but config missing
```

**Problem**: The `risk_assessor()` method tries to access `self.agents_config["risk_assessor"]` which doesn't exist in `agents.yaml`, causing a KeyError.

### Target State (Fixed)

```
DeepAnalysisCrew
├── asset_analyst() ✅ - Defined in agents.yaml
└── investment_reporter() ✅ - Defined in agents.yaml
```

**Solution**: Remove the deprecated `risk_assessor()` method entirely.

## Components and Interfaces

### Files to Modify

1. **`src/finwiz/crews/deep_analysis/deep_analysis.py`**
   - Remove `risk_assessor()` agent method (lines ~410-420)
   - Remove instantiation of `risk_assessor_agent` (line ~571)
   - Remove related comments referencing risk_assessor

2. **No changes needed to `agents.yaml`** - Already correct (only has asset_analyst and investment_reporter)

## Data Models

No schema changes required. This is purely a code cleanup.

## Correctness Properties

### Property 1: Crew instantiation succeeds
*For any* valid ticker and asset_class, instantiating DeepAnalysisCrew should complete without KeyError  
**Validates: Requirements 1.1, 1.3**

### Property 2: Agent count is exactly 2
*For any* instantiated DeepAnalysisCrew, the crew should contain exactly 2 agents (asset_analyst, investment_reporter)  
**Validates: Requirements 2.2**

### Property 3: Crew execution completes
*For any* valid holding, running the crew should complete without errors  
**Validates: Requirements 2.1, 2.4**

## Error Handling

### Current Error
```python
KeyError: 'risk_assessor'
  File "deep_analysis.py", line 414, in risk_assessor
    config=self.agents_config["risk_assessor"],
```

### After Fix
No error - method removed entirely.

## Testing Strategy

### Unit Tests
- Test crew instantiation succeeds
- Test agent count is 2
- Test no risk_assessor references in agent list

### Integration Tests  
- Test deep analysis completes for stock ticker
- Test deep analysis completes for crypto ticker (BTC-USD)
- Test no KeyError exceptions during execution

### Manual Testing
- Run deep analysis on BTC-USD (the failing ticker from production)
- Verify no deprecation warnings in logs
- Confirm EnrichedAnalysis output is generated

## Implementation Steps

1. **Remove deprecated agent method** (5 minutes)
   - Delete `risk_assessor()` method from `deep_analysis.py`
   
2. **Remove agent instantiation** (2 minutes)
   - Delete `risk_assessor_agent = self.risk_assessor()` line
   
3. **Remove related comments** (2 minutes)
   - Clean up any comments referencing risk_assessor
   
4. **Verify no other references** (5 minutes)
   - Search codebase for any remaining risk_assessor references
   
5. **Test** (10 minutes)
   - Run unit tests
   - Run integration test with BTC-USD
   - Verify production scenario works

**Total Estimated Time**: 25 minutes

## Risks and Mitigations

### Risk 1: Breaking existing functionality
**Likelihood**: Very Low  
**Impact**: High  
**Mitigation**: The risk_assessor was already deprecated and not being used. Removing it only fixes the KeyError.

### Risk 2: Missing references elsewhere
**Likelihood**: Low  
**Impact**: Medium  
**Mitigation**: Comprehensive grep search for all risk_assessor references before marking complete.

## Success Criteria

- ✅ DeepAnalysisCrew instantiates without KeyError
- ✅ Crew contains exactly 2 agents
- ✅ Deep analysis completes for BTC-USD
- ✅ No deprecation warnings in logs
- ✅ All existing tests still pass

---

**Version**: 1.0  
**Created**: 2025-01-22  
**Estimated Effort**: 25 minutes
