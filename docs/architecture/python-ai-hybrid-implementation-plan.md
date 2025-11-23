# Python-AI Hybrid Architecture - Implementation Plan

**Date**: 2025-11-21
**Status**: Ready for Execution
**Timeline**: 6 weeks
**Project Manager**: project-analyst agent

---

## 📋 Executive Summary

This implementation plan outlines the strategy to restore analytical depth to FinWiz while maintaining the 10-20x performance gains achieved through AI Minimalism. The hybrid architecture leverages Python for deterministic calculations and AI for contextual analysis, delivering the best of both worlds.

**Core Principle**: "Python calculates, AI analyzes"

### Success Metrics

| Metric | Target | Baseline | Status |
|--------|--------|----------|--------|
| Performance | ≤30s per holding | ✅ Achieved | Maintain |
| Cost | ≤$0.10 per holding | ✅ Achieved | Maintain |
| Report Quality | ≥2000 words | ~500 words | Restore |
| Qualitative Insights | ≥5 per report | 0-1 | Restore |
| Actionability | Bull/base/bear + strategy | Missing | Restore |

---

## 🗺️ 6-Phase Implementation Roadmap

### Phase 1: Schema Foundation (Week 1)

**Task ID**: #1
**Priority**: CRITICAL
**Dependencies**: None

#### Objective

Establish type-safe Pydantic v2 data models for the hybrid architecture.

#### Deliverables

1. **QuantitativeAnalysis Schema** (Python output)
   - `composite_score`, `fundamental_score`, `technical_score`, `risk_score`
   - `grade` (A+ to F), `preliminary_recommendation` (BUY/HOLD/SELL)
   - Detailed metrics dictionaries
   - Metadata (data_quality, lineage, confidence)

2. **QualitativeInsights Schema** (AI output)
   - `sec_insights`, `fundamental_context`, `technical_strategy`
   - `contextual_risks`, `investment_strategy`
   - All contextual and narrative fields

3. **EnrichedAnalysis Schema** (Combined)
   - Combines quantitative + qualitative
   - `final_grade`/`score`/`recommendation`
   - `recommendation_confidence` (AI: LOW/MEDIUM/HIGH)
   - `executive_summary`, `investment_rationale`, `action_plan`

4. **Supporting Schemas** (10+ schemas)
   - SecAnalysisInsights, FundamentalContextInsights
   - TechnicalStrategyInsights, ContextualRiskInsights
   - InvestmentSynthesis, GrowthDriver, ChartPattern
   - EntryExitStrategy, StressScenario, AlternativeHolding

#### Success Criteria

- [ ] All schemas use Pydantic v2
- [ ] Field validation rules implemented
- [ ] Type hints complete (Python 3.12+)
- [ ] Unit tests for schema validation (≥65% coverage)
- [ ] Documentation strings for all schemas and fields

#### Files to Create

- `src/finwiz/schemas/enriched_analysis.py` (main schemas)
- `tests/unit/schemas/test_enriched_analysis.py` (unit tests)

---

### Phase 2: Deep Analysis Orchestrator Refactoring (Week 2)

**Task ID**: #2
**Priority**: CRITICAL
**Dependencies**: Task #1

#### Objective

Update orchestrator to implement 3-step hybrid workflow combining Python calculations with AI contextual analysis.

#### Workflow Architecture

```
┌─────────────────────────────────────────┐
│   1. Python Quantitative Analysis       │
│   _process_single_holding()             │
│   → QuantitativeAnalysis                │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│   2. AI Qualitative Enrichment (NEW)    │
│   _enrich_with_qualitative_analysis()   │
│   → QualitativeInsights                 │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│   3. Synthesis (NEW)                    │
│   _synthesize_enriched_analysis()       │
│   → EnrichedAnalysis                    │
└─────────────────────────────────────────┘
```

#### Key Deliverables

1. **Modify Quantitative Processing**
   - Update `_process_single_holding()` to return QuantitativeAnalysis
   - Preserve existing Python calculation logic (NO changes to scoring)
   - Add comprehensive metadata (lineage, data_quality, confidence)
   - Ensure deterministic behavior maintained

2. **Add Qualitative Enrichment** (NEW)
   - New method: `_enrich_with_qualitative_analysis(quant_analysis, ticker, asset_class)`
   - Prepare crew inputs with Python results as READ-ONLY context
   - Route to appropriate crew (stock/etf/crypto) based on asset_class
   - Return QualitativeInsights from crew execution
   - Handle crew failures gracefully

