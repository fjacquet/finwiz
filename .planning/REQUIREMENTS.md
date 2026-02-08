# Requirements: v2 Security & Structural Quality

## Security Hardening

- [ ] **SEC-01**: Tool classes validate required API keys at `__init__` and raise `ValueError` immediately if missing (fail-fast, no silent degradation)
- [ ] **SEC-02**: Log output sanitizes sensitive data (API keys, tokens, credentials) before writing, using a centralized sanitizer
- [ ] **SEC-03**: All hardcoded API endpoint URLs consolidated into a single configuration module with per-service defaults

## Structural Refactoring

- [ ] **REFAC-01**: Duplicate portfolio review logic across 10+ files consolidated into a single shared implementation
- [ ] **REFAC-02**: Lazy-loaded orchestrators in `FinwizFlow` replaced with a design that eliminates circular import risk (e.g., registry pattern or dependency injection)

## Code Quality Tooling

- [ ] **QUAL-01**: Pre-commit hooks enforce ruff lint/format, file size limits (300 lines for new files), and unittest.mock ban on every commit
- [ ] **QUAL-02**: CI pipeline runs the same quality checks as pre-commit, failing the build on violations

## Future Requirements

None — all proposed features included in this milestone.

## Out of Scope

- File size splits for existing files (150+ files, enforce for new code only)
- API key rotation (runtime key refresh too complex for v2)
- Multi-user support (architectural change)
- Real-time data / streaming (future milestone)

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEC-01 | — | Pending |
| SEC-02 | — | Pending |
| SEC-03 | — | Pending |
| REFAC-01 | — | Pending |
| REFAC-02 | — | Pending |
| QUAL-01 | — | Pending |
| QUAL-02 | — | Pending |

---
*Created: 2026-02-08 for milestone v2*
