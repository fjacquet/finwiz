# Phase 16: Report Enrichment - Research

**Researched:** 2026-02-09
**Domain:** HTML report enrichment with sentiment, macro, and economic calendar data
**Confidence:** HIGH

## Summary

Phase 16 adds three new visual sections to the existing HTML reports: (1) a per-holding sentiment section showing score, confidence, article count, and top headlines, (2) a portfolio-level macro dashboard with VIX, yield curve, GDP, CPI, Fed rate, and Fear & Greed index using traffic-light color coding, and (3) an economic calendar section showing upcoming FOMC meetings, CPI releases, and earnings dates. All rendering is Python/Jinja2 -- zero AI (AI Minimalism).

The codebase is well-prepared for this phase. Phases 14 and 15 already built the data pipeline: `SentimentMacroCollector` collects per-holding `NewsSentimentResult` (with articles, aggregate_sentiment, article_count, bullish/bearish/neutral counts) and session-level `MacroSnapshot` (with VIX, yield_curve_spread, fed_rate, cpi_yoy, gdp_growth, unemployment_rate, fear_greed_index, fear_greed_label). The `DeepAnalysisResult` already carries optional `sentiment_score`, `sentiment_confidence`, `macro_score`, and `macro_regime` fields. The raw data (including `news_sentiment` and `macro_snapshot`) flows through the analysis pipeline via `collect_raw_data()` in `deep_analysis_pipeline.py`.

The primary work is template authoring and data plumbing: (1) passing sentiment/macro data from the reporting orchestrator to templates, (2) creating new Jinja2 template sections or section generator functions, (3) adding CSS for traffic-light indicators and Fear & Greed gauge, and (4) building a new `EconomicCalendarAdapter` for Finnhub's `earnings_calendar()` and `calendar_economic()` endpoints.

**Primary recommendation:** Follow the stress test section pattern exactly. Create new section generator functions in `section_generators.py` for sentiment, macro dashboard, and economic calendar. Add them to `PythonReportGenerator._generate_html_report()`. For per-holding enriched reports, add sentiment sections to the `enriched_analysis_report.html` and `deep_analysis_report.html.j2` templates. For data, build a lightweight `EconomicCalendarAdapter` in `data/adapters/` and extend `SentimentMacroCollector` to collect calendar data.

## Standard Stack

### Core (Already Installed -- No New Dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| jinja2 | (installed) | Template rendering for HTML reports | Already used by all report generators |
| finnhub-python | >=2.4.20 | `earnings_calendar()` and `calendar_economic()` API | Already in pyproject.toml, used by FinnhubNewsAdapter |
| pydantic | >=2.0 | Schema validation for calendar events | Project standard for all schemas |

### Supporting (No New Dependencies)

| Component | Location | Status |
|-----------|----------|--------|
| NewsSentimentResult | `schemas/sentiment.py` | Complete from Phase 13 |
| MacroSnapshot | `schemas/macro.py` | Complete from Phase 13 |
| SentimentMacroCollector | `data/sentiment_collector.py` | Complete from Phase 13 |
| FinnhubNewsAdapter | `data/adapters/finnhub_news_adapter.py` | Complete from Phase 13 |
| FearGreedAdapter | `data/adapters/fear_greed_adapter.py` | Complete from Phase 13 |
| FREDAdapter | `data/adapters/fred_adapter.py` | Complete from Phase 13 |
| Section generators | `reporting/section_generators.py` | Existing pattern to follow |
| CSS styles | `reporting/css_styles.py` | Existing CSS module to extend |
| Enriched report template | `templates/enriched_analysis_report.html` | Per-holding template to extend |
| Deep analysis template | `templates/crew_reports/deep_analysis_report.html.j2` | Per-holding template to extend |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Inline traffic-light CSS | Chart.js / SVG gauge | Chart.js adds a JS dependency; inline CSS with colored spans is simpler, consistent with existing approach (stress test uses inline color coding), and requires no external assets |
| Finnhub `calendar_economic()` | FRED release calendar | Finnhub is already in the codebase; FRED does not have a clean calendar endpoint for upcoming events |
| Extending section_generators.py | Separate sentiment_section_generator.py | Keeping in section_generators.py follows the existing pattern (all consolidated report sections live there). Only split if the file grows too large |
| Pure CSS gauge for Fear & Greed | SVG/Canvas gauge | Pure CSS with conic-gradient is sufficient for a 0-100 gauge, works without JS, and renders correctly in static HTML files |

