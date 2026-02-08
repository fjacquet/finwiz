# Roadmap: FinWiz

## Milestones

- v1 Hardening & Discovery - Phases 1-5 (shipped 2026-02-08)
- v2 Security & Structural Quality - Phases 6-8 (in progress)

## Phases

<details>
<summary>v1 Hardening & Discovery (Phases 1-5) - SHIPPED 2026-02-08</summary>

See: milestones/v1-ROADMAP.md for full phase details.

Phases completed: 1-5 (13 plans total)

</details>

### v2 Security & Structural Quality (In Progress)

**Milestone Goal:** Harden security, eliminate structural debt, and automate code quality enforcement.

**Phase Numbering:**
- Integer phases (6, 7, 8): Planned milestone work
- Decimal phases (6.1, 7.1): Urgent insertions if needed (marked with INSERTED)

- [ ] **Phase 6: Security Hardening** - Fail-fast key validation, log sanitization, centralized endpoints
- [ ] **Phase 7: Structural Refactoring** - Deduplicate portfolio review, redesign orchestrator loading
- [ ] **Phase 8: Code Quality Enforcement** - Pre-commit hooks and CI pipeline for automated checks

## Phase Details

### Phase 6: Security Hardening
**Goal**: Sensitive data is protected at rest in logs and at runtime via fail-fast validation, with all API endpoints centrally configured
**Depends on**: Nothing (first phase of v2)
**Requirements**: SEC-01, SEC-02, SEC-03
**Success Criteria** (what must be TRUE):
  1. Instantiating any tool class without its required API key raises `ValueError` immediately — no silent degradation or deferred runtime error
  2. Log output from a full portfolio analysis run contains zero API keys, tokens, or credentials when inspected with grep
  3. Every API endpoint URL is defined in a single configuration module — no hardcoded URLs remain in tool or service files
**Plans**: TBD

Plans:
- [ ] 06-01: TBD
- [ ] 06-02: TBD

### Phase 7: Structural Refactoring
**Goal**: Duplicate logic is consolidated and import architecture eliminates circular dependency risk
**Depends on**: Phase 6
**Requirements**: REFAC-01, REFAC-02
**Success Criteria** (what must be TRUE):
  1. Portfolio review logic exists in exactly one shared module, and all former duplicate sites import from it (zero copy-paste implementations remain)
  2. `python -c "from finwiz.flows.orchestrator import FinwizFlow"` succeeds cleanly with no circular import warnings — orchestrator loading uses registry or DI pattern
  3. All existing tests pass after refactoring with no regressions (`make test` green)
**Plans**: TBD

Plans:
- [ ] 07-01: TBD
- [ ] 07-02: TBD

### Phase 8: Code Quality Enforcement
**Goal**: Quality standards are automatically enforced on every commit and every CI build, preventing regressions
**Depends on**: Phase 7
**Requirements**: QUAL-01, QUAL-02
**Success Criteria** (what must be TRUE):
  1. A commit containing a ruff violation, a new file over 300 lines, or a `unittest.mock` import is rejected by pre-commit hooks before reaching the repository
  2. CI pipeline fails the build when any pre-commit quality check fails — same rules, same outcome
  3. `make check` locally produces the same pass/fail result as CI (no environment-specific divergence)
**Plans**: TBD

Plans:
- [ ] 08-01: TBD
- [ ] 08-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 6 -> 7 -> 8

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 6. Security Hardening | v2 | 0/TBD | Not started | - |
| 7. Structural Refactoring | v2 | 0/TBD | Not started | - |
| 8. Code Quality Enforcement | v2 | 0/TBD | Not started | - |

---
*Created: 2026-02-08 for milestone v2*
