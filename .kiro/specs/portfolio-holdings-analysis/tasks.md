# Implementation Plan

- [x] 1. Portfolio analysis and rebalancing

- [x] 1.1 Core analysis tools and schema enhancements
  - Create HoldingAnalyzerOrchestrator with crew integration
    (stock/ETF/crypto)
  - Implement crew output caching (7-day TTL) and fallback logic
  - Map crew outputs to portfolio schema (fundamental, technical, SEC data)
  - Enhance PortfolioReview schema with PriceTargets and
    PositionSizeRecommendation models
  - Add data_freshness indicators and crew_analysis_used tracking
  - _Requirements: 1.1-1.6, 8.1-8.6_

- [x] 1.2 Price target calculation and recommendations
  - Implement PriceTargetCalculator tool with fair value calculations
  - Add buy/sell/stop-loss target logic for KEEP/SELL/BUY recommendations
  - Calculate technical support/resistance levels from price history
  - Implement multi-currency support with FX risk notes
  - Add data source citations and confidence scoring
  - _Requirements: 2.1-2.5, 6.1-6.4, 7.1-7.3_

- [x] 1.3 Alternative finder and A+ integration ✅ COMPLETED
  - ✅ Implement AlternativeFinder tool with sector/exposure matching
  - ✅ Integrate with discovery crew A+ outputs
  - ✅ Generate 2-3 alternatives for holdings graded below B
  - ✅ Add transition strategies (immediate/gradual/tax-optimized)
  - ✅ Calculate expected grade improvements and benefits
  - ✅ Enhance Alternative schema with swap timing and tax implications
  - ✅ 22 tests passing, 95%+ coverage
  - _Requirements: 3.1-3.5, 4.1-4.4_
  - _See: TASK_1.3_IMPLEMENTATION_SUMMARY.md_

- [x] 1.4 Position sizing and risk management
  - Implement PositionSizingTool with risk-based calculations
  - Add correlation analysis with existing portfolio holdings
  - Apply concentration limits (single stock 10%, sector 35%)
  - Generate sizing actions (add/trim/hold/exit) with rationale
  - Ensure portfolio allocations sum to 100%
  - _Requirements: 5.1-5.6_

- [x] 1.5 Enhanced PortfolioRebalancingCrew integration
  - Add holding_analyzer, price_target_specialist, alternative_researcher
    agents to agents.yaml
  - Create analyze_holding_task, calculate_price_targets_task,
    find_alternatives_task in tasks.yaml
  - Update portfolio_analyst to use HoldingAnalyzerOrchestrator
  - Update rebalancing_strategist to use PriceTargetCalculator and
    AlternativeFinder
  - Update risk_manager to use PositionSizingTool
  - Add parallel holding analysis with asyncio
  - _Requirements: 1.1, 2.1, 3.1, 5.1, 8.1_

- [x] 1.6 French HTML report generation
  - Create French HTML report template with portfolio dashboard
  - Add holdings table with price targets, alternatives, and position sizing
  - Implement responsive CSS with color-coded grades and emojis
    (� A📈 📉 💰)
  - Add A+ improvement roadmap section with phased plan
  - Integrate report generation into crew
    (output: portfolio_review_fr.html)
  - Ensure print-friendly layout
  - Use BeautifulSoup4 for HTML generation and validation
  - _Requirements: 9.1-9.6_

- [x] 1.7 Performance optimization and caching
  - Implement crew output caching (7-day TTL for analysis, 1-hour for
    prices)
  - Add parallel processing for holdings (chunks of 10)
  - Implement rate limiting (20 RPM) and exponential backoff
  - Add connection pooling for API calls
  - _Requirements: 8.1, 8.2_

- [x] 2. Testing and validation

- [x] 2.1 Write unit tests for all tools
  - Write unit tests for HoldingAnalyzerOrchestrator
  - Write unit tests for PriceTargetCalculator
  - Write unit tests for AlternativeFinder (already completed)
  - Write unit tests for PositionSizingTool
  - Write unit tests for PortfolioHoldingsHTMLGenerator
  - Mock all external dependencies using pytest-mock
  - Achieve 80%+ code coverage
  - _Requirements: All_

- [x] 2.3 Test with sample portfolio CSV and verify outputs
  - Create test portfolio with 5-10 holdings
  - Run full analysis and verify JSON output structure
  - Verify HTML report is well-formed and valid
  - Verify French language content
  - Verify all requirements are met
  - _Requirements: All_

- [ ] 3. Documentation and deployment

- [ ] 3.1 Write user documentation
  - Write user guide for interpreting price targets and alternatives
  - Document A+ improvement implementation strategy
  - Create position sizing recommendations guide
  - Document how to navigate the HTML report
  - _Requirements: All_

- [ ] 3.2 Create example outputs
  - Generate sample portfolio_review.json with complete data
  - Generate sample portfolio_review_fr.html with rendered report
  - Create screenshots of key report sections
  - Document expected output structure
  - _Requirements: All_

- [ ] 3.3 Test with full portfolio and monitor performance
  - Test with full 65-holding portfolio
  - Monitor performance (< 15 min target for medium portfolio)
  - Monitor error rates and cache hit rates
  - Verify all holdings analyzed successfully
  - Document any issues or limitations
  - _Requirements: All_