**Installation:** No new dependencies needed.

## Architecture Patterns

### Recommended Project Structure (New/Modified Files)

```
src/finwiz/
├── data/
│   └── adapters/
│       └── economic_calendar_adapter.py    # NEW: EconomicCalendarAdapter
│
├── schemas/
│   └── economic_calendar.py                # NEW: EconomicEvent, EarningsEvent, EconomicCalendar
│
├── data/
│   └── sentiment_collector.py              # MODIFY: Add collect_economic_calendar() method
│
├── reporting/
│   ├── section_generators.py               # MODIFY: Add 3 new section generators
│   ├── css_styles.py                       # MODIFY: Add traffic-light + gauge CSS
│   └── python_report_generator.py          # MODIFY: Wire new sections into report
│
├── templates/
│   ├── enriched_analysis_report.html       # MODIFY: Add sentiment section per holding
│   ├── crew_reports/
│   │   └── deep_analysis_report.html.j2    # MODIFY: Add sentiment section per holding
│   └── sentiment_section.html              # NEW (optional): Includable sentiment partial
│   └── macro_dashboard_section.html        # NEW (optional): Includable macro partial
│
├── orchestrators/
│   └── reporting_orchestrator.py           # MODIFY: Pass sentiment/macro data to report generator
│
├── flow_state_models.py                    # No change needed -- sentiment/macro fields exist
│
tests/unit/reporting/
│   ├── test_sentiment_section_rendering.py        # NEW: Sentiment section tests
│   ├── test_macro_dashboard_rendering.py          # NEW: Macro dashboard tests
│   └── test_economic_calendar_rendering.py        # NEW: Calendar section tests
tests/unit/data/
│   └── test_economic_calendar_adapter.py          # NEW: Calendar adapter tests
```

### Pattern 1: Section Generator Pattern (Existing Codebase Pattern)

**What:** Pure functions in `section_generators.py` that take data dicts and return HTML strings. Called by `PythonReportGenerator._generate_html_report()`.
**When to use:** For all portfolio-level report sections in the consolidated report.
**Example from codebase:**

```python
# Source: src/finwiz/reporting/section_generators.py (existing pattern)
def generate_stress_test_section(stress_test_results: list[dict[str, Any]] | None) -> str:
    """Generate stress test analysis section."""
    if not stress_test_results:
        return ""
    # ... build HTML cards with inline styles ...
    return f"""
  <div class="section">
    <h2>Analyse de Stress du Portefeuille</h2>
    {cards_html}
  </div>
    """
```

**New functions to create:**
- `generate_sentiment_section(holdings_sentiment: dict[str, dict] | None) -> str` -- per-holding sentiment summary for consolidated report
- `generate_macro_dashboard_section(macro_snapshot: dict | None) -> str` -- portfolio-level macro dashboard
- `generate_economic_calendar_section(calendar_data: dict | None) -> str` -- upcoming economic events

### Pattern 2: Per-Holding Template Section (Existing Codebase Pattern)

**What:** Jinja2 template blocks in `enriched_analysis_report.html` and `deep_analysis_report.html.j2` that conditionally render when data is available.
**When to use:** For adding sentiment data to individual per-holding reports.
**Example from codebase:**

```html
<!-- Source: templates/crew_reports/deep_analysis_report.html.j2, line 136 -->
{% if technical_details %}
<h3>Analyse Technique</h3>
<div class="metrics-grid">
    {% if technical_details.rsi is defined %}
    <div class="metric-card">
        <h4>RSI</h4>
        <p class="metric-value">{{ "%.1f"|format(technical_details.rsi) }}</p>
    </div>
    {% endif %}
</div>
{% endif %}
```

**New sections to add:**

```html
<!-- Sentiment section for per-holding reports -->
{% if sentiment_data %}
<div class="section">
    <h2>Sentiment de Marche</h2>
    <div class="metrics-grid">
        <div class="metric-card">
            <h4>Score de Sentiment</h4>
            <p class="metric-value {{ sentiment_color_class }}">
                {{ "%.2f"|format(sentiment_data.score) }}
            </p>
        </div>
        <!-- confidence, article_count, top headlines -->
    </div>
</div>
{% endif %}
```