3. **Synthesis Logic** (NEW)
   - New method: `_synthesize_enriched_analysis(quant, qual, ticker, asset_class)`
   - Combine QuantitativeAnalysis + QualitativeInsights
   - Merge into EnrichedAnalysis object
   - Preserve Python grade/score as baseline
   - Add AI confidence assessment
   - Create executive summary and action plan

4. **Workflow Integration**
   - Update batch processing loop to use 3-step workflow
   - Maintain performance optimizations (prefetch, parallel processing)
   - Update progress tracking and logging
   - Handle partial failures (Python succeeds, AI fails)
   - Preserve existing session_id and output_path logic

#### Success Criteria

- [ ] Orchestrator produces EnrichedAnalysis objects
- [ ] Python calculations unchanged and deterministic
- [ ] Qualitative analysis integrated without performance regression
- [ ] Batch processing works with new workflow
- [ ] Execution time ≤30s per holding
- [ ] Tests updated and passing (≥65% coverage)
- [ ] No breaking changes to existing API

#### Files to Modify

- `src/finwiz/orchestrators/deep_analysis_orchestrator.py`
- `tests/unit/orchestrators/test_deep_analysis_orchestrator.py`
- `tests/integration/test_deep_analysis_workflow.py`

---

### Phase 3: Stock Crew Task Refactoring (Week 3)

**Task ID**: #3
**Priority**: HIGH
**Dependencies**: Task #2

#### Objective

Transform Stock Crew from calculator to contextual analyst. Eliminate ALL calculation duplication.

#### Critical Transformation

**BEFORE (Current State)**:

- AI agents calculate everything (ROE, RSI, volatility, etc.)
- Python calculations ignored
- Duplicate work, slower execution

**AFTER (Target State)**:

- Python calculations passed as READ-ONLY context
- AI agents focus ONLY on qualitative analysis
- Zero calculation duplication
- Faster, richer outputs

#### 5 Refactored Tasks

**1. SEC Analysis Task** (Qualitative Only)

- **INPUT**: Python metrics as context (ROE, debt/equity, grade) - READ ONLY
- **FOCUS**: Business model, competitive advantages, risk factors from filings, strategic initiatives
- **PROHIBIT**: Recalculating any financial metrics
- **OUTPUT**: `SecAnalysisInsights` Pydantic schema
- **TOOLS**: Remove calculation tools, keep SEC filing tools

**2. Fundamental Context Task** (Contextual Only)

- **INPUT**: Python fundamental_score and metrics - READ ONLY
- **FOCUS**: Industry dynamics, growth drivers, competitive positioning, management quality
- **PROHIBIT**: Recalculating ROE, margins, growth rates
- **OUTPUT**: `FundamentalContextInsights`
- **TOOLS**: Remove financial calculation tools

**3. Technical Strategy Task** (Interpretation Only)

- **INPUT**: Python technical_score and indicators (RSI, MACD, trend) - READ ONLY
- **FOCUS**: Chart patterns, support/resistance, entry/exit strategy, timing assessment
- **PROHIBIT**: Recalculating RSI, MACD, or any technical indicators
- **OUTPUT**: `TechnicalStrategyInsights`
- **TOOLS**: Remove technical calculation tools

**4. Contextual Risk Task** (Contextual Risks Only)

- **INPUT**: Python risk_score and metrics (volatility, beta, drawdown) - READ ONLY
- **FOCUS**: Regulatory, geopolitical, competitive, operational risks, stress scenarios
- **PROHIBIT**: Recalculating volatility, beta, or risk metrics
- **OUTPUT**: `ContextualRiskInsights`
- **DEPENDENCIES**: sec_analysis_task

**5. Investment Synthesis Task** (Strategy & Narrative)

- **INPUT**: All previous outputs + Python grade/score/recommendation
- **FOCUS**: Investment thesis, bull/base/bear scenarios, confidence assessment, action plan, alternatives
- **ROLE**: Synthesize Python baseline with qualitative context
- **OUTPUT**: `InvestmentSynthesis`
- **DEPENDENCIES**: All previous tasks

#### Enforcement Mechanisms

