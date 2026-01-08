# Schema to Crew Task Mapping

This document maps each crew's intermediate tasks to their corresponding Pydantic schemas for JSON output validation.

## Stock Crew

| Task | Output File | Schema | Description |
|------|-------------|--------|-------------|
| `market_technical_analysis_task` | `stock_market_trends.md` | `MarketTrend` | Market trend analysis with key trends and growth sectors |
| `stock_screening_task` | `emerging_stocks_analysis.md` | `StockScreeningResult` | Top 10 stock candidates with sentiment analysis |
| `technical_detail_task` | `stock_technical_details.md` | `StockTechnicalAnalysis` | Technical analysis with 10-K insights and quantitative metrics |
| `stock_risk_assessment_task` | `stock_investment_risk_strategy_en.html` | `StockRiskProfile` | Risk assessment with standardized scoring and mitigation strategies |

**Additional Schemas**:
- `StockCandidate` - Individual stock in screening results
- `TechnicalIndicators` - Technical indicators (RSI, MACD, etc.)
- `QuantitativeMetrics` - Quantitative analysis metrics
- `TenKInsight` - 10-K filing insights (existing)
- `MarketSentiment` - Sentiment analysis (existing)
- `SentimentItem` - Individual sentiment item (existing)

## ETF Crew

| Task | Output File | Schema | Description |
|------|-------------|--------|-------------|
| `etf_market_trends_task` | `etf_market_trends.md` | `ETFMarketTrend` | ETF market trends and emerging sectors |
| `etf_screening_task` | `high_potential_etfs.md` | `ETFScreeningResult` | Top 10 ETF candidates with analysis |
| `etf_technical_detail_task` | `etf_technical_details.md` | `ETFTechnicalAnalysis` | Technical analysis with factsheet and holdings |
| `etf_risk_assessment_task` | `etf_risk_assessment.md` | `ETFRiskProfile` | Risk assessment with standardized scoring |

**Additional Schemas**:
- `ETFCandidate` - Individual ETF in screening results
- `ETFTechnicalIndicators` - Technical indicators for ETFs
- `ETFQuantitativeMetrics` - Quantitative metrics for ETFs
- `ETFFactsheet` - ETF factsheet data (existing)
- `ETFTopHolding` - Individual ETF holding (existing)

## Crypto Crew

| Task | Output File | Schema | Description |
|------|-------------|--------|-------------|
| `market_analysis_task` | `crypto_market_analysis.md` | `CryptoMarketAnalysis` | Top 10 promising cryptocurrencies with market analysis |
| `technical_analysis_task` | `crypto_technical_analysis.md` | `CryptoTechnicalAnalysis` | Technical analysis with indicators and price targets |
| `risk_assessment_task` | `crypto_risk_assessment.md` | `CryptoRiskProfile` | Risk assessment with crypto-specific risks |
| `investment_strategy_task` | `crypto_investment_strategy.md` | `CryptoInvestmentStrategy` | Investment strategy with thesis and recommendations |

**Additional Schemas**:
- `CryptoCandidate` - Individual crypto in market analysis
- `CryptoTechnicalIndicators` - Technical indicators for crypto
- `CryptoQuantitativeMetrics` - Quantitative metrics for crypto
- `CryptoThesis` - Investment thesis with citations (existing)
- `CryptoRisk` - Alias for RiskAssessmentStandardized (existing)

## Investment Discovery Crew

| Task | Output File | Schema | Description |
|------|-------------|--------|-------------|
| `etf_discovery_task` | `a_plus_etfs.md` | `APlusDiscoveryResult` | A+ grade ETF candidates |
| `stock_discovery_task` | `a_plus_stocks.md` | `APlusDiscoveryResult` | A+ grade stock candidates |
| `crypto_discovery_task` | `a_plus_crypto.md` | `APlusDiscoveryResult` | A+ grade crypto candidates |
| `validation_task` | `validation_report.md` | `ValidationResult` | Validation results for all candidates |
| `optimization_task` | `optimization_report.md` | `OptimizationResult` | Portfolio optimization recommendations |
| `report_generation_task` | `rapport_opportunites_a_plus.html` | N/A (HTML) | Final HTML report |

**Additional Schemas**:
- `MarketRegime` - Market regime assessment
- `APlusCriteria` - Dynamic A+ scoring criteria
- `InvestmentCandidate` - Individual investment candidate
- `APlusAnalysis` - Detailed A+ analysis
- `PortfolioImprovement` - Portfolio improvement recommendation

## Portfolio Rebalancing Crew

| Task | Output File | Schema | Description |
|------|-------------|--------|-------------|
| `analyze_holding_task` | N/A | `PortfolioAnalysis` | Individual holding analysis |
| `calculate_price_targets_task` | N/A | `TradeRecommendation` | Price targets for holdings |
| `find_alternatives_task` | N/A | `AlternativeScenario` | Alternatives for underperforming holdings |
| `portfolio_analysis_task` | `portfolio_composition_analysis.md` | `PortfolioAnalysis` | Portfolio composition analysis |
| `rebalancing_optimization_task` | `rebalancing_trade_recommendations.md` | `RebalancingResult` | Trade recommendations |
| `risk_validation_task` | `portfolio_rebalancing_risk_validation.html` | `RebalancingResult` | Risk validation and compliance |

**Additional Schemas** (from `rebalancing/` package):
- `Holding` - Individual portfolio holding
- `PortfolioConfiguration` - Portfolio configuration
- `PriceData` - Price data for holdings
- `TradeRecommendation` - Trade recommendation
- `CostAnalysis` - Cost analysis for trades
- `ExecutionSummary` - Execution summary
- `PortfolioMetrics` - Portfolio metrics
- `RebalancingNeed` - Rebalancing need assessment

## Report Crew

The Report Crew is special - it has **NO intermediate JSON outputs**. All tasks consume upstream context and generate final HTML reports directly.

| Task | Output File | Schema | Description |
|------|-------------|--------|-------------|
| All tasks | `*.html` | N/A | Final HTML reports only |

**Note**: Report crew agents have empty tools lists and only consume context from upstream crews.

## Common Schemas

These schemas are shared across all crews:

- `RiskAssessmentStandardized` - Standardized 0-5 risk assessment
- `RiskLevel` - Risk level enum (Low, Medium, High, Very High)

## Schema Validation Rules

All schemas follow these standards:

1. **Strict Validation**: `model_config = ConfigDict(extra='forbid')`
2. **Modern Syntax**: Use `Type | None` instead of `Optional[Type]`
3. **Collections**: Use `list`, `dict`, `tuple` instead of `List`, `Dict`, `Tuple`
4. **Descriptions**: All fields have clear descriptions
5. **Constraints**: Appropriate validation constraints (ge, le, min_length, etc.)
6. **Versioning**: Include `schema_version` field for tracking

## Usage in Task Configurations

To use these schemas in task configurations:

```yaml
task_name:
  description: "Task description..."
  expected_output: "Expected output description..."
  output_pydantic: "SchemaClassName"  # Reference schema by name
  output_file: "output/path/file.json"  # Use .json extension
  agent: agent_name
  async_execution: true
```

Example:

```yaml
stock_screening_task:
  description: "Screen and identify top 10 stocks..."
  expected_output: "List of 10 stocks with analysis..."
  output_pydantic: "StockScreeningResult"
  output_file: "output/stock/emerging_stocks_analysis.json"
  agent: market_technical_analyst
  async_execution: true
```

---

**Last Updated**: 2025-05-10
**Status**: Complete