### Pattern 3: Traffic-Light Color Coding (Existing Codebase Pattern)

**What:** CSS classes like `risk-low`, `risk-medium`, `risk-high` that map to green/yellow/red. Used extensively in `deep_analysis_report.html.j2`.
**When to use:** For all macro indicator visual status.
**Example from codebase:**

```html
<!-- Source: templates/crew_reports/deep_analysis_report.html.j2, lines 179-182 -->
<p class="metric-value {% if risk_score >= 0.7 %}risk-low{% elif risk_score >= 0.4 %}risk-medium{% else %}risk-high{% endif %}">
    {{ "%.0f"|format(risk_score * 100) }}%
</p>
```

**Application to macro dashboard:**

```html
<!-- VIX traffic light -->
<div class="metric-card">
    <h4>VIX (Volatilite)</h4>
    <p class="metric-value {% if vix <= 20 %}risk-low{% elif vix <= 30 %}risk-medium{% else %}risk-high{% endif %}">
        {{ "%.1f"|format(vix) }}
    </p>
</div>
```

### Pattern 4: Data Adapter Pattern (Existing Codebase Pattern)

**What:** Standalone adapter classes in `data/adapters/` that wrap external APIs, return Pydantic models, handle errors gracefully.
**When to use:** For the economic calendar data source.
**Example from codebase:**

```python
# Source: src/finwiz/data/adapters/fear_greed_adapter.py (existing pattern)
class FearGreedAdapter:
    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self.timeout_seconds = timeout_seconds
        self._cached_value: tuple[int, str] | None = None

    def is_available(self) -> bool:
        return True

    def get_fear_greed(self) -> tuple[int, str]:
        if self._cached_value is not None:
            return self._cached_value
        # ... fetch and cache ...
```

**New adapter:**

```python
class EconomicCalendarAdapter:
    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self.finnhub_key = os.getenv("FINNHUB_API_KEY")

    def get_economic_calendar(self, days_ahead: int = 30) -> EconomicCalendar:
        """Get upcoming economic events (FOMC, CPI) from Finnhub."""
        # Uses finnhub.Client.calendar_economic(_from, to)
        ...

    def get_earnings_calendar(self, tickers: list[str], days_ahead: int = 30) -> list[EarningsEvent]:
        """Get upcoming earnings dates for portfolio tickers."""
        # Uses finnhub.Client.earnings_calendar(_from, to, symbol)
        ...
```

## Codebase Analysis

### Data Availability (What Exists Today)

#### Per-Holding Sentiment Data (Phase 14)

The `NewsSentimentResult` schema (in `schemas/sentiment.py`) provides:
- `ticker` -- holding identifier
- `aggregate_sentiment` -- float, -1.0 to +1.0
- `weighted_sentiment` -- reliability-weighted score
- `article_count` -- total articles collected
- `bullish_count`, `bearish_count`, `neutral_count` -- article breakdown
- `articles` -- list of `NewsArticle` objects with `title`, `url`, `source`, `published_at`, `sentiment_score`, `sentiment_label`
- `data_freshness_hours` -- age of newest article

The `DeepAnalysisResult` (in `flow_state_models.py`) carries:
- `sentiment_score: float | None` -- -1.0 to +1.0 (None = no news)
- `sentiment_confidence: float | None` -- 0.0 to 1.0 (None = no news)

**Gap for REPORT-01:** The `DeepAnalysisResult` has score and confidence but NOT the full article list or headlines. The raw `NewsSentimentResult` with articles is only available during `collect_raw_data()` as `raw_data["news_sentiment"]`. It is NOT persisted in the enriched JSON or in `DeepAnalysisResult`.

**Resolution:** Either (a) persist top N headlines in `DeepAnalysisResult` (add optional field), (b) persist them in the enriched JSON, or (c) re-collect at report time. Option (b) is recommended: extend the enriched JSON to include a `sentiment_summary` dict with score, confidence, article_count, and top 3-5 headlines.

#### Portfolio-Level Macro Data (Phase 15)

