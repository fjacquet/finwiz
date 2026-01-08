# Requirements Document

## Introduction

The FinWiz platform currently generates generic portfolio reviews with placeholder
analysis for user holdings stored in `data/etf.csv` and `data/stock.csv`. The
current output in `output/portfolio/portfolio_review.json` contains only:

- Generic baseline scores (0.65 for ETFs, 0.6 for stocks)
- Placeholder risk factors ("Baseline placeholder")
- Generic rationale ("Ticker validated on Yahoo; baseline confidence")
- No specific buy/sell price targets
- No alternatives or improvement suggestions

Users need detailed, actionable analysis for each of their specific holdings
including:

- Deep fundamental analysis (for stocks and ETFs)
- Specific keep/sell/buy recommendations with price targets
- Alternative investment suggestions
- A+ grade improvement opportunities
- Risk-adjusted position sizing recommendations

This feature will enhance the portfolio review crew to provide comprehensive,
ticker-specific analysis that goes beyond validation to deliver actionable
investment intelligence for a portfolio of 28 ETFs and 37 stocks across multiple
exchanges (US, European, Swiss).

## Requirements

### Requirement 1: Individual Holding Deep Analysis

**User Story:** As an investor, I want detailed analysis of each holding in my
portfolio, so that I can make informed decisions about whether to keep, sell, or
add to each position.

#### Acceptance Criteria

1. WHEN a portfolio review is requested THEN the system SHALL analyze each
   validated ticker individually using the appropriate crew (stock/ETF/crypto)
2. WHEN analyzing a stock holding THEN the system SHALL retrieve and include
   SEC filing data, fundamental metrics, and competitive positioning
3. WHEN analyzing an ETF holding THEN the system SHALL include expense ratio
   analysis, tracking error, holdings composition, and benchmark comparison
4. WHEN analyzing a crypto holding THEN the system SHALL include technical
   analysis, volatility metrics, and market structure assessment
5. IF a holding has been analyzed by a crew THEN the system SHALL incorporate
   that crew's detailed output into the portfolio review
6. WHEN analysis is complete THEN the system SHALL replace generic "baseline"
   data with specific, ticker-relevant analysis

### Requirement 2: Actionable Buy/Sell Recommendations with Price Targets

**User Story:** As an investor, I want specific price targets for buying more or
selling my holdings, so that I can execute trades at optimal levels.

#### Acceptance Criteria

1. WHEN a holding receives a KEEP recommendation THEN the system SHALL provide:
   - Current price and fair value estimate
   - Buy-more price target (accumulation level)
   - Stop-loss or sell price target (risk management level)
   - Rationale for each price level
2. WHEN a holding receives a SELL recommendation THEN the system SHALL provide:
   - Target exit price range
   - Timeline for exit (immediate vs gradual)
   - Tax considerations if applicable
   - Specific reasons for the sell recommendation
3. WHEN a holding receives a BUY recommendation THEN the system SHALL provide:
   - Initial entry price target
   - Scale-in levels for dollar-cost averaging
   - Position sizing recommendation as % of portfolio
   - Risk/reward ratio at current levels
4. IF technical analysis is available THEN the system SHALL include
   support/resistance levels in price targets
5. WHEN price targets are provided THEN they SHALL be in the holding's native
   currency

### Requirement 3: Alternative Investment Suggestions

**User Story:** As an investor, I want to see better alternatives to my current
holdings, so that I can upgrade my portfolio quality over time.

#### Acceptance Criteria

1. WHEN a holding has a grade below B THEN the system SHALL suggest at least
   2-3 alternative investments
2. WHEN suggesting alternatives THEN the system SHALL match:
   - Similar asset class and risk profile
   - Similar or better expected returns
   - Lower fees (for ETFs)
   - Better fundamentals (for stocks)
   - Higher liquidity (for crypto)
3. WHEN alternatives are provided THEN each SHALL include:
   - Ticker symbol and name
   - Key advantage over current holding
   - Risk comparison
   - Transition strategy (swap timing and tax implications)
4. IF the current holding is in a tax-advantaged account THEN the system SHALL
   note tax-free swap opportunities
5. WHEN alternatives are A+ rated THEN they SHALL be clearly marked as premium
   opportunities

### Requirement 4: A+ Grade Improvement Path

**User Story:** As an investor, I want to understand how to improve my portfolio
to achieve more A+ rated holdings, so that I can systematically upgrade my
investment quality.

#### Acceptance Criteria

1. WHEN a portfolio contains holdings graded below A+ THEN the system SHALL
   provide an improvement roadmap
