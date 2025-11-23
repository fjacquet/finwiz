# PRD: Python-AI Hybrid Analysis Architecture

**Version**: 1.0
**Date**: 2025-11-21
**Status**: Planning
**Priority**: HIGH

---

## 📋 Executive Summary

Restore analytical depth to FinWiz platform by implementing hybrid architecture that combines Python's deterministic calculations with AI's contextual analysis. The current system successfully optimized performance (10-20x faster, 100% cost reduction for calculations) but lost analytical richness. This initiative aims to restore valuable qualitative insights while maintaining performance gains.

**Success Metrics**:

- Performance: ≤30s per holding analysis (maintain)
- Cost: ≤\$0.10 LLM cost per holding (maintain)
- Quality: Reports ≥2000 words with 5+ qualitative insights (restore)
- Actionability: Bull/base/bear scenarios + entry/exit strategy (restore)

---

## 🎯 Problem Statement

### Current State Issues

**What Works** ✅:

- Python calculations are fast, deterministic, and consistent
- DeepAnalysisScorer produces accurate quantitative metrics
- Performance improved 10-20x over pure AI approach
- Zero LLM cost for calculations

**What's Broken** ❌:

- AI agents receive pre-made decisions (no reasoning)
- Reports are superficial (formatting only, no insights)
- No contextual/qualitative analysis
- Missing: sector context, catalysts, peer comparison, risk scenarios
- No actionable recommendations (entry/exit strategy, position sizing)

### Root Cause

Python calculates everything → AI just formats the decision → Reports lack depth and actionability.

**Before (Full AI)**: Data → AI Analysis (calc + insights) → Rich Report
**Now (Python Only)**: Data → Python Calc → AI Formatting → Superficial Report
**Goal (Hybrid)**: Data → Python Calc → AI Contextual Analysis → Rich Actionable Report

---

## 🏗️ Proposed Architecture

### Core Principle

**"Python calculates, AI analyzes"**

### Workflow

1. **Data Collection** (Python, no change)

   - Fetch price, financial, technical data
   - Output: raw_data dict

2. **Quantitative Analysis** (Python, no change)

   - DeepAnalysisScorer calculates all metrics
   - Output: QuantitativeAnalysis (scores, grade, recommendation)

3. **Qualitative Analysis** (AI, NEW)

   - Agents receive Python results as READ-ONLY context
   - Focus: SEC insights, competitive positioning, growth drivers, risk scenarios
   - Output: QualitativeInsights (contextual analysis)

4. **Synthesis** (Hybrid, NEW)

   - Combine quantitative + qualitative
   - Python grade/score + AI confidence/strategy
   - Output: EnrichedAnalysis

5. **Rich Reports** (AI + Python templates)
   - Python tables for metrics
   - AI narrative for insights
   - Combined executive summary

---

## 📦 Deliverables

### Phase 1: Schema Foundation (Week 1)

**Pydantic Schemas** - `src/finwiz/schemas/enriched_analysis.py`

1. **QuantitativeAnalysis** (Python output)

   - composite_score, fundamental_score, technical_score, risk_score
   - grade (A+ to F), preliminary_recommendation (BUY/HOLD/SELL)
   - detailed metrics (ROE, RSI, volatility, etc.)
   - metadata (data_quality, lineage, confidence)

2. **QualitativeInsights** (AI output)

   - sec_insights (business model, competitive advantages, risk factors)
   - fundamental_context (competitive positioning, growth drivers, management quality)
   - technical_strategy (chart patterns, entry/exit points)
   - contextual_risks (regulatory, geopolitical, competitive)
   - investment_strategy (thesis, bull/base/bear cases, alternatives)

3. **EnrichedAnalysis** (Combined)

   - quantitative (Python), qualitative (AI)
   - final_grade/score/recommendation (Python baseline)
   - recommendation_confidence (AI assessment: LOW/MEDIUM/HIGH)
   - executive_summary, investment_rationale, action_plan (AI narratives)

4. **Supporting Schemas**
   - SecAnalysisInsights, FundamentalContextInsights, TechnicalStrategyInsights
   - ContextualRiskInsights, InvestmentSynthesis
   - GrowthDriver, ChartPattern, EntryExitStrategy, StressScenario, AlternativeHolding

