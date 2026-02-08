# Requirements Archive: v2 Security & Structural Quality

**Archived:** 2026-02-08
**Status:** SHIPPED

This is the archived requirements specification for v2.
For current requirements, see `.planning/REQUIREMENTS.md` (created for next milestone).

---

## Security Hardening

- [x] **SEC-01**: Tool classes validate required API keys at `__init__` and raise `ValueError` immediately if missing (fail-fast, no silent degradation)
- [x] **SEC-02**: Log output sanitizes sensitive data (API keys, tokens, credentials) before writing, using a centralized sanitizer
- [x] **SEC-03**: All hardcoded API endpoint URLs consolidated into a single configuration module with per-service defaults

## Structural Refactoring

- [x] **REFAC-01**: Duplicate portfolio review logic across 10+ files consolidated into a single shared implementation
- [x] **REFAC-02**: Lazy-loaded orchestrators in `FinwizFlow` replaced with a design that eliminates circular import risk (e.g., registry pattern or dependency injection)

## Code Quality Tooling

- [x] **QUAL-01**: Pre-commit hooks enforce ruff lint/format, file size limits (300 lines for new files), and unittest.mock ban on every commit
- [x] **QUAL-02**: CI pipeline runs the same quality checks as pre-commit, failing the build on violations

## Out of Scope

- File size splits for existing files (150+ files, enforce for new code only)
- API key rotation (runtime key refresh too complex for v2)
- Multi-user support (architectural change)
- Real-time data / streaming (future milestone)

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEC-01 | Phase 6 | Complete |
| SEC-02 | Phase 6 | Complete |
| SEC-03 | Phase 6 | Complete |
| REFAC-01 | Phase 7 | Complete |
| REFAC-02 | Phase 7 | Complete |
| QUAL-01 | Phase 8 | Complete |
| QUAL-02 | Phase 8 | Complete |

---

## Milestone Summary

**Shipped:** 7 of 7 requirements
**Adjusted:** None — all requirements delivered as originally specified
**Dropped:** None

---
*Archived: 2026-02-08 as part of v2 milestone completion*
