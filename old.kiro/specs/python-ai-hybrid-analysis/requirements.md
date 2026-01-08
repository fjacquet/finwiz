# Requirements Document: Python/AI Hybrid Analysis Architecture

## Introduction

This specification addresses a critical regression in FinWiz's analysis quality following the AI Minimalism refactoring. While the refactoring successfully moved deterministic calculations to Python (achieving 10-20x performance improvement and 100% cost reduction for calculations), it inadvertently eliminated the valuable contextual analysis that AI agents provided.

The goal is to restore analytical richness by implementing a hybrid architecture where:

- **Python** performs all deterministic calculations (scores, grades, recommendations)
- **AI agents** provide contextual analysis, qualitative insights, and strategic guidance
- **Both** work together to produce comprehensive, actionable investment reports

## Glossary

- **QuantitativeAnalysis**: Python-calculated metrics (ROE, RSI, volatility, scores, grades)
- **QualitativeInsights**: AI-generated contextual analysis (competitive positioning, catalysts, scenarios)
- **EnrichedAnalysis**: Combined output merging quantitative calculations with qualitative insights
- **DeepAnalysisScorer**: Python class that calculates composite scores and grades
- **Stock Crew**: CrewAI crew with agents for SEC analysis, fundamental context, technical strategy, risk assessment
- **Deep Analysis Crew**: CrewAI crew for analyzing portfolio holdings with KEEP/SELL decisions
- **Hybrid Orchestrator**: Flow orchestrator that coordinates Python calculations and AI analysis
- **Data Source Waterfall**: Sequential fallback strategy trying multiple data providers (yfinance → Alpha Vantage → Intrinio → Tiingo/EOD)
- **Critical Fields**: Required fundamental metrics (ROE, debt_to_equity, revenue_growth) that must be present for analysis
- **Alpha Vantage**: Free API providing 500 calls/day for fundamentals, earnings, balance sheets across 60+ exchanges
- **Intrinio**: Free SDK for SEC filings, financial statements, and insider trades
- **Tiingo**: 99.9% uptime data provider with better international stock coverage (free for 500 symbols)
- **EODHistoricalData**: Global coverage provider with 70K+ tickers including emerging markets (free for 20 symbols)

## Requirements

### Requirement 1: Separate Quantitative and Qualitative Analysis

**User Story:** As a developer, I want clear separation between Python calculations and AI analysis, so that each component focuses on its strengths without duplication.

#### Acceptance Criteria

1. WHEN Python calculates quantitative metrics THEN the system SHALL store results in a QuantitativeAnalysis Pydantic model
2. WHEN AI agents receive quantitative results THEN the system SHALL pass them as read-only context (not for recalculation)
3. WHEN AI agents perform analysis THEN the system SHALL focus exclusively on qualitative insights (no metric recalculation)
4. WHEN combining results THEN the system SHALL merge quantitative and qualitative data into an EnrichedAnalysis model
5. THE system SHALL prevent AI agents from recalculating ROE, RSI, volatility, scores, or grades

### Requirement 2: Restore Contextual Analysis Capabilities

**User Story:** As an investor, I want rich contextual analysis beyond raw numbers, so that I understand the "why" behind investment recommendations.

#### Acceptance Criteria

1. WHEN analyzing SEC filings THEN the system SHALL extract business model insights, competitive advantages, and risk factors
2. WHEN assessing fundamentals THEN the system SHALL provide industry context, growth drivers, and competitive positioning
3. WHEN interpreting technical indicators THEN the system SHALL identify chart patterns, support/resistance levels, and entry/exit strategies
4. WHEN evaluating risks THEN the system SHALL analyze regulatory, geopolitical, competitive, and operational risks
5. WHEN synthesizing analysis THEN the system SHALL create bull/base/bear scenarios with catalysts and probabilities

### Requirement 3: Maintain Performance and Cost Efficiency

**User Story:** As a system administrator, I want to preserve the performance gains from AI Minimalism, so that analysis remains fast and cost-effective.

#### Acceptance Criteria

1. WHEN performing quantitative analysis THEN the system SHALL complete calculations in ≤5 seconds per holding
2. WHEN using AI agents THEN the system SHALL limit LLM costs to ≤$0.10 per holding
3. WHEN calculating metrics THEN the system SHALL maintain 100% deterministic consistency
4. WHEN running full analysis THEN the system SHALL complete in ≤30 seconds per holding
5. THE system SHALL NOT make redundant API calls for data already calculated by Python

### Requirement 4: Implement Structured State Management

**User Story:** As a developer, I want type-safe state management in CrewAI Flows, so that data flow is predictable and maintainable.

#### Acceptance Criteria

1. WHEN defining Flow state THEN the system SHALL use Pydantic BaseModel for type safety
2. WHEN passing data between Flow methods THEN the system SHALL return dict[str, Any] for downstream listeners
3. WHEN AI agents access quantitative results THEN the system SHALL provide them via Flow state (not self.inputs)
4. WHEN storing analysis results THEN the system SHALL use structured Pydantic models (not unstructured dicts)
5. THE system SHALL validate all state updates using Pydantic validation

### Requirement 5: Generate Actionable Investment Reports

**User Story:** As an investor, I want comprehensive reports with actionable guidance, so that I can make informed investment decisions.

#### Acceptance Criteria

1. WHEN generating reports THEN the system SHALL include executive summary (AI-written narrative)
2. WHEN presenting metrics THEN the system SHALL display quantitative data in structured tables
3. WHEN providing recommendations THEN the system SHALL include entry/exit strategy with price targets
4. WHEN assessing scenarios THEN the system SHALL present bull/base/bear cases with probabilities
5. WHEN recommendation is SELL THEN the system SHALL suggest 2-3 alternative holdings with rationale

