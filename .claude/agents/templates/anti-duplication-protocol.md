---
name: anti-duplication-protocol
description: Anti-duplication protocol template for preventing code duplication across agents
---
# 🚨 ANTI-DUPLICATION PROTOCOL TEMPLATE

This template should be added to ALL agents that generate code (Edit, MultiEdit, Write tools).

## Template Section to Add

```markdown
## 🚨 CRITICAL: ANTI-DUPLICATION PROTOCOL

**MANDATORY BEFORE ANY CODE GENERATION:**

### 1. EXISTING CODE DISCOVERY
```bash
# ALWAYS scan for existing implementations first
Read src/                          # Examine project structure  
Grep -r "ComponentName" src/       # Search for existing components
Grep -r "functionName" src/        # Search for existing functions
Grep -r "className" src/           # Search for existing classes
LS tests/                          # Check existing test structure
Grep -r "describe.*Component" tests/ --include="*.test.*"  # Find existing tests
```

### 2. MEMORY-BASED DUPLICATION CHECK
```bash
# Check organizational memory for similar implementations
mcp__basic-memory__search_notes "implementation ComponentName"
mcp__basic-memory__search_notes "pattern similar-functionality"
```

### 3. STRICT NO-DUPLICATION RULES
**NEVER CREATE:**
- Components that already exist with similar functionality
- Functions that duplicate existing utility methods
- Test files for components that already have tests
- Configuration that duplicates existing setup
- Types/interfaces that already exist
- Styles/CSS that duplicate existing patterns

### 4. ENHANCEMENT-FIRST APPROACH
**INSTEAD OF DUPLICATING:**
- ✅ **Extend existing components** with new props/methods
- ✅ **Enhance existing functions** with additional parameters
- ✅ **Add test cases** to existing test files
- ✅ **Import and reuse** existing implementations
- ✅ **Build upon established patterns** in the codebase

### 5. PRE-GENERATION VERIFICATION
Before generating ANY code, confirm:
- [ ] I have thoroughly examined ALL existing code
- [ ] I have searched for similar implementations using Grep
- [ ] I have checked Basic Memory MCP for past solutions
- [ ] I am NOT duplicating ANY existing functionality
- [ ] My solution extends rather than replaces existing code
- [ ] I will reuse existing patterns and utilities

**DUPLICATION PREVENTION IS CRITICAL FOR CODE QUALITY AND MAINTAINABILITY.**
```

## Agents That Need This Protocol

1. **Frontend Agents:**
   - react-expert.md
   - vue-expert.md  
   - angular-expert.md
   - nextjs-expert.md

2. **Backend Agents:**
   - nodejs-expert.md
   - python-expert.md
   - django-expert.md
   - fastapi-expert.md
   - rails-expert.md
   - laravel-expert.md
   - gin-expert.md
   - fastify-expert.md

3. **Specialized Agents:**
   - database-architect.md
   - security-specialist.md
   - deployment-specialist.md
   - performance-optimizer.md

4. **Testing/QA Agents:**
   - test-automation-expert.md ✅ (Already updated)
   - qa-automation-engineer.md

## Implementation Instructions

1. Add the protocol section at the top of each agent file (after the front matter)
2. Customize the specific search patterns for each framework/technology
3. Ensure agents use the verification checklist before any code generation
4. Test with common duplication scenarios to verify effectiveness

## Framework-Specific Customizations

### React Expert
```bash
Grep -r "export.*Component" src/components/
Grep -r "useState\|useEffect" src/
Grep -r "interface.*Props" src/
```

### Node.js Expert  
```bash
Grep -r "module.exports\|export" src/
Grep -r "class.*\|function.*" src/
Grep -r "require.*\|import.*" src/
```

### Testing Expert
```bash
Grep -r "describe.*\|it.*should" tests/
Grep -r "jest.mock\|sinon.stub" tests/
Grep -r "beforeEach\|afterEach" tests/
```
