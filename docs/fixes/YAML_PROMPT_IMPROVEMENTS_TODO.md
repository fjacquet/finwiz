# YAML Prompt Quality Improvements - Implementation TODO

> Generated: 2026-01-01
> Status: Phase 1-2 Complete, Phase 3 Pending
> Priority: Low (Backlog)

## Overview

This document captures actionable improvements for all CrewAI YAML configurations in `src/finwiz/crews/`. Tasks are organized by priority with checkboxes for tracking progress.

---

## Current Quality Assessment

| Crew                  | Score  | Key Issue                         |
| --------------------- | ------ | --------------------------------- |
| deep_analysis         | **A**  | Reference implementation          |
| report_crew           | **A**  | Best anti-hallucination           |
| investment_discovery  | **B+** | Verbose, needs anchors            |
| portfolio_rebalancing | **B+** | Goal/backstory imbalance          |
| stock_crew            | **B**  | Needs French + anti-hallucination |
| etf_crew              | **B**  | Needs French + anti-hallucination |
| crypto_crew           | **B**  | Needs French + anti-hallucination |

---

## Phase 1: High Priority ✅ COMPLETE (2026-01-01)

### Task 1.1: Add Anti-Hallucination Rules ✅ COMPLETE

**Files:**

- [x] `src/finwiz/crews/stock_crew/config/tasks.yaml`
- [x] `src/finwiz/crews/etf_crew/config/tasks.yaml`
- [x] `src/finwiz/crews/crypto_crew/config/tasks.yaml`
- [x] `src/finwiz/crews/portfolio_rebalancing_crew/config/tasks.yaml`

**Template to insert:**

```yaml
⚠️ CRITICAL ANTI-HALLUCINATION RULES:
  - NEVER invent or guess URLs, ISINs, or company names
  - NEVER fabricate financial metrics or prices
  - If data is missing, explicitly state "Données non disponibles"
  - All URLs must come from verified data sources
  - Cross-reference data points before including in output
```

### Task 1.2: Add French Language Directive ✅ COMPLETE

**Files:**

- [x] `src/finwiz/crews/stock_crew/config/agents.yaml`
- [x] `src/finwiz/crews/etf_crew/config/agents.yaml`
- [x] `src/finwiz/crews/crypto_crew/config/agents.yaml`

**Template to insert (reporter agents):**

```yaml
OUTPUT LANGUAGE: French (Français)
All analysis text, recommendations, and explanations must be in French.
Technical terms (ticker symbols, financial ratios) remain in English.
```

### Task 1.3: Remove Commented-Out Code ✅ COMPLETE

- [x] `src/finwiz/crews/portfolio_rebalancing_crew/config/agents.yaml` - Removed `translator` agent
- [x] `src/finwiz/crews/report_crew/config/agents.yaml` - Removed `pdf_conversion_specialist` and `translator`
- [x] `src/finwiz/crews/etf_crew/config/agents.yaml` - Removed `translator` agent (bonus cleanup)
- [x] `src/finwiz/crews/crypto_crew/config/agents.yaml` - Removed `translator` agent (bonus cleanup)

---

## Phase 2: Medium Priority ✅ COMPLETE (2026-01-01)

### Task 2.1: Refactor Goal vs Backstory ✅ COMPLETE

**Files:**

- [x] `src/finwiz/crews/portfolio_rebalancing_crew/config/agents.yaml` - Refactored 6 agents
- [x] `src/finwiz/crews/investment_discovery_crew/config/agents.yaml` - Already well-structured

**Applied pattern:**

```yaml
agent_name:
  role: "[1 line job title]"
  goal: "[1-3 sentences: Primary objective]"
  backstory: >
    [Experience + Constraints + KB instructions + Output Language]
```

### Task 2.2: Implement YAML Anchors ⏸️ DEFERRED

**Reason:** CrewAI's YAML parser may not properly handle YAML anchors. Risk of breaking crew execution outweighs DRY benefits. Each task has context-specific variations that make anchors less valuable.

**Decision:** Skip this task; repeated blocks are acceptable for reliability.