The `MacroSnapshot` schema (in `schemas/macro.py`) provides:
- `vix: float | None` -- VIX Volatility Index
- `yield_curve_spread: float | None` -- 10Y-2Y spread
- `fed_rate: float | None` -- Federal Funds Rate
- `cpi_yoy: float | None` -- CPI Year-over-Year
- `gdp_growth: float | None` -- GDP Growth Rate
- `unemployment_rate: float | None` -- Unemployment Rate
- `treasury_10y: float | None`, `treasury_2y: float | None`
- `fear_greed_index: int | None` -- 0-100
- `fear_greed_label: str | None` -- "Extreme Fear" to "Extreme Greed"
- `fetched_at: datetime`

**Gap for REPORT-02/03:** The `MacroSnapshot` is collected per session by `SentimentMacroCollector.collect_macro()` but is NOT persisted outside the raw data dict during analysis. It is in `raw_data["macro_snapshot"]` but not in `DeepAnalysisResult`, not in flow state, and not directly accessible to the reporting orchestrator at report generation time.

**Resolution:** Either (a) add `macro_snapshot` to flow state (`FinwizState`), (b) persist it to a JSON file during analysis and read it back at report time, or (c) re-collect at report time. Option (a) is cleanest: add an optional `macro_snapshot: dict | None` field to `FinwizState` and set it during the deep analysis phase. Option (b) is a good alternative if state bloat is a concern.

#### Economic Calendar Data (Phase 16 New)

**Does NOT exist yet.** No economic calendar adapter, schema, or data collection exists in the codebase.

The Finnhub Python client already has the methods needed:
- `finnhub.Client.calendar_economic(_from, to)` -- returns upcoming economic events (FOMC, CPI releases, GDP releases, employment reports)
- `finnhub.Client.earnings_calendar(_from, to, symbol)` -- returns upcoming earnings dates per ticker

These methods are available in the already-installed `finnhub-python` package. The `FINNHUB_API_KEY` environment variable is already used by `FinnhubNewsAdapter`.

### Report Infrastructure (What Exists Today)

#### Consolidated Report (portfolio-level)

Generated by `PythonReportGenerator._generate_html_report()` in `reporting/python_report_generator.py`. It builds HTML by calling section generator functions in `reporting/section_generators.py`:

```python
html = f"""...
  {self._generate_executive_summary(portfolio_stats)}
  {self._generate_portfolio_overview(portfolio_review, portfolio_stats)}
  {self._generate_holdings_analysis(portfolio_review.holdings)}
  {self._generate_recommendations(portfolio_stats, discovery_results)}
  {self._generate_discovery_section(discovery_results)}
  {self._generate_deep_analysis_section(deep_analysis_results)}
  {self._generate_performance_metrics(deep_analysis_results)}
  {self._generate_stress_test_section(stress_test_results)}
  ...footer..."""
```

New sections (macro dashboard, sentiment summary, economic calendar) should be added here following the same pattern. The `generate_python_report()` function signature will need new parameters for `macro_snapshot` and `economic_calendar` data.

#### Per-Holding Reports

Two template types exist:
1. **`deep_analysis_report.html.j2`** -- Jinja2 template extending `crew_reports/base.html`. Uses `metrics-grid` layout with `metric-card` divs. All labels in French. Rendered by `DeepAnalysisReportGenerator`.
2. **`enriched_analysis_report.html`** -- Standalone Jinja2 template (does NOT extend base.html). Has its own comprehensive CSS including dark mode support, tooltips, glossary. Rendered by `EnrichedAnalysisReportGenerator`.

Both need a new sentiment section. The data is passed via `_prepare_template_variables()` in the enriched generator and directly in the deep analysis generator.

#### CSS Patterns

- Consolidated report: CSS in `reporting/css_styles.py` via `get_report_css()`. Uses classes: `.section`, `.stats-grid`, `.stat-card`, `.stat-number`, `.highlight`, `.success/.warning/.danger`, `.badge-buy/.badge-hold/.badge-sell`, `.grade-*`.
- Per-holding deep analysis: CSS in `templates/crew_reports/base.html`. Uses classes: `.metrics-grid`, `.metric-card`, `.metric-value`, `.risk-low`, `.risk-medium`, `.risk-high`.
- Per-holding enriched: CSS inline in `enriched_analysis_report.html`. Uses CSS custom properties with dark mode support. Uses classes: `.metrics-grid`, `.metric-card`, `.metric-value`, `.recommendation-box`, `.insight-box`.

