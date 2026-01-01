# YAML Prompt Quality Improvements - Implementation TODO

> Generated: 2026-01-01
> Status: Phase 1 Complete, Phase 2-3 Pending
> Priority: High

## Overview

This document captures actionable improvements for all CrewAI YAML configurations in `src/finwiz/crews/`. Tasks are organized by priority with checkboxes for tracking progress.

---

## Current Quality Assessment

| Crew | Score | Key Issue |
|------|-------|-----------|
| deep_analysis | **A** | Reference implementation |
| report_crew | **A** | Best anti-hallucination |
| investment_discovery | **B+** | Verbose, needs anchors |
| portfolio_rebalancing | **B+** | Goal/backstory imbalance |
| stock_crew | **B** | Needs French + anti-hallucination |
| etf_crew | **B** | Needs French + anti-hallucination |
| crypto_crew | **B** | Needs French + anti-hallucination |

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

## Phase 2: Medium Priority

### Task 2.1: Refactor Goal vs Backstory

**Files:**
- [ ] `src/finwiz/crews/portfolio_rebalancing_crew/config/agents.yaml`
- [ ] `src/finwiz/crews/investment_discovery_crew/config/agents.yaml`

**Target pattern:**
```yaml
agent_name:
  role: "[1 line job title]"
  goal: "[1-3 sentences: Primary objective]"
  backstory: >
    [Experience + Constraints + KB instructions + Output Language]
```

### Task 2.2: Implement YAML Anchors

**Files:**
- [ ] `src/finwiz/crews/investment_discovery_crew/config/tasks.yaml`
- [ ] `src/finwiz/crews/report_crew/config/tasks.yaml`

**Anchors to create:**
- `&anti_hallucination` - Anti-hallucination rules block
- `&json_output` - JSON output requirements block
- `&risk_format` - Risk assessment format block

### Task 2.3: Add Context Variable Documentation

**Files:**
- [ ] `src/finwiz/crews/stock_crew/config/tasks.yaml`
- [ ] `src/finwiz/crews/etf_crew/config/tasks.yaml`
- [ ] `src/finwiz/crews/crypto_crew/config/tasks.yaml`
- [ ] `src/finwiz/crews/deep_analysis/config/tasks.yaml`

**Template:**
```yaml
Available Context Variables:
- {ticker}: Asset symbol (e.g., "AAPL", "BTC-USD")
- {asset_class}: "stock", "etf", or "crypto"
- {company_name}: Full entity name
```

---

## Phase 3: Low Priority (Backlog)

### Task 3.1: Condense KB Instructions
- [ ] Reduce from 15-20 lines to 3-4 lines across all agents

### Task 3.2: Add Expected Output Examples
- [ ] Add examples to DeepAnalysisExport tasks
- [ ] Add examples to PortfolioRebalancingExport tasks

### Task 3.3: Create Shared Context File
- [ ] Create `src/finwiz/crews/shared/common_instructions.yaml`
- [ ] Refactor crews to import shared instructions

---

## Validation

After each phase, run:
```bash
make test                    # Ensure tests pass
crewai flow kickoff          # Verify crews execute
```

**Final checklist:**
- [ ] All crews have anti-hallucination rules
- [ ] All crews specify French output
- [ ] No commented-out code remains
- [ ] Goals are 1-3 sentences max
- [ ] YAML anchors eliminate duplication

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