**Acceptance Criteria**:

- [ ] All schemas defined with Pydantic v2
- [ ] Field validation rules implemented
- [ ] Unit tests for schema validation
- [ ] Documentation for each schema

### Phase 2: Orchestrator Refactoring (Week 2)

**Deep Analysis Orchestrator** - `src/finwiz/orchestrators/deep_analysis_orchestrator.py`

1. **Modify Quantitative Processing**

   - Update `_process_single_holding()` to return QuantitativeAnalysis
   - Preserve existing Python calculation logic
   - Add comprehensive metadata (lineage, data_quality)

2. **Add Qualitative Enrichment**

   - New method: `_enrich_with_qualitative_analysis(quant_analysis, ticker, asset_class)`
   - Prepare crew inputs with Python results as READ-ONLY context
   - Call appropriate crew (stock/etf/crypto) for qualitative analysis
   - Return QualitativeInsights

3. **Synthesis Logic**

   - New method: `_synthesize_enriched_analysis(quant, qual)`
   - Combine quantitative + qualitative
   - Merge into EnrichedAnalysis
   - Preserve Python grade/score, add AI confidence

4. **Workflow Integration**
   - Update batch processing to use new 3-step flow
   - Maintain performance optimizations (prefetch, parallel processing)
   - Update progress tracking and logging

**Acceptance Criteria**:

- [ ] Orchestrator produces EnrichedAnalysis objects
- [ ] Python calculations unchanged (deterministic)
- [ ] Qualitative analysis integrated without performance degradation
- [ ] Batch processing works with new workflow
- [ ] Tests updated and passing

### Phase 3: Stock Crew Task Refactoring (Week 3)

**Stock Crew Tasks** - `src/finwiz/crews/stock_crew/config/tasks.yaml`

Tasks must be rewritten to eliminate calculation duplication and focus on qualitative analysis.

1. **SEC Analysis Task** (Qualitative Only)

   - **INPUT**: Python metrics as context (ROE, debt/equity, grade)
   - **FOCUS**: Business model, competitive advantages, risk factors from filings, strategic initiatives
   - **PROHIBIT**: Recalculating financial metrics
   - **OUTPUT**: SecAnalysisInsights

2. **Fundamental Context Task** (Contextual Only)

   - **INPUT**: Python fundamental_score and metrics
   - **FOCUS**: Industry dynamics, growth drivers, competitive positioning, management quality
   - **PROHIBIT**: Recalculating ROE, margins, growth rates
   - **OUTPUT**: FundamentalContextInsights

3. **Technical Strategy Task** (Interpretation Only)

   - **INPUT**: Python technical_score and indicators (RSI, MACD, trend)
   - **FOCUS**: Chart patterns, support/resistance, entry/exit strategy, timing
   - **PROHIBIT**: Recalculating RSI, MACD
   - **OUTPUT**: TechnicalStrategyInsights

4. **Contextual Risk Task** (Contextual Risks Only)

   - **INPUT**: Python risk_score and metrics (volatility, beta, drawdown)
   - **FOCUS**: Regulatory, geopolitical, competitive, operational risks, stress scenarios
   - **PROHIBIT**: Recalculating volatility, beta
   - **OUTPUT**: ContextualRiskInsights

5. **Investment Synthesis Task** (Strategy & Narrative)
   - **INPUT**: All previous task outputs + Python grade/score/recommendation
   - **FOCUS**: Investment thesis, bull/base/bear scenarios, refined recommendation with confidence, action plan, alternatives
   - **ROLE**: Synthesize Python baseline with qualitative context
   - **OUTPUT**: InvestmentSynthesis

**Acceptance Criteria**:

- [ ] All 5 tasks rewritten to eliminate calculation duplication
- [ ] Task descriptions explicitly state what NOT to recalculate
- [ ] Focus areas clearly defined (qualitative only)
- [ ] Output schemas properly defined
- [ ] Task dependencies correctly configured
- [ ] Tool lists updated (remove redundant calculation tools)

### Phase 4: Deep Analysis Crew Refactoring (Week 4)