All reports use French labels (e.g., "Evaluation des Risques", "Analyse Fondamentale").

### Data Flow at Report Time

```
ReportingOrchestrator.report()
  |-- _get_portfolio_review_from_state() -> PortfolioReview
  |-- _read_deep_analysis_from_files() -> dict (results_by_ticker)
  |-- _merge_deep_analysis_into_portfolio()
  |-- _generate_python_report(portfolio_review, deep_analysis_results)
       |-- PythonReportGenerator.generate_family_financial_plan()
            |-- _generate_html_report(portfolio_review, portfolio_stats,
                    deep_analysis_results, discovery_results, session_id,
                    stress_test_results)
                 |-- generate_executive_summary(portfolio_stats)
                 |-- generate_holdings_analysis(holdings)
                 |-- generate_stress_test_section(stress_test_results)
                 |-- ... (returns HTML string)
```

Macro snapshot and sentiment data are NOT currently in this flow. They need to be added.

### Traffic-Light Threshold Design

Based on prior decisions and existing patterns:

| Indicator | Green | Yellow | Red | Source |
|-----------|-------|--------|-----|--------|
| VIX | <= 20 | 20-30 | > 30 | Existing in `MacroSnapshot.get_market_regime()` |
| Yield Curve Spread | > 0.50 | 0 to 0.50 | < 0 (inverted) | Existing in `MacroSnapshot.is_recession_signal()` |
| GDP Growth | > 2.0% | 0-2.0% | < 0% (contraction) | Standard economic thresholds |
| CPI YoY | < 3.0% | 3.0-5.0% | > 5.0% | Standard inflation thresholds |
| Fed Rate | < 3.0% | 3.0-5.0% | > 5.0% | Context-dependent; standard ranges |
| Unemployment | < 5.0% | 5.0-7.0% | > 7.0% | Standard labor market thresholds |
| Fear & Greed | 55-100 (Greed) | 45-55 (Neutral) | 0-45 (Fear) | CNN Fear & Greed classification |

### Fear & Greed Gauge Design

The gauge should display as a semi-circular meter (0-100) with color gradient from red (Extreme Fear) through yellow (Neutral) to green (Extreme Greed). The current value is indicated with a needle or highlighted arc segment. This can be done with pure CSS using `conic-gradient` or a simple colored bar with a marker. The label from `fear_greed_label` is displayed below.

Simpler alternative (recommended): A horizontal bar with 5 colored segments (Extreme Fear / Fear / Neutral / Greed / Extreme Greed) and an arrow/marker at the current value. This is easier to implement in pure CSS and renders well in static HTML.

### French Labels

All existing reports use French labels. New sections must follow this convention:

- "Sentiment de Marche" (not "Market Sentiment")
- "Tableau de Bord Macroeconomique" (not "Macro Dashboard")
- "Calendrier Economique" (not "Economic Calendar")
- "Indice de Peur et Cupidite" (not "Fear & Greed Index")
- "Rendement du Tresor 10 ans" (not "10Y Treasury Yield")
- "Courbe des Taux" (not "Yield Curve")
- "Taux Directeur Fed" (not "Fed Rate")
- "Prochaines reunions FOMC" (not "Upcoming FOMC meetings")
- "Publications CPI" (not "CPI releases")
- "Dates de resultats" (not "Earnings dates")

## Key Decisions Required

### Decision 1: Where to persist sentiment article headlines for REPORT-01

**Options:**
- **(a) Add top_headlines field to DeepAnalysisResult** -- Adds `top_headlines: list[dict] | None` to the flow state model. Simple but adds state size.
- **(b) Persist sentiment_summary in enriched JSON** -- During `_store_enriched_analysis()`, include `sentiment_summary: {score, confidence, article_count, top_headlines: [{title, source, sentiment_label}]}` alongside the EnrichedAnalysis data. The enriched JSON is already written per-holding.
- **(c) Re-collect at report time** -- Call `FinnhubNewsAdapter.get_news_sentiment()` again during report generation. Adds latency and API calls.