### Requirement 6: Refactor Stock Crew Tasks

**User Story:** As a developer, I want Stock Crew tasks focused on qualitative analysis, so that AI agents add unique value without duplicating Python calculations.

#### Acceptance Criteria

1. WHEN SEC analyst runs THEN the task SHALL analyze filings for business model insights (not recalculate metrics)
2. WHEN fundamental analyst runs THEN the task SHALL provide industry context and growth drivers (not recalculate ROE)
3. WHEN technical analyst runs THEN the task SHALL interpret chart patterns and entry points (not recalculate RSI)
4. WHEN risk assessor runs THEN the task SHALL analyze contextual risks (not recalculate volatility)
5. WHEN investment strategist runs THEN the task SHALL synthesize all analyses into cohesive thesis

### Requirement 7: Refactor Deep Analysis Crew

**User Story:** As a portfolio manager, I want deep analysis of holdings with rich justification for KEEP/SELL decisions, so that I understand portfolio optimization recommendations.

#### Acceptance Criteria

1. WHEN analyzing portfolio holdings THEN the system SHALL apply the same hybrid pattern as Stock Crew
2. WHEN making KEEP/SELL decisions THEN the system SHALL provide detailed qualitative justification
3. WHEN recommending SELL THEN the system SHALL suggest alternative holdings with comparative analysis
4. WHEN assessing holdings THEN the system SHALL consider portfolio context (diversification, correlation)
5. THE system SHALL generate reports ≥2000 words (vs ~500 words currently)

### Requirement 8: Implement New Pydantic Schemas

**User Story:** As a developer, I want well-defined schemas for hybrid analysis, so that data contracts are clear and validated.

#### Acceptance Criteria

1. WHEN defining QuantitativeAnalysis THEN the schema SHALL include scores, grade, metrics, and data lineage
2. WHEN defining QualitativeInsights THEN the schema SHALL include SEC insights, competitive analysis, scenarios, and action plan
3. WHEN defining EnrichedAnalysis THEN the schema SHALL combine quantitative and qualitative with final synthesis
4. WHEN validating schemas THEN the system SHALL use Pydantic v2 with strict mode
5. THE system SHALL include sub-schemas for SecAnalysisInsights, FundamentalContextInsights, TechnicalStrategyInsights, ContextualRiskInsights, InvestmentSynthesis

### Requirement 9: Update Deep Analysis Orchestrator

**User Story:** As a developer, I want the orchestrator to coordinate Python calculations and AI analysis, so that the hybrid workflow executes correctly.

#### Acceptance Criteria

1. WHEN processing holdings THEN the orchestrator SHALL first run Python calculations (QuantitativeAnalysis)
2. WHEN Python completes THEN the orchestrator SHALL pass results as INPUT to AI crew (not as final output)
3. WHEN AI crew completes THEN the orchestrator SHALL merge quantitative and qualitative into EnrichedAnalysis
4. WHEN storing results THEN the orchestrator SHALL maintain both Python and AI outputs separately
5. THE orchestrator SHALL handle errors gracefully with fallback to Python-only analysis

### Requirement 10: Validate Quality Restoration

**User Story:** As a product owner, I want to verify that analytical quality is restored, so that reports meet investor expectations.

#### Acceptance Criteria

1. WHEN comparing reports THEN the system SHALL generate ≥2000 words (vs ~500 currently)
2. WHEN reviewing insights THEN reports SHALL include ≥5 unique qualitative insights
3. WHEN assessing scenarios THEN reports SHALL present bull/base/bear cases with catalysts
4. WHEN providing guidance THEN reports SHALL include entry/exit strategy with price targets
5. WHEN recommending SELL THEN reports SHALL suggest alternatives with comparative rationale

### Requirement 11: Multi-Source Data Acquisition with Fallbacks

**User Story:** As a system, I want multiple data source fallbacks, so that analysis can proceed even when primary sources fail to provide critical fields.

#### Acceptance Criteria

1. WHEN yfinance fails to provide ROE or debt_to_equity THEN the system SHALL attempt Alpha Vantage fundamentals API
2. WHEN Alpha Vantage fails THEN the system SHALL attempt Intrinio SEC filings API
3. WHEN ticker is international (non-US exchange) THEN the system SHALL try Tiingo or EODHistoricalData
4. WHEN all data sources fail for critical fields THEN the system SHALL use industry averages with confidence penalty and warning
5. THE system SHALL log which data source provided each field for data lineage tracking
6. THE system SHALL complete data acquisition in ≤10 seconds per ticker across all fallback attempts
7. WHEN data source provides invalid values (negative ROE, extreme outliers) THEN the system SHALL reject and try next source

### Requirement 12: AI Output Format Enforcement

**User Story:** As a developer, I want AI crews to return structured, parseable output, so that grade/score extraction never fails.

#### Acceptance Criteria

1. WHEN AI crew executes THEN the task SHALL use `output_pydantic` with strict schema validation
2. WHEN AI crew completes THEN the output SHALL include grade, composite_score, fundamental_score, technical_score, and risk_score
3. WHEN AI output fails Pydantic validation THEN the system SHALL retry with explicit format instructions in task description
4. WHEN retries fail after 2 attempts THEN the system SHALL fall back to Python-only analysis with warning logged
5. THE system SHALL validate AI output structure before attempting field extraction
6. WHEN AI returns tool calls instead of analysis THEN the system SHALL detect and retry with corrected prompt
7. THE system SHALL include output format examples in task descriptions to guide AI agents

---

**Version**: 1.1  
**Created**: 2025-11-21  
**Updated**: 2025-11-22  
**Status**: Updated - Includes Data Quality Requirements
