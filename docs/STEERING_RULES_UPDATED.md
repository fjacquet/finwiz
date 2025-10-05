# Steering Rules Updated - unittest.mock Ban

## Summary

I've added **unittest.mock enforcement** to the steering rules so it's **always included in AI context**.

## Files Updated

### 1. `.kiro/steering/unittest-mock-ban.md` (NEW)

**Status**: ✅ Created with `inclusion: always` frontmatter

**Purpose**: Dedicated steering file for unittest.mock ban

**Content**:

- Critical rule explanation
- All 4 enforcement layers documented
- Required patterns (pytest-mock)
- Banned patterns (unittest.mock)
- Quick migration guide
- Common patterns and examples
- Verification commands
- What happens if you try to use it

**Frontmatter**:

```yaml
---
inclusion: always
---
```

This ensures the rule is **always included** in AI agent context.

### 2. `.kiro/steering/testing-standards.md` (UPDATED)

**Changes**:

- Added unittest.mock enforcement section at the top
- Updated Core Testing Principles with ban notice
- Added enforcement commands
- Updated Anti-Patterns section with 4-layer enforcement
- Added unittest.mock violations section
- Updated Test Quality Checklist with enforcement as #1 item
- Added Pre-Commit Verification section

### 3. `.kiro/steering/quality.md` (UPDATED)

**Changes**:

- Added unittest.mock ban to Core Rules
- Added unittest.mock Enforcement section
- Documented all 4 enforcement layers
- Added correct/banned examples
- Referenced full documentation

### 4. `.kiro/steering/tech.md` (UPDATED)

**Changes**:

- Updated Core Technology Stack description
- Added `make check-unittest-mock` to Essential Commands
- Added unittest.mock is BANNED section
- Documented all 4 enforcement layers
- Added correct/banned examples
- Referenced documentation

## What This Means

### For AI Agents

When AI agents work on this codebase, they will **always see**:

- unittest.mock is BANNED
- 4 enforcement layers are active
- Only pytest-mock is allowed
- Clear examples of correct patterns
- Migration instructions

### For Developers

The steering rules ensure:

- Consistent messaging across all AI interactions
- Clear documentation of the ban
- Examples always available
- No confusion about which mocking library to use

## Steering File Structure

```
.kiro/steering/
├── unittest-mock-ban.md        # NEW - Dedicated ban documentation
├── testing-standards.md         # UPDATED - Added enforcement
├── quality.md                   # UPDATED - Added enforcement
├── tech.md                      # UPDATED - Added enforcement
├── agents.md                    # (existing)
├── crewai-standards.md         # (existing)
├── finance.md                   # (existing)
├── finwiz-guide.md             # (existing)
├── output-standards.md         # (existing)
├── product.md                   # (existing)
├── security.md                  # (existing)
├── structure.md                 # (existing)
└── validation.md                # (existing)
```

## Verification

All steering files with unittest.mock enforcement have been updated:

```bash
# Check the new steering file
cat .kiro/steering/unittest-mock-ban.md

# Verify frontmatter
head -5 .kiro/steering/unittest-mock-ban.md
# Output: ---
#         inclusion: always
#         ---

# Check updated files
grep -l "unittest.mock" .kiro/steering/*.md
# Output: unittest-mock-ban.md
#         testing-standards.md
#         quality.md
#         tech.md
```

## How Steering Works

Steering files with `inclusion: always` are:

1. **Automatically included** in AI agent context
2. **Always available** for reference
3. **Consistently applied** across all interactions

This means every AI agent working on this codebase will:

- Know unittest.mock is banned
- Use pytest-mock exclusively
- Follow the correct patterns
- Reference the enforcement documentation

## Complete Documentation Stack

Now you have **comprehensive documentation** at multiple levels:

### 1. Steering Rules (Always in AI Context)

- `.kiro/steering/unittest-mock-ban.md` - Dedicated ban rule
- `.kiro/steering/testing-standards.md` - Testing standards
- `.kiro/steering/quality.md` - Quality standards
- `.kiro/steering/tech.md` - Technical standards

### 2. Developer Documentation

- `docs/TESTING_ENFORCEMENT.md` - Full enforcement guide
- `docs/UNITTEST_MOCK_BLACKLIST.md` - Quick reference
- `UNITTEST_MOCK_ENFORCEMENT_SUMMARY.md` - Implementation details

### 3. Enforcement Mechanisms

- `pyproject.toml` - Ruff TID rules
- `.git/hooks/pre-commit` - Pre-commit hook
- `tests/conftest_unittest_blocker.py` - Runtime blocker
- `Makefile` - Manual check target

### 4. Task Tracking

- `.kiro/specs/finwiz-codebase-modernization/tasks.md` - Conversion tasks

## Benefits

1. **AI Consistency**: All AI agents see the same rules
2. **Developer Clarity**: Clear documentation at all levels
3. **Enforcement**: 4 layers prevent violations
4. **Guidance**: Examples and migration paths always available
5. **Tracking**: Tasks document conversion progress

## Next Steps

1. ✅ Steering rules updated (COMPLETE)
2. ✅ Enforcement mechanisms installed (COMPLETE)
3. ✅ Documentation created (COMPLETE)
4. ⏳ Convert existing 61 test files (Phase 1 in tasks.md)
5. ⏳ Verify with `make check-unittest-mock` after each conversion

---

**Status**: ✅ All steering rules updated and active
**Impact**: AI agents will always know unittest.mock is banned
**Documentation**: Complete at all levels (steering, docs, enforcement)