1. **Explicit Prohibitions**: Task descriptions use EXACT phrasing: "Do NOT recalculate..."
2. **Tool Removal**: Remove all calculation tools from agent tool lists
3. **Context Passing**: Python metrics passed as INPUT context variables
4. **Output Validation**: Tests verify no calculation duplication

#### Success Criteria

- [ ] All 5 tasks explicitly prohibit recalculation in descriptions
- [ ] Python metrics passed as INPUT context variables
- [ ] Tool lists updated (calculation tools removed)
- [ ] Output schemas properly defined with Pydantic
- [ ] Task dependencies configured correctly
- [ ] Agent reasoning settings appropriate (reasoning=True, max_reasoning_attempts=3)
- [ ] Tests verify no calculation duplication

#### Files to Modify

- `src/finwiz/crews/stock_crew/config/tasks.yaml` (all 5 tasks)
- `src/finwiz/crews/stock_crew/config/agents.yaml` (update tool lists)
- `src/finwiz/crews/stock_crew/stock_crew.py` (task method signatures)
- `tests/unit/crews/test_stock_crew.py`

---

### Phase 4: Deep Analysis Crew Refactoring (Week 4)

**Task ID**: #4
**Priority**: HIGH
**Dependencies**: Task #3

#### Objective

Apply qualitative-focus pattern to Deep Analysis Crew with portfolio-specific enhancements.

#### 5 Deep Analysis Tasks

**1. Deep SEC Analysis**

- Deep dive into 10-K/10-Q footnotes and MD&A sections
- Red flags detection (qualitative indicators)
- Year-over-year trend analysis (qualitative narrative)
- **OUTPUT**: `DeepSecAnalysisInsights`

**2. Deep Fundamental Context**

- Quality of business assessment (durable competitive advantages)
- Sustainability of competitive advantages (long-term moat)
- Capital allocation effectiveness (qualitative management assessment)
- Long-term growth sustainability analysis
- **OUTPUT**: `DeepFundamentalContextInsights`

**3. Deep Technical Strategy**

- Multi-timeframe analysis interpretation (short vs long-term)
- Institutional flow analysis (qualitative indicators)
- Short-term vs long-term trend reconciliation
- Precise entry/exit points with risk/reward ratios
- **OUTPUT**: `DeepTechnicalStrategyInsights`

**4. Deep Contextual Risk**

- Stress testing scenarios (recession, market crash, sector downturn)
- Black swan event analysis (tail risk assessment)
- Contingency planning (risk mitigation strategies)
- Portfolio correlation considerations
- **OUTPUT**: `DeepContextualRiskInsights`

**5. Deep Investment Decision**

- Comprehensive KEEP vs SELL analysis with detailed rationale
- Context: Portfolio fit, diversification, risk profile
- Alternative suggestions for SELL decisions (2-3 alternatives)
- Rebalancing recommendations (position sizing adjustments)
- Monitoring checklist (what to watch)
- **OUTPUT**: `DeepInvestmentDecision`

#### Portfolio-Specific Enhancements

- **Portfolio Fit Analysis**: How holding fits in overall portfolio
- **Correlation Considerations**: Diversification impact
- **Rebalancing Guidance**: Specific position sizing adjustments
- **Alternative Suggestions**: Must provide for SELL decisions
- **Monitoring Checklist**: What to watch going forward

#### Success Criteria

- [ ] All 5 tasks focus on qualitative portfolio-specific analysis
- [ ] KEEP/SELL decisions richly justified with context
- [ ] Alternatives provided for SELL recommendations
- [ ] Portfolio correlation and fit considered
- [ ] Rebalancing recommendations specific and actionable
- [ ] Tests verify portfolio-specific context used
- [ ] Deep analysis outputs substantially richer than stock crew

#### Files to Modify

- `src/finwiz/crews/deep_analysis/config/tasks.yaml`
- `src/finwiz/crews/deep_analysis/config/agents.yaml`
- `src/finwiz/crews/deep_analysis/deep_analysis.py`
- `tests/unit/crews/test_deep_analysis_crew.py`

---

### Phase 5: Enhanced Report Generation (Week 5)

**Task ID**: #5
**Priority**: HIGH
**Dependencies**: Task #4

#### Objective

Generate rich, actionable investment reports combining Python precision with AI insights.

**Target**: ≥2000 words (vs ~500 currently)

#### Report Structure

**1. Executive Summary Section** (AI-written synthesis)