**Recommendation:** Option (b). It follows the existing pattern where enriched JSON files contain all data needed for HTML generation. No schema changes to `DeepAnalysisResult` are needed. The enriched JSON already contains quantitative and qualitative data; adding a `sentiment_summary` key is natural.

### Decision 2: Where to persist MacroSnapshot for REPORT-02/03

**Options:**
- **(a) Add macro_snapshot to FinwizState** -- Add `macro_snapshot: dict | None = None` field. Set it once during first deep analysis. Accessible to reporting orchestrator via `self.state.macro_snapshot`.
- **(b) Persist to JSON file** -- Write `output/macro/macro_snapshot.json` during analysis. Read back at report time.
- **(c) Re-collect at report time** -- Call `SentimentMacroCollector.collect_macro()` during report generation.

**Recommendation:** Option (a) for simplicity -- macro data is session-level (collected once, shared across all holdings), and `FinwizState` is the natural place for session-level data. The reporting orchestrator already accesses `self.state`. Fallback to option (b) if state size is a concern.

### Decision 3: Economic calendar scope for REPORT-04

The Finnhub API provides:
- `calendar_economic()` -- General economic events (FOMC, CPI, GDP, employment reports, etc.)
- `earnings_calendar()` -- Per-ticker earnings dates

**Recommendation:** Collect both. General economic calendar (next 30 days) provides FOMC and CPI dates. Per-ticker earnings calendar provides earnings dates for portfolio holdings. Gate behind a `finnhub_calendar` feature flag (consistent with existing pattern).

### Decision 4: Template approach for per-holding sentiment

**Options:**
- **(a) Modify existing templates inline** -- Add `{% if sentiment_data %}` blocks directly in `enriched_analysis_report.html` and `deep_analysis_report.html.j2`.
- **(b) Create an includable partial** -- Create `templates/partials/sentiment_section.html` and `{% include %}` it from both templates.

**Recommendation:** Option (a) for simplicity. The two templates have different styling systems (enriched has its own CSS; deep analysis extends base.html), so a shared partial would need to handle both CSS contexts. Inline modifications are simpler and consistent with how other sections are added.

## Gotchas & Risks

### Risk 1: Finnhub API rate limits for calendar endpoints

The Finnhub free tier has 60 API calls/minute. The `earnings_calendar()` endpoint is called per-ticker, so a portfolio with 30 holdings could consume 30 calls. Mitigation: batch requests where possible, cache results per session, gate behind feature flag.

### Risk 2: MacroSnapshot may be None when feature flags are off

When `fred_macro` or `fear_greed_index` feature flags are disabled, `MacroSnapshot` will be `None` and all macro dashboard fields will be missing. Templates must handle `None` gracefully with `{% if macro_snapshot %}` guards. The section should show "Donnees macroeconomiques non disponibles" when data is missing.

### Risk 3: Sentiment data unavailability

When `finnhub_news` feature flag is off or API key is missing, no sentiment data exists. Templates must handle this with "Sentiment non disponible" placeholders. The sentiment section should only render when there is actual data.

### Risk 4: Economic calendar data varies by date

The `calendar_economic()` endpoint returns events only within the queried date range. Near quarter-end, there may be many events; mid-quarter, fewer. The calendar section should gracefully handle zero events: "Aucun evenement economique programme dans les 30 prochains jours."

### Risk 5: Two different per-holding template systems

The `enriched_analysis_report.html` and `deep_analysis_report.html.j2` templates have different:
- CSS systems (standalone vs. base.html inheritance)
- Data variable names (flattened vs. nested)
- Rendering paths (EnrichedAnalysisReportGenerator vs. DeepAnalysisReportGenerator)

Both must be updated consistently, but the CSS and variable handling will differ. Test both paths.

### Risk 6: Existing test patterns for rendering

Tests in `tests/unit/reporting/test_stress_test_rendering.py` validate HTML output by checking for string presence (e.g., `assert "Market Crash -20%" in html`). New tests should follow this exact pattern: call the section generator function with sample data and assert key strings are present in the output.

## Requirements Mapping

