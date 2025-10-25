# Requirement 3 Completion Plan

**Date**: 2025-01-14  
**Status**: ⚠️ INCOMPLETE - 6/12 acceptance criteria met (50%)

---

## Executive Summary

Requirement 3 (Flow Resume Capability) is **not fulfilled**. While the core state persistence mechanism works via CrewAI's `@persist()` decorator, the user-facing resume functionality is completely missing.

**Critical Gap**: Users cannot resume interrupted flows because there's no mechanism to discover, select, or load existing states.

---

## What's Working ✅

1. **State Persistence** - `@persist()` decorator saves state automatically
2. **Conditional Start** - `@start("validate_data_integration")` enables resume logic
3. **Progress Tracking** - Holdings processed/remaining tracked in state
4. **Error Recovery** - Failed holdings tracked for retry
5. **State Merging** - New results merge with existing state
6. **Graceful Degradation** - Continues with partial results

---

## What's Missing ❌

### 1. **State Discovery** (Criteria #1, #2)
**Problem**: No mechanism to find existing persisted states

**Required**:
- Scan `~/.crewai/state/` directory for .db files
- Extract metadata (UUID, age, progress) from each state
- Display list of available sessions to user

**Impact**: Users don't know if resumable states exist

---

### 2. **User Prompt** (Criteria #2, #3)
**Problem**: No interactive prompt for resume vs fresh start

**Required**:
- Display available states with metadata
- Prompt user: "Resume", "Start Fresh", or "Cancel"
- Warn if state is stale (>24h)
- Allow user to select which state to resume

**Impact**: System auto-resumes without user control

---

### 3. **CLI Arguments** (Criteria #12)
**Problem**: No command-line control over resume behavior

**Required**:
- `--resume-uuid <uuid>` - Resume specific session
- `--no-resume` - Force fresh start

**Impact**: Cannot script or automate resume behavior

---

### 4. **State Age Validation** (Criteria #2, #8)
**Problem**: No check for 24-hour expiry

**Required**:
- Calculate state age from `flow_start_time`
- Compare against `FINWIZ_STATE_MAX_AGE_HOURS` (default: 24)
- Warn user if state is stale
- Allow override with confirmation

**Impact**: May resume from stale/outdated state

---

### 5. **State Cleanup** (Criteria #11)
**Problem**: No automatic cleanup of old states

**Required**:
- Optional cleanup on successful completion
- Configurable via `FINWIZ_CLEANUP_STATE_ON_SUCCESS`
- Delete states older than N days
- Prevent state directory bloat

**Impact**: State directory grows indefinitely

---

### 6. **Error Handling** (Criteria #9)
**Problem**: No handling for corrupted/incompatible states

**Required**:
- Detect SQLite corruption
- Detect schema incompatibility
- Log clear error message
- Automatically fall back to fresh start

**Impact**: Cryptic errors if state is corrupted

---

## Implementation Tasks

### Phase 1: Core Infrastructure (Tasks 18, 22)

**Task 18: FlowStateManager** (Priority: HIGH)
- Create `src/finwiz/utils/flow_state_manager.py`
- Implement state discovery from `~/.crewai/state/`
- Implement metadata extraction from SQLite
- Implement user prompt with state selection
- Implement state loading by UUID
- Implement state cleanup

**Task 22: ResilienceConfig Updates** (Priority: HIGH)
- Add `cleanup_state_on_success` field
- Add `state_cleanup_max_age_days` field
- Update validation

**Estimated Time**: 4-6 hours

---

### Phase 2: CLI Integration (Tasks 19, 23)

**Task 19: CLI Arguments** (Priority: HIGH)
- Add `--resume-uuid` argument
- Add `--no-resume` flag
- Implement `initialize_flow_with_resume()`
- Integrate with FlowStateManager

**Task 23: Environment Variables** (Priority: MEDIUM)
- Update `.env.example`
- Document new variables
- Document CLI arguments

**Estimated Time**: 2-3 hours

---

### Phase 3: Flow Integration (Tasks 20, 21)

**Task 20: Flow Orchestrator Updates** (Priority: HIGH)
- Check `resume_from_checkpoint` flag in methods
- Log skip messages with details
- Return skip status for resumed work

**Task 21: State Cleanup** (Priority: MEDIUM)
- Add cleanup at flow completion
- Check configuration flag
- Log cleanup results

**Estimated Time**: 2-3 hours

---

### Phase 4: Testing & Documentation (Tasks 18.1, 19.1, 24, 25)

**Task 18.1: FlowStateManager Tests** (Priority: HIGH)
- Test state discovery
- Test metadata extraction
- Test user prompt
- Test state loading
- Test cleanup

**Task 19.1: CLI Tests** (Priority: MEDIUM)
- Test argument parsing
- Test flow initialization
- Test error handling

**Task 24: Documentation** (Priority: MEDIUM)
- Update USER_GUIDE.md
- Add resume examples
- Document CLI usage

**Task 25: Integration Tests** (Priority: LOW - OPTIONAL)
- End-to-end resume test
- Stale state test
- Corrupted state test

**Estimated Time**: 4-5 hours

---

## Total Effort Estimate

**Core Tasks (18-21, 22, 23)**: 8-12 hours  
**Testing (18.1, 19.1)**: 3-4 hours  
**Documentation (24)**: 1-2 hours  
**Optional (25)**: 2-3 hours

**Total**: 12-18 hours for complete implementation

---

## Acceptance Criteria Checklist

After implementation, verify:

- [ ] 1. System checks for existing persisted states on startup
- [ ] 2. System displays list of available sessions with metadata
- [ ] 3. System prompts user: "Resume", "Start Fresh", or "Cancel"
- [ ] 4. User can select "Resume" to load selected state
- [ ] 5. Conditional @start() skips completed work when resuming
- [ ] 6. System logs which holdings are skipped vs remaining
- [ ] 7. User can select "Start Fresh" to create new UUID
- [ ] 8. System warns if state >24h but allows resume
- [ ] 9. System handles corrupted state gracefully
- [ ] 10. System merges persisted + new results
- [ ] 11. System optionally cleans up state on success
- [ ] 12. User can provide --resume-uuid to skip prompt

---

## Risk Assessment

**High Risk**:
- SQLite state format may change with CrewAI updates
- State corruption could cause data loss

**Mitigation**:
- Implement robust error handling
- Always allow fallback to fresh start
- Add state validation before loading

**Medium Risk**:
- User confusion with multiple states
- Stale state causing incorrect results

**Mitigation**:
- Clear UI with metadata display
- Prominent warnings for stale states
- Automatic cleanup of old states

---

## Success Criteria

Implementation is complete when:

1. ✅ User can see list of available states on startup
2. ✅ User can choose to resume or start fresh
3. ✅ System skips already-completed work when resuming
4. ✅ System validates state age and warns appropriately
5. ✅ System handles errors gracefully
6. ✅ CLI arguments work for automation
7. ✅ State cleanup prevents directory bloat
8. ✅ All 12 acceptance criteria are met
9. ✅ Unit tests pass for new components
10. ✅ Documentation is complete

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Prioritize tasks** based on urgency
3. **Implement Phase 1** (FlowStateManager + Config)
4. **Test Phase 1** before proceeding
5. **Implement Phase 2** (CLI integration)
6. **Implement Phase 3** (Flow integration)
7. **Complete Phase 4** (Testing + Docs)
8. **Verify all acceptance criteria**
9. **Update IMPLEMENTATION_REVIEW.md** to reflect completion

---

**Version**: 1.0  
**Created**: 2025-01-14  
**Purpose**: Complete Requirement 3 implementation