2. WHEN creating an improvement roadmap THEN the system SHALL:
   - Identify which holdings to exit first (prioritize D and F grades)
   - Suggest A+ replacements from the discovery crew output
   - Provide a phased transition plan (e.g., "Month 1-3: Exit X, Y; Month 4-6:
     Add A, B")
   - Calculate expected portfolio grade improvement
3. WHEN A+ opportunities exist THEN the system SHALL show:
   - Current portfolio A+ allocation percentage
   - Target A+ allocation percentage
   - Gap analysis and specific actions to close the gap
4. IF an A+ alternative exists for a current holding THEN it SHALL be
   highlighted in the holding's analysis
5. WHEN improvement suggestions are made THEN they SHALL respect the user's
   risk tolerance and investment constraints

### Requirement 5: Risk-Adjusted Position Sizing

**User Story:** As an investor, I want position sizing recommendations based on
each holding's risk profile, so that I can optimize my portfolio's risk/reward
balance.

#### Acceptance Criteria

1. WHEN analyzing each holding THEN the system SHALL calculate a recommended
   position size as % of total portfolio
2. WHEN calculating position size THEN the system SHALL consider:
   - Holding's risk score (0-10 scale)
   - Correlation with other portfolio holdings
   - User's overall risk tolerance
   - Concentration limits (e.g., max 10% in single stock)
3. WHEN current position size exceeds recommended size THEN the system SHALL
   flag it as "overweight" with trim recommendations
4. WHEN current position size is below recommended size THEN the system SHALL
   flag it as "underweight" with add recommendations
5. IF a holding is high-risk (score > 7) THEN the system SHALL recommend
   position size ≤ 3% of portfolio
6. WHEN position sizing recommendations are provided THEN they SHALL sum to
   100% across the entire portfolio

### Requirement 6: Data Freshness and Citation Requirements

**User Story:** As an investor, I want to know when the analysis data was last
updated and where it came from, so that I can trust the recommendations.

#### Acceptance Criteria

1. WHEN displaying analysis for any holding THEN the system SHALL include:
   - Data as-of date (timestamp)
   - Primary data sources with URLs
   - Freshness indicator (fresh < 7 days, stale > 30 days)
2. WHEN data is stale (> 30 days) THEN the system SHALL display a warning and
   reduce confidence scores by 20%
3. WHEN SEC filings are cited THEN the system SHALL include:
   - Filing type (10-K, 10-Q, 8-K)
   - Accession number
   - Filing date
   - Relevant excerpt or summary
4. WHEN market data is used THEN the system SHALL cite the specific API/source
   (Yahoo Finance, Alpha Vantage, etc.)
5. IF analysis cannot be completed due to missing data THEN the system SHALL
   clearly state what data is unavailable

### Requirement 7: Multi-Currency Support

**User Story:** As an international investor with holdings in multiple currencies,
I want analysis and price targets in each holding's native currency, so that I
can execute trades accurately.

#### Acceptance Criteria

1. WHEN a holding is denominated in a non-base currency THEN all price targets
   SHALL be in that currency
2. WHEN displaying portfolio-level metrics THEN they SHALL be converted to the
   user's base currency (CHF)
3. WHEN currency conversion is applied THEN the system SHALL:
   - Show the exchange rate used
   - Include the conversion timestamp
   - Note FX risk in the risk assessment
4. IF a holding trades on multiple exchanges THEN the system SHALL specify
   which exchange/listing is being analyzed
5. WHEN suggesting alternatives THEN the system SHALL prefer same-currency
   alternatives to minimize FX exposure

### Requirement 8: Integration with Existing Crews

**User Story:** As a system, I want to leverage existing crew analysis outputs,
so that portfolio reviews are comprehensive and avoid duplicate API calls.

#### Acceptance Criteria

1. WHEN a portfolio review is initiated THEN the system SHALL check if recent
   crew analysis exists for each ticker
2. IF crew analysis exists and is fresh (< 7 days) THEN the system SHALL reuse
   that analysis
3. IF crew analysis is missing or stale THEN the system SHALL trigger the
   appropriate crew (stock/ETF/crypto) to analyze the ticker
4. WHEN integrating crew outputs THEN the system SHALL map crew-specific fields
   to portfolio review schema:
   - Stock crew → fundamental_analysis, sec_citations, competitive_moat
   - ETF crew → expense_ratio, tracking_error, holdings_analysis
   - Crypto crew → technical_indicators, volatility_metrics, market_structure
5. WHEN all crew analyses are complete THEN the system SHALL consolidate them
   into a unified portfolio review output
6. IF a crew analysis fails THEN the system SHALL fall back to baseline
   analysis with a clear warning

### Requirement 9: French HTML Report Generation

**User Story:** As an investor, I want a professional French HTML report with
comprehensive portfolio analysis, so that I can review my holdings and make
informed decisions.

#### Acceptance Criteria

1. WHEN portfolio analysis is complete THEN the system SHALL generate a French
   HTML report at `output/portfolio/portfolio_review_fr.html`
2. WHEN generating HTML THEN the system SHALL use BeautifulSoup4 for proper
   HTML structure and validation
3. WHEN creating the report THEN it SHALL include:
   - Portfolio summary dashboard with grade distribution
   - Holdings analysis table (sortable/filterable)
   - Price targets section for each holding
   - Alternatives section for underperforming holdings
   - A+ improvement roadmap
   - Position sizing recommendations with visual charts
4. WHEN styling the report THEN it SHALL:
   - Use professional CSS with FinWiz branding
   - Be responsive and mobile-friendly
   - Include strategic emoji usage (📊 📈 📉 💰 ⚠️ ✅ ❌)
   - Use color-coded grades (green for A+/A, yellow for B/C, red for D/F)
   - Be print-friendly
5. WHEN displaying text THEN all content SHALL be in French with proper
   financial terminology
6. IF the report cannot be generated THEN the system SHALL log the error and
   fall back to JSON output only

## Success Criteria

- Portfolio reviews contain zero "baseline placeholder" entries for validated
  tickers
- Each holding has specific, actionable buy/sell price targets
- At least 80% of holdings below grade B have alternative suggestions
- Position sizing recommendations sum to 100% across portfolio
- All analysis includes data sources and freshness indicators
- User can execute trades directly from the recommendations without additional
  research
- French HTML report is generated successfully with professional formatting
- HTML is valid and well-formed (validated with BeautifulSoup4)