**Deep Analysis Crew** - `src/finwiz/crews/deep_analysis/`

Apply same pattern as stock_crew, focusing on portfolio-specific analysis:

1. **Deep SEC Analysis** (Qualitative)

   - Deep dive into 10-K/10-Q footnotes and MD&A
   - Red flags detection
   - Year-over-year trend analysis (qualitative)

2. **Deep Fundamental Context** (Qualitative)

   - Quality of business assessment
   - Sustainability of competitive advantages
   - Capital allocation effectiveness
   - Long-term growth sustainability

3. **Deep Technical Strategy** (Interpretation)

   - Multi-timeframe analysis interpretation
   - Institutional flow analysis (qualitative)
   - Short-term vs long-term trend reconciliation
   - Precise entry/exit points with risk/reward

4. **Deep Contextual Risk** (Qualitative)

   - Stress testing scenarios
   - Black swan event analysis
   - Contingency planning
   - Portfolio correlation considerations

5. **Deep Investment Decision** (KEEP/SELL with Rich Justification)
   - Comprehensive KEEP vs SELL analysis
   - Detailed rationale with context
   - Alternative suggestions for SELL decisions
   - Rebalancing recommendations
   - Position sizing adjustments

**Acceptance Criteria**:

- [ ] All deep analysis tasks refactored
- [ ] KEEP/SELL decisions richly justified
- [ ] Alternatives provided for SELL recommendations
- [ ] Portfolio-specific considerations included
- [ ] Tests updated and passing

### Phase 5: Report Generation Enhancement (Week 5)

**Enhanced Report Generation** - `src/finwiz/reporting/enriched_report_generator.py`

Create rich HTML reports combining quantitative and qualitative analysis:

1. **New Report Template**

   - Executive Summary (AI-written synthesis)
   - Quantitative Metrics Section (Python tables)
     - Scores, grades, metrics in structured tables
     - Data quality indicators
     - Calculation lineage
   - Qualitative Analysis Section (AI narrative)
     - SEC insights
     - Competitive positioning
     - Growth drivers and catalysts
     - Risk scenarios
   - Investment Strategy Section (AI guidance)
     - Investment thesis
     - Bull/base/bear scenarios
     - Entry/exit strategy
     - Position sizing recommendations
   - Action Plan Section (AI step-by-step)
     - Immediate actions
     - Monitoring checklist
     - Exit criteria
   - Alternatives Section (AI suggestions, if applicable)

2. **Report Generator Class**
   - Method: `generate_enriched_report(enriched_analysis: EnrichedAnalysis, output_path: str)`
   - Use Jinja2 templates (NO AI for HTML generation)
   - Support both stock and deep analysis report types
   - Include data quality badges
   - Add timestamp and version metadata

**Acceptance Criteria**:

- [ ] Jinja2 templates created for enriched reports
- [ ] Report generator supports EnrichedAnalysis schema
- [ ] Reports include both quantitative tables and qualitative narratives
- [ ] HTML is well-formatted and readable
- [ ] Reports are ≥2000 words with substantial insights
- [ ] Action plans are specific and actionable

### Phase 6: Testing & Validation (Week 6)

**Comprehensive Testing**

1. **Unit Tests**

   - Test all new Pydantic schemas
   - Test orchestrator methods in isolation
   - Test report generation with mock data
   - Coverage target: ≥65%

2. **Integration Tests**

   - End-to-end workflow tests (data → enriched report)
   - Test with real API data (1-2 sample tickers)
   - Validate schema serialization/deserialization
   - Test batch processing with new workflow

3. **Quality Validation**

   - **Report Comparison**: Compare old vs new reports for same holding
   - **Metrics**:
     - Word count: Target ≥2000 words (vs ~500 currently)
     - Insights count: ≥5 qualitative insights per report
     - Completeness: Bull/base/bear scenarios present
     - Actionability: Entry/exit strategy with specific prices/timing
     - Alternatives: Suggested for SELL decisions
   - **Manual Review**: 3-5 sample reports reviewed by stakeholders