### Task 2.3: Add Context Variable Documentation ✅ COMPLETE

**Files:**

- [x] `src/finwiz/crews/stock_crew/config/tasks.yaml`
- [x] `src/finwiz/crews/etf_crew/config/tasks.yaml`
- [x] `src/finwiz/crews/crypto_crew/config/tasks.yaml`
- [x] `src/finwiz/crews/deep_analysis/config/tasks.yaml`

**Added documentation block:**

```yaml
# AVAILABLE CONTEXT VARIABLES:
# - {ticker}: Asset symbol (e.g., "AAPL", "BTC-USD")
# - {asset_class}: "stock", "etf", or "crypto"
# - {company_name}: Full entity name
# - {grade}: Python-calculated grade (A+, A, B, C, D, F)
# - {composite_score}: Python-calculated overall score (0.0-1.0)
# ... (full list per crew type)
```

---

## Phase 3: Low Priority ✅ COMPLETE (2026-01-01)

### Task 3.1: Condense KB Instructions ✅ COMPLETE

- [x] Condensed etf_crew/config/agents.yaml: market_etf_analyst, risk_assessor
- [x] Condensed report_crew/config/agents.yaml: portfolio_allocator, risk_manager
- [x] Other crews already follow concise KB pattern (refactored in Phase 2)

**Applied pattern:**
```yaml
**Knowledge Base Usage**: Query "{ticker} [topic]" before analysis.
Store findings with ticker, date, key metrics. Update when data changes.
```

### Task 3.2: Add Expected Output Examples ⏸️ DEFERRED

**Reason:** Portfolio rebalancing tasks already have extensive documentation:
- REQUIRED FIELDS TO EXTRACT FROM CONTEXT sections
- VALIDATION requirements with specific thresholds
- REQUIRED ENUM VALUES specifications
- JSON OUTPUT REQUIREMENTS blocks

DeepAnalysisExport tasks already have full JSON examples (lines 159-202).
Adding more examples provides diminishing returns vs file size increase.

### Task 3.3: Create Shared Context File ⏸️ DEFERRED

**Reason:** CrewAI's YAML loader may not support external imports.
Each crew has context-specific variations. Current approach is reliable.

---

## Validation

After each phase, run:

```bash
make test                    # Ensure tests pass
crewai flow kickoff          # Verify crews execute
```

**Final checklist:**

- [x] All crews have anti-hallucination rules
- [x] All crews specify French output
- [x] No commented-out code remains
- [x] Goals are 1-3 sentences max (portfolio_rebalancing_crew refactored)
- [x] Context variables documented in all tasks.yaml files
- [ ] YAML anchors (deferred - not recommended for CrewAI)

---

## Reference Templates

### Agent Template

```yaml
agent_name:
  role: >
    Senior Financial Analyst
  goal: >
    Analyze {ticker} ({asset_class}) and provide actionable investment insights.
  backstory: >
    Expert analyst with 15+ years in {asset_class} analysis.

    **Constraints**: Only use verified data sources. Never fabricate metrics.
    **Knowledge Base**: Search "{ticker} [topic]" before analysis.
    **Output Language**: French (technical terms in English)
  verbose: true
  allow_delegation: false
```

### Task Template

```yaml
task_name:
  description: >
    Analyze {ticker} for {company_name}.

    Available Variables: {ticker}, {asset_class}, {company_name}

    ⚠️ ANTI-HALLUCINATION: Never invent data. State "Non disponible" if missing.
    🚨 JSON OUTPUT: Valid JSON only, no trailing commas.

    REQUIRED SCHEMA:
    - ticker: str
    - grade: "A+"|"A"|"B"|"C"|"D"|"F"
    - recommendation: "BUY"|"HOLD"|"SELL"
  expected_output: "Structured JSON analysis"
  output_pydantic: AnalysisExport
  agent: analyst
  async_execution: true
```

---

## Notes

- Do NOT change task logic - only improve prompt quality
- Preserve Pydantic schemas - output validation must remain intact
- Reference `deep_analysis` and `report_crew` as exemplary implementations