- 2-3 paragraph overview
- Key findings and recommendation
- Risk/reward summary

**2. Quantitative Metrics Section** (Python tables)

- Composite score, grade, preliminary recommendation
- Fundamental metrics table (ROE, debt/equity, growth, margins)
- Technical indicators table (RSI, MACD, trend, momentum)
- Risk metrics table (volatility, beta, drawdown, Sharpe ratio)
- Data quality badges and calculation lineage

**3. Qualitative Analysis Section** (AI narrative)

- SEC Insights subsection (business model, competitive advantages)
- Competitive Positioning subsection
- Growth Drivers & Catalysts subsection
- Risk Scenarios subsection (regulatory, geopolitical, competitive)

**4. Investment Strategy Section** (AI guidance)

- Investment thesis (2-3 paragraphs)
- Bull/Base/Bear scenarios with price targets and probabilities
- Entry strategy (price points, timing)
- Exit strategy (take profit, stop loss)
- Position sizing recommendations

**5. Action Plan Section** (AI step-by-step)

- Immediate actions checklist
- Monitoring checklist (what to watch)
- Exit criteria (when to sell)
- Review schedule

**6. Alternatives Section** (AI suggestions, if applicable)

- Alternative holdings for SELL decisions
- Rationale for each alternative

#### Technical Implementation

**Report Generator Class**:

- File: `src/finwiz/reporting/enriched_report_generator.py`
- Method: `generate_enriched_report(enriched_analysis: EnrichedAnalysis, output_path: str) -> str`
- Support both stock analysis and deep analysis report types
- Use Jinja2 templates (AI Minimalism principle: NO AI for HTML)
- Include version metadata and timestamps
- Add data quality indicators
- Responsive HTML with good typography

**Template Assets**:

- CSS styling for professional appearance
- Responsive layout (mobile-friendly)
- Print-friendly styles
- Color coding for grades (A+=green, F=red)
- Icons for sections and risk levels

#### Success Criteria

- [ ] Reports are ≥2000 words (vs ~500 currently)
- [ ] Executive summary captures essence in 2-3 paragraphs
- [ ] Quantitative tables are clear and well-formatted
- [ ] Qualitative narrative is cohesive and insightful
- [ ] Action plans are specific and actionable
- [ ] HTML is valid and well-structured
- [ ] Reports render well on desktop and mobile
- [ ] All data from EnrichedAnalysis schema utilized
- [ ] Tests verify correct data mapping to template

#### Files to Create/Modify

- `src/finwiz/reporting/enriched_report_generator.py`
- `src/finwiz/templates/enriched_analysis_report.html`
- `src/finwiz/templates/enriched_analysis_report.css`
- `tests/unit/reporting/test_enriched_report_generator.py`

---

### Phase 6: Comprehensive Testing & Validation (Week 6)

**Task ID**: #6
**Priority**: CRITICAL
**Dependencies**: Task #5

#### Objective

Validate that hybrid architecture achieves all success criteria without regressions.

#### Testing Strategy

**1. Unit Tests** (Fast, Isolated)

- Test all new Pydantic schemas
  - Serialization/deserialization
  - Field validation rules
  - Edge cases and error handling
- Test orchestrator methods in isolation
  - `_process_single_holding()` returns QuantitativeAnalysis
  - `_enrich_with_qualitative_analysis()` handles crew failures
  - `_synthesize_enriched_analysis()` merges correctly
- Test report generator with mock data
  - Template rendering
  - Data mapping accuracy
  - HTML structure validation
- **Coverage target**: ≥65% (configured in pyproject.toml)

**2. Integration Tests** (Real Data)

- End-to-end workflow tests
  - Data collection → Quant analysis → Qual enrichment → Report
  - Test with real API data (1-2 sample tickers: AAPL, TSLA)
  - Validate schema serialization through full pipeline
- Batch processing with new workflow
  - Test with small portfolio (3-5 holdings)
  - Verify parallel processing still works
  - Check session_id and file organization
- Crew integration tests
  - Stock crew produces QualitativeInsights
  - Deep analysis crew produces DeepInvestmentDecision
  - Crews receive Python context correctly

**3. Quality Validation** (Manual Review)

**Report Comparison Study**:

- Generate reports for same holdings using old vs new system
- Compare side-by-side for 3-5 sample tickers
- Document quality improvements

**Quality Metrics Checklist**:

- [ ] Word count: Target ≥2000 words (baseline: ~500)
- [ ] Insights count: ≥5 qualitative insights per report
- [ ] Executive summary present and substantive
- [ ] Bull/base/bear scenarios with price targets
- [ ] Entry/exit strategy with specific prices
- [ ] Action plan with monitoring checklist
- [ ] Alternatives provided for SELL decisions
- [ ] Risk scenarios (regulatory, geopolitical, competitive)

**Manual Review**:

- 3-5 sample reports reviewed by stakeholders
- Feedback form for actionability, clarity, insights
- Iterate on task descriptions if quality insufficient

**4. Performance Validation** (Benchmarks)

**Timing Benchmarks**:

- Single holding: ≤30s execution time
- 66-holding portfolio: <40 minutes
- Batch processing speedup maintained (10-20x vs sequential)

**Cost Monitoring**:

- LLM token usage per holding
- Target: ≤$0.10 per holding
- Track by crew (stock, deep analysis)
- Monitor for cost creep

**Consistency Validation**:

- Python calculations remain deterministic
- Same input → same quantitative output (always)
- Run same ticker multiple times, verify consistency

**5. Regression Testing** (No Breaking Changes)

- Ensure existing functionality not broken
  - Portfolio review workflow still works
  - Rebalancing crew not affected
  - Investment discovery crew not affected
- Verify backward compatibility where needed
  - Old report generation still works (if maintained)
  - Existing API contracts preserved
- Validate ALL existing tests still pass
  - Run full test suite: `make test-all`
  - No new test failures introduced
  - Fix any broken tests from refactoring

#### Success Criteria - Gate for Merge

**ALL Must Pass**:

- [ ] Unit test coverage ≥65%
- [ ] All integration tests passing
- [ ] Quality metrics met:
  - [ ] Reports ≥2000 words
  - [ ] 5+ qualitative insights per report
  - [ ] Bull/base/bear scenarios present
  - [ ] Entry/exit strategy specific and actionable
  - [ ] Alternatives provided for SELL
- [ ] Performance metrics met:
  - [ ] ≤30s per holding
  - [ ] ≤$0.10 LLM cost per holding
  - [ ] Python calculations still deterministic
- [ ] No regressions:
  - [ ] All existing tests pass
  - [ ] No breaking changes to public APIs
  - [ ] Backward compatibility maintained
- [ ] Stakeholder approval on sample reports (3-5 reports)

#### Files to Create/Modify

- `tests/unit/schemas/test_enriched_analysis.py`
- `tests/unit/orchestrators/test_deep_analysis_orchestrator.py`
- `tests/unit/reporting/test_enriched_report_generator.py`
- `tests/integration/test_enriched_workflow.py`
- `tests/integration/test_quality_validation.py`
- `tests/performance/test_timing_benchmarks.py`
- `docs/testing/hybrid-architecture-validation-report.md`

---

## 🚧 Risk Management

### Critical Risks & Mitigation Strategies

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **AI agents still recalculate despite instructions** | HIGH | MEDIUM | Explicit task descriptions with "Do NOT recalculate", remove calculation tools, add validation tests |
| **Performance degradation** | HIGH | LOW | Benchmark each phase, maintain Python calculation speed, monitor execution times |
| **Report quality still insufficient** | MEDIUM | MEDIUM | POC with sample reports, iterate on task descriptions, stakeholder feedback loop |
| **Cost explosion** | MEDIUM | LOW | Set max_tokens limits, use cost-effective models for synthesis, monitor token usage |
| **Schema complexity** | LOW | MEDIUM | Start simple, iterate based on feedback, comprehensive documentation |
| **Integration complexity** | MEDIUM | MEDIUM | Incremental integration, comprehensive tests, fallback mechanisms |

---

## 📊 Success Metrics Dashboard

### Performance Metrics (Maintain)

| Metric | Baseline | Target | Monitoring |
|--------|----------|--------|------------|
| Execution time per holding | ✅ ~10-15s | ≤30s | Continuous benchmarking |
| Batch processing speedup | ✅ 10-20x | Maintain | Integration tests |
| Python calculation time | ✅ 1-2s | No change | Unit tests |

### Cost Metrics (Maintain)

| Metric | Baseline | Target | Monitoring |
|--------|----------|--------|------------|
| LLM cost per holding | ✅ $0.05-0.10 | ≤$0.10 | Token usage tracking |
| Calculation cost | ✅ $0 | $0 | No LLM in Python |