| Requirement | Implementation Location | Data Source | Key Challenge |
|-------------|------------------------|-------------|---------------|
| REPORT-01: Per-holding sentiment section | `enriched_analysis_report.html`, `deep_analysis_report.html.j2`, `section_generators.py` | `NewsSentimentResult` via enriched JSON | Persisting top headlines in enriched JSON |
| REPORT-02: Macro dashboard with traffic-light | `section_generators.py` (new function), `css_styles.py` | `MacroSnapshot` via flow state | Passing macro data to report generator |
| REPORT-03: Fear & Greed gauge | `section_generators.py` (within macro dashboard), `css_styles.py` | `MacroSnapshot.fear_greed_index/label` | Pure CSS gauge rendering |
| REPORT-04: Economic calendar | `section_generators.py` (new function), new `EconomicCalendarAdapter` | Finnhub `calendar_economic()` + `earnings_calendar()` | New adapter, new schema, feature flag gating |

## Estimated Complexity

| Component | Effort | Lines (est.) | Risk |
|-----------|--------|-------------|------|
| EconomicCalendarAdapter + schema | Medium | ~150 | Low -- follows FearGreedAdapter pattern |
| Sentiment section generator (consolidated) | Low | ~80 | Low -- follows stress test pattern |
| Macro dashboard section generator | Medium | ~120 | Low -- traffic-light CSS already exists |
| Fear & Greed gauge CSS | Low | ~40 | Low -- pure CSS |
| Economic calendar section generator | Low | ~80 | Low -- table rendering |
| Enriched template sentiment section | Medium | ~60 | Medium -- two templates to modify |
| Deep analysis template sentiment section | Medium | ~50 | Medium -- different CSS context |
| Data plumbing (orchestrator changes) | Medium | ~60 | Low -- adding parameters to existing functions |
| Enriched JSON sentiment summary persistence | Low | ~30 | Low -- add dict to existing store |
| Flow state macro_snapshot field | Low | ~10 | Low -- add optional field |
| CSS additions (traffic-light, gauge) | Low | ~60 | Low |
| Tests (4 new test files) | Medium | ~400 | Low -- follows existing test patterns |
| **Total** | **Medium** | **~1140** | **Low-Medium** |

## Testing Strategy

### Test Files

1. **`tests/unit/reporting/test_sentiment_section_rendering.py`** -- Tests `generate_sentiment_section()` for:
   - Returns empty string when data is None
   - Contains section header "Sentiment de Marche"
   - Contains score, confidence, article count
   - Contains top headline titles
   - Handles holdings with no sentiment (None score)
   - Color codes sentiment (green for bullish, red for bearish)

2. **`tests/unit/reporting/test_macro_dashboard_rendering.py`** -- Tests `generate_macro_dashboard_section()` for:
   - Returns empty string when macro_snapshot is None
   - Contains all 6 indicators (VIX, yield curve, GDP, CPI, Fed rate, unemployment)
   - Traffic-light color coding for each indicator
   - Fear & Greed gauge renders with correct value
   - Handles partial data (some fields None)
   - French labels present

3. **`tests/unit/reporting/test_economic_calendar_rendering.py`** -- Tests `generate_economic_calendar_section()` for:
   - Returns empty/placeholder when data is None or empty
   - Contains FOMC dates
   - Contains CPI release dates
   - Contains earnings dates for portfolio tickers
   - Handles zero events gracefully

4. **`tests/unit/data/test_economic_calendar_adapter.py`** -- Tests `EconomicCalendarAdapter` for:
   - Returns valid EconomicCalendar when data available
   - Handles missing API key gracefully
   - Handles API errors gracefully
   - Caches results per session
   - Date range calculation is correct

### Run Commands

```bash
# Unit tests for new files
uv run pytest tests/unit/reporting/test_sentiment_section_rendering.py -v
uv run pytest tests/unit/reporting/test_macro_dashboard_rendering.py -v
uv run pytest tests/unit/reporting/test_economic_calendar_rendering.py -v
uv run pytest tests/unit/data/test_economic_calendar_adapter.py -v

# Full test suite (regression)
make test

# Lint
make lint
```

## Implementation Order

Recommended sub-phase breakdown:

### Sub-phase 16-01: Data Plumbing & Schemas
1. Create `schemas/economic_calendar.py` (EconomicEvent, EarningsEvent, EconomicCalendar)
2. Create `data/adapters/economic_calendar_adapter.py`
3. Extend `SentimentMacroCollector` with `collect_economic_calendar()` method
4. Add `macro_snapshot: dict | None` field to `FinwizState`
5. Modify enriched JSON storage to include `sentiment_summary`
6. Add `economic_calendar` feature flag to definitions
7. Tests for adapter and schema

### Sub-phase 16-02: Section Generators & CSS
1. Add `generate_sentiment_section()` to `section_generators.py`
2. Add `generate_macro_dashboard_section()` to `section_generators.py`
3. Add `generate_economic_calendar_section()` to `section_generators.py`
4. Add traffic-light and gauge CSS to `css_styles.py`
5. Wire new sections into `PythonReportGenerator._generate_html_report()`
6. Pass macro/sentiment/calendar data through `ReportingOrchestrator` -> `PythonReportGenerator`
7. Tests for all 3 section generators

### Sub-phase 16-03: Per-Holding Template Enrichment
1. Add sentiment section to `enriched_analysis_report.html`
2. Add sentiment section to `deep_analysis_report.html.j2`
3. Pass sentiment data through `EnrichedAnalysisReportGenerator._prepare_template_variables()`
4. Pass sentiment data through deep analysis report context
5. Tests for per-holding rendering

## References

### Key Files (Absolute Paths)

| File | Role |
|------|------|
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/reporting/section_generators.py` | Consolidated report section generators (add new functions here) |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/reporting/python_report_generator.py` | Main report builder (wire new sections here) |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/reporting/css_styles.py` | CSS styles (add traffic-light + gauge CSS) |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/reporting/enriched_analysis_report_generator.py` | Per-holding enriched report generator |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/templates/enriched_analysis_report.html` | Per-holding enriched template (add sentiment section) |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/templates/crew_reports/deep_analysis_report.html.j2` | Per-holding deep analysis template (add sentiment section) |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/templates/crew_reports/base.html` | Base template with shared CSS (metrics-grid, risk-low/medium/high) |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/orchestrators/reporting_orchestrator.py` | Orchestrator (pass new data to generator) |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/flow_state.py` | Flow state (add macro_snapshot field) |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/flow_state_models.py` | DeepAnalysisResult (already has sentiment/macro fields) |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/schemas/sentiment.py` | NewsSentimentResult, NewsArticle, SentimentScore schemas |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/schemas/macro.py` | MacroSnapshot, MacroScore schemas |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/data/sentiment_collector.py` | SentimentMacroCollector (extend with calendar collection) |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/data/adapters/finnhub_news_adapter.py` | FinnhubNewsAdapter (pattern for new adapter) |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/data/adapters/fear_greed_adapter.py` | FearGreedAdapter (pattern for new adapter) |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/config/endpoints.py` | API endpoint constants (FINNHUB_BASE already exists) |
| `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/config/features/definitions.py` | Feature flag definitions (add economic_calendar flag) |
| `/Users/fjacquet/Projects/kiro/finwiz/tests/unit/reporting/test_stress_test_rendering.py` | Reference test pattern for section rendering |
| `/Users/fjacquet/Projects/kiro/finwiz/tests/unit/reporting/test_report_section_generators.py` | Reference test pattern for section generators |
| `/Users/fjacquet/Projects/kiro/finwiz/.planning/phases/14-sentiment-scoring/14-VERIFICATION.md` | Phase 14 verification (confirmed sentiment pipeline works) |
| `/Users/fjacquet/Projects/kiro/finwiz/.planning/phases/15-macro-context/15-VERIFICATION.md` | Phase 15 verification (confirmed macro pipeline works) |

### Finnhub API Methods

| Method | Parameters | Returns | Use Case |
|--------|-----------|---------|----------|
| `client.calendar_economic(_from, to)` | Date strings "YYYY-MM-DD" | Economic events (FOMC, CPI, GDP, etc.) | REPORT-04: Economic calendar |
| `client.earnings_calendar(_from, to, symbol)` | Date strings + ticker | Earnings dates per company | REPORT-04: Earnings dates |
| `client.company_news(symbol, _from, to)` | Ticker + date strings | News articles with sentiment | Already used by FinnhubNewsAdapter |