4. **Performance Validation**

   - **Timing**: Execution time ≤30s per holding
   - **Cost**: LLM cost ≤\$0.10 per holding
   - **Consistency**: Python calculations remain deterministic
   - **Batch Performance**: 66-holding portfolio in <40 minutes

5. **Regression Testing**
   - Ensure existing functionality not broken
   - Verify backward compatibility where needed
   - Validate all existing tests still pass

**Acceptance Criteria**:

- [ ] Unit test coverage ≥65%
- [ ] All integration tests passing
- [ ] Quality metrics met (word count, insights, actionability)
- [ ] Performance metrics met (time, cost)
- [ ] No regressions in existing functionality
- [ ] Stakeholder approval on sample reports

---

## 🚧 Technical Constraints

1. **Performance**: Must maintain 10-20x speedup from Python calculations
2. **Cost**: LLM costs must remain controlled (≤\$0.10/holding)
3. **Determinism**: Python calculations must remain 100% consistent
4. **Backward Compatibility**: Existing workflows should continue working during migration
5. **Testing**: Minimum 65% code coverage, pytest-mock only (no unittest.mock)
6. **Type Safety**: All new code must have type hints (Python 3.12+)

---

## 📊 Success Criteria

### Must Have (P0)

- [ ] Python calculations unchanged and deterministic
- [ ] AI agents receive Python results as context (no recalculation)
- [ ] Reports contain qualitative insights (5+ per report)
- [ ] Execution time ≤30s per holding
- [ ] LLM cost ≤\$0.10 per holding
- [ ] All tests passing with ≥65% coverage

### Should Have (P1)

- [ ] Bull/base/bear scenarios in all reports
- [ ] Entry/exit strategy with specific prices
- [ ] Alternative holdings suggested for SELL decisions
- [ ] Risk scenarios (regulatory, geopolitical, competitive)
- [ ] Investment thesis narrative
- [ ] Action plan with monitoring checklist

### Nice to Have (P2)

- [ ] Portfolio correlation analysis
- [ ] Stress testing scenarios
- [ ] Historical comparison with previous analyses
- [ ] Interactive HTML reports with expandable sections

---

## 🎯 Out of Scope

- ETF crew refactoring (will follow stock crew pattern later)
- Crypto crew refactoring (will follow stock crew pattern later)
- Portfolio rebalancing crew changes
- Investment discovery crew changes
- UI/frontend changes
- Real-time data streaming
- New data sources integration

---

## 🔍 Key Risks

| Risk                                             | Impact | Probability | Mitigation                                                           |
| ------------------------------------------------ | ------ | ----------- | -------------------------------------------------------------------- |
| AI agents still recalculate despite instructions | HIGH   | MEDIUM      | Explicit task descriptions, remove calculation tools, add validation |
| Performance degradation                          | HIGH   | LOW         | Benchmark each phase, maintain Python calculation speed              |
| Report quality still insufficient                | MEDIUM | MEDIUM      | POC with sample reports, iterate on task descriptions                |
| Cost explosion                                   | MEDIUM | LOW         | Set max_tokens limits, use cost-effective models for synthesis       |
| Schema complexity                                | LOW    | MEDIUM      | Start simple, iterate based on feedback                              |

---

## 📅 Timeline

- **Week 1**: Schema foundation (Pydantic models)
- **Week 2**: Orchestrator refactoring
- **Week 3**: Stock crew task refactoring
- **Week 4**: Deep analysis crew refactoring
- **Week 5**: Report generation enhancement
- **Week 6**: Testing & validation

**Total Duration**: 6 weeks
**Target Start**: TBD
**Target Completion**: TBD

---

## 👥 Stakeholders

- **Development Team**: Implementation
- **QA Team**: Testing and validation
- **Product Owner**: Requirements validation and acceptance
- **End Users**: Report quality feedback

---

## ✅ Next Steps

1. Validate this PRD with stakeholders
2. Parse PRD with Task Master to generate tasks
3. Analyze complexity and expand tasks into subtasks
4. Create POC with single ticker (e.g., AAPL) to validate concept
5. Iterate based on POC feedback
6. Execute full migration plan

---

**Document Status**: Draft for validation
**Version**: 1.0
**Last Updated**: 2025-11-21