### Quality Metrics (Restore)

| Metric | Baseline | Target | Validation |
|--------|----------|--------|------------|
| Report word count | ~500 words | ≥2000 words | Automated counting |
| Qualitative insights | 0-1 | ≥5 | Manual review |
| Bull/base/bear scenarios | Missing | Present | Checklist |
| Entry/exit strategy | Missing | Detailed | Manual review |
| Alternatives for SELL | Missing | 2-3 | Automated check |

---

## 🎯 Next Steps

### Immediate Actions (This Week)

1. **Stakeholder Validation**
   - [ ] Review PRD with product owner
   - [ ] Review implementation plan with tech lead
   - [ ] Get approval to proceed

2. **Task Expansion**

   ```bash
   # Analyze complexity of all tasks
   task-master analyze-complexity --research

   # Expand high-complexity tasks into subtasks
   task-master expand --all --research
   ```

3. **POC Planning**
   - [ ] Select POC ticker (recommendation: AAPL)
   - [ ] Define POC success criteria
   - [ ] Schedule POC development (2-3 days)

### Week 1 Kickoff (Phase 1)

1. **Environment Setup**
   - [ ] Create feature branch: `feature/python-ai-hybrid-architecture`
   - [ ] Review Pydantic v2 documentation
   - [ ] Set up schema test infrastructure

2. **Begin Schema Development**

   ```bash
   task-master next                          # Get Task #1
   task-master set-status --id=1 --status=in-progress
   ```

3. **Daily Standups**
   - Progress updates
   - Blocker resolution
   - Scope adjustments if needed

---

## 📚 Reference Documentation

### Related Documents

1. **PRD**: [.taskmaster/docs/python-ai-hybrid-architecture-prd.md](.taskmaster/docs/python-ai-hybrid-architecture-prd.md)
2. **Architecture Analysis**: [docs/architecture/python-ai-analysis-architecture.md](docs/architecture/python-ai-analysis-architecture.md)
3. **CLAUDE.md**: Project-wide development guidelines
4. **CrewAI Standards**: [.kiro/steering/crewai-standards.md](../.kiro/steering/crewai-standards.md)

### Task Master Commands

```bash
# View all tasks
task-master list

# Get next available task
task-master next

# View specific task
task-master show <id>

# Update task status
task-master set-status --id=<id> --status=<status>

# Add implementation notes
task-master update-subtask --id=<id> --prompt="notes..."

# Generate task files
task-master generate
```

### Key Technical References

- **Pydantic v2**: https://docs.pydantic.dev/latest/
- **CrewAI Flow**: https://docs.crewai.com/concepts/flows
- **Jinja2 Templates**: https://jinja.palletsprojects.com/
- **pytest-mock**: https://pytest-mock.readthedocs.io/

---

## 📈 Project Tracking

### Task Master Integration

**Project Root**: `/Users/fjacquet/Projects/kiro/finwiz`

**Tasks Created**:

- Task #1: Phase 1 - Schema Foundation
- Task #2: Phase 2 - Orchestrator Refactoring
- Task #3: Phase 3 - Stock Crew Refactoring
- Task #4: Phase 4 - Deep Analysis Crew Refactoring
- Task #5: Phase 5 - Enhanced Report Generation
- Task #6: Phase 6 - Comprehensive Testing & Validation

**Total Tasks**: 6 main tasks (to be expanded into subtasks)

**Current Status**: All tasks pending, ready for complexity analysis and expansion

---

## ✅ Approval Checklist

Before proceeding with implementation:

- [ ] PRD reviewed and approved by product owner
- [ ] Implementation plan reviewed by tech lead
- [ ] Timeline approved by project manager
- [ ] Resources allocated for 6-week timeline
- [ ] Stakeholders aligned on success criteria
- [ ] Risk mitigation strategies approved
- [ ] POC scope defined and scheduled

---

**Document Version**: 1.0
**Last Updated**: 2025-11-21
**Next Review**: After POC completion
**Project Analyst**: @project-analyst (Claude 007 Agent)

---

*This implementation plan provides a comprehensive roadmap for restoring analytical depth to FinWiz while maintaining performance gains. The hybrid architecture represents the optimal balance between Python's deterministic precision and AI's contextual intelligence.*
