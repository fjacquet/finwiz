# Analyse Architecture Python vs AI - Rapport Détaillé

**Date**: 2025-11-21
**Objectif**: Identifier la régression de valeur analytique et proposer une architecture hybride optimale
**Statut**: 🚧 Work in Progress - Document de spécification

---

## 📋 Table des Matières

1. [Contexte et Problématique](#contexte-et-problématique)
2. [Analyse de la Production Python](#analyse-de-la-production-python)
3. [Analyse de la Production AI](#analyse-de-la-production-ai)
4. [Identification des Doublons](#identification-des-doublons)
5. [Valeur Ajoutée Unique des Agents AI](#valeur-ajoutée-unique-des-agents-ai)
6. [Architecture Hybride Proposée](#architecture-hybride-proposée)
7. [Plan de Migration](#plan-de-migration)

---

## 🎯 Contexte et Problématique

### État Actuel

**Acquis (AI Minimalism réussi)** ✅

- Calculs déterministes en Python (DeepAnalysisScorer)
- Performance 10-20x améliorée
- Coût LLM réduit de 100% pour les calculs
- Consistance et testabilité parfaites

**Régression (Perte de valeur analytique)** ❌

- Agents AI reçoivent les décisions déjà prises
- Pas de réflexion contextuelle
- Pas d'analyse qualitative
- Rapports superficiels (formatage uniquement)
- Perte de propositions et d'insights

### Diagnostic

**Avant (Full AI):**

```
Data → AI Agent → Analyse + Calcul + Insights + Décision → Rapport Riche
```

**Maintenant (Python Only):**

```
Data → Python Calcul → Décision → AI Formatting → Rapport Superficiel
```

**Objectif (Hybride Optimal):**

```
Data → Python Calcul → AI Analyse Contextuelle → Décision Informée → Rapport Riche
```

---

## 🐍 Analyse de la Production Python

### 1. DeepAnalysisScorer (Calculs)

**Localisation**: `src/finwiz/scoring/deep_analysis_scorer.py`

**Ce que Python produit:**

```python
DeepAnalysisResult:
  ├── composite_score: float (0.0-1.0)
  ├── grade: str (A+ to F)
  ├── recommendation: str (BUY/HOLD/SELL)
  ├── rationale: str (template-based)
  │
  ├── Scores détaillés:
  │   ├── fundamental_score: float
  │   ├── technical_score: float
  │   └── risk_score: float
  │
  ├── Détails des composantes:
  │   ├── fundamental_details: dict
  │   │   ├── roe: float
  │   │   ├── debt_to_equity: float
  │   │   ├── revenue_growth: float
  │   │   └── profit_margin: float
  │   │
  │   ├── technical_details: dict
  │   │   ├── rsi: float
  │   │   ├── trend_direction: str
  │   │   └── momentum: str
  │   │
  │   └── risk_details: dict
  │       ├── volatility: float
  │       ├── max_drawdown: float
  │       └── beta: float
  │
  └── Metadata:
      ├── data_quality: dict
      ├── lineage: dict (data sources)
      └── confidence_level: float
```

**Rationale générée (Template-based):**

```python
# Exemple pour AAPL (Grade A)
f"{ticker} receives a {grade} grade with a composite score of {composite_score:.2f}. "
f"Fundamental analysis (score: {fund_score:.2f}) shows ROE of {roe:.1%}, "
f"debt-to-equity of {debt_equity:.2f}, and revenue growth of {growth:.1%}. "
f"Technical analysis (score: {tech_score:.2f}) indicates {trend} trend with RSI at {rsi:.1f}. "
f"Risk assessment (score: {risk_score:.2f}) shows {volatility:.1%} volatility and "
f"maximum drawdown of {max_dd:.1%}. Strong fundamentals, favorable technical indicators, "
f"and manageable risk profile support a BUY recommendation."
```

**Forces:**

- ✅ Calculs précis et déterministes
- ✅ Tous les métriques quantitatifs disponibles
- ✅ Traçabilité complète (lineage)
- ✅ Data quality tracking

**Faiblesses:**

- ❌ Rationale mécanique (template)
- ❌ Pas de contexte sectoriel/industrie
- ❌ Pas d'analyse de catalyseurs
- ❌ Pas de comparaison avec peers
- ❌ Pas d'analyse macroéconomique

---

## 🤖 Analyse de la Production AI (Crews)

### 1. Stock Crew (AVANT AI Minimalism)

**Localisation**: `src/finwiz/crews/stock_crew/`

**Agents et leurs rôles originaux:**

#### **10k_analyst**

- 📄 Analyse SEC 10-K/10-Q filings
- 🔍 Extrait business model, competitive advantages
- ⚖️ Identifie risk factors from filings
- 📊 Analyse trends in financial statements

**Exemple de valeur ajoutée:**

```
"Apple's 10-K reveals a strategic shift towards services revenue,
with recurring revenue now representing 23% of total revenue.
Management highlights supply chain diversification as a key risk
mitigation strategy, reducing dependence on single-country manufacturing."
```

#### **fundamental_analyst**

- 🔬 Analyse qualitative des fondamentaux
- 🏭 Contexte sectoriel et positionnement concurrentiel
- 📈 Analyse des drivers de croissance
- 💼 Évaluation du management et gouvernance

**Exemple de valeur ajoutée:**

```
"AAPL operates in the highly competitive consumer electronics sector
with strong pricing power due to brand loyalty. Key growth drivers include:
1. Services ecosystem expansion (Apple Music, iCloud, App Store)
2. Emerging markets penetration (India, Southeast Asia)
3. Wearables category leadership (Apple Watch, AirPods)

Competitive moat: Ecosystem lock-in effect, with 2+ billion active devices."
```

#### **technical_analyst**

- 📊 Analyse des patterns chartistes
- 🎯 Support/resistance levels avec contexte
- 📈 Volume analysis et institutional activity
- ⚡ Momentum indicators interprétation

**Exemple de valeur ajoutée:**

```
"AAPL broke through long-term resistance at $175 on strong volume
(2x average), suggesting institutional accumulation. The bullish
cup-and-handle pattern projects a target of $195. RSI at 58 indicates
room for upside before overbought conditions. Key support at $165
(50-day MA) provides a favorable risk/reward ratio."
```

#### **risk_assessor**

- ⚠️ Analyse des risques spécifiques au contexte
- 🌐 Risques géopolitiques et réglementaires
- 🏢 Risques opérationnels et de supply chain
- 💰 Risques financiers (liquidity, solvency)

**Exemple de valeur ajoutée:**

```
"Key risks for AAPL:
1. Regulatory: EU Digital Markets Act could force App Store changes,
   impacting high-margin services revenue (30% commission at risk)
2. Geopolitical: 90% of iPhone manufacturing in China creates exposure
   to US-China tensions; gradual shift to India underway
3. Competitive: Android gaining market share in premium segment
   (Samsung Galaxy S24, Google Pixel 8)
4. Product cycle: Mature smartphone market requires innovation
   (AR/VR with Vision Pro represents next frontier)"
```

#### **investment_reporter**

- 📝 Synthèse cohérente de toutes les analyses
- 🎯 Investment thesis avec catalyseurs
- 📊 Scénarios (bull/base/bear case)
- 💡 Actionable recommendations avec timing

**Exemple de valeur ajoutée:**

```
"Investment Thesis: ACCUMULATE
AAPL represents a high-quality growth-at-reasonable-price opportunity
with multiple positive catalysts:

Bull Case Catalysts (12-month):
- Vision Pro launch expanding to new markets (potential $10B+ revenue)
- Services revenue acceleration (20%+ growth vs. 15% hardware)
- Buyback program reducing shares outstanding (3% annually)
- Price target: $210 (+20% upside)

Base Case (9-month):
- Steady iPhone upgrade cycle (moderate growth)
- Services margin expansion offsetting hardware pressure
- Target: $185 (+10% upside)

Bear Case Risks:
- Regulatory headwinds reducing App Store margins
- Weak China demand amid economic slowdown
- Downside support: $165 (-5% downside)

Entry Strategy:
- Accumulate on dips to $170-175 range
- Stop loss: Close below $160 (50-week MA)
- Position size: 5-7% of portfolio (quality large-cap exposure)"
```

### 2. Deep Analysis Crew (Analyse de Holdings)

**Agents originaux:**

#### **deep_10k_analyst**

- 📄 Deep dive dans SEC filings
- 🔍 Analyse des footnotes et MD&A
- ⚖️ Red flags detection
- 📊 Year-over-year trends analysis

#### **deep_fundamental_analyst**

- 💎 Analyse de la qualité de l'entreprise
- 🏆 Competitive advantages assessment
- 📈 Sustainability des marges
- 💰 Capital allocation effectiveness

#### **deep_technical_analyst**

- 📊 Multi-timeframe analysis
- 🎯 Entry/exit points précis
- 📈 Institutional flow analysis
- ⚡ Short-term vs long-term trends

#### **deep_risk_assessor**

- ⚠️ Stress testing scenarios
- 🌐 Black swan event analysis
- 🏢 Contingency planning
- 💰 Portfolio correlation analysis

#### **deep_investment_reporter**

- 📝 Rapport complet avec action plan
- 🎯 KEEP/SELL decision avec justification détaillée
- 📊 Alternative holdings suggestions
- 💡 Rebalancing recommendations

---

## 🔄 Identification des Doublons

### Matrice Python vs AI

| **Élément**                    | **Python**   | **AI Crew**    | **Doublon?** | **Action**        |
| ------------------------------ | ------------ | -------------- | ------------ | ----------------- |
| **Calculs Quantitatifs**       |              |                |              |                   |
| ROE, Debt/Equity, Growth       | ✅ Calculé   | 🔄 Recalculé   | ❌ DOUBLON   | Supprimer du crew |
| RSI, MACD, Moving Averages     | ✅ Calculé   | 🔄 Recalculé   | ❌ DOUBLON   | Supprimer du crew |
| Volatility, Beta, Drawdown     | ✅ Calculé   | 🔄 Recalculé   | ❌ DOUBLON   | Supprimer du crew |
| Composite Score                | ✅ Calculé   | 🔄 Recalculé   | ❌ DOUBLON   | Supprimer du crew |
| Grade (A+ to F)                | ✅ Assigné   | 🔄 Réassigné   | ❌ DOUBLON   | Supprimer du crew |
| Recommendation (BUY/HOLD/SELL) | ✅ Déterminé | 🔄 Redéterminé | ❌ DOUBLON   | Supprimer du crew |
|                                |              |                |              |                   |
| **Analyse Qualitative**        |              |                |              |                   |
| SEC Filings Insights           | ❌ Non       | ✅ Unique      | ✅ VALEUR AI | **GARDER**        |
| Competitive Positioning        | ❌ Non       | ✅ Unique      | ✅ VALEUR AI | **GARDER**        |
| Growth Drivers Analysis        | ❌ Non       | ✅ Unique      | ✅ VALEUR AI | **GARDER**        |
| Management Quality             | ❌ Non       | ✅ Unique      | ✅ VALEUR AI | **GARDER**        |
| Industry Context               | ❌ Non       | ✅ Unique      | ✅ VALEUR AI | **GARDER**        |
| Catalysts Identification       | ❌ Non       | ✅ Unique      | ✅ VALEUR AI | **GARDER**        |
| Risk Scenarios                 | ❌ Template  | ✅ Contextuels | ✅ VALEUR AI | **GARDER**        |
| Bull/Base/Bear Cases           | ❌ Non       | ✅ Unique      | ✅ VALEUR AI | **GARDER**        |
| Peer Comparison                | ❌ Non       | ✅ Unique      | ✅ VALEUR AI | **GARDER**        |
| Entry/Exit Strategy            | ❌ Non       | ✅ Unique      | ✅ VALEUR AI | **GARDER**        |
| Alternative Suggestions        | ❌ Non       | ✅ Unique      | ✅ VALEUR AI | **GARDER**        |

---

## 💎 Valeur Ajoutée Unique des Agents AI

### 1. Analyse Contextuelle

**Ce que Python ne peut PAS faire:**

- 🏭 **Contexte sectoriel**: Comprendre les dynamiques de l'industrie
- 🌐 **Macroéconomie**: Lier les métriques au cycle économique
- ⚖️ **Réglementaire**: Identifier l'impact des nouvelles lois
- 🗺️ **Géopolitique**: Évaluer les risques géopolitiques

**Exemple concret:**

```
Python: "TSLA a une volatilité de 45% (score: 0.4)"

AI: "TSLA's 45% volatility reflects the EV sector's transition phase,
with regulatory tailwinds (IRA tax credits) offset by competitive
pressure from Chinese manufacturers (BYD, NIO). The recent Cybertruck
launch represents a high-risk/high-reward catalyst, potentially
expanding TAM but requiring significant production ramp-up."
```

### 2. Insights Qualitatifs

**Ce que Python ne peut PAS faire:**

- 🔬 **SEC Filings Analysis**: Interpréter le langage des rapports
- 💼 **Management Assessment**: Évaluer la qualité du leadership
- 🏆 **Competitive Moat**: Identifier les avantages durables
- 📈 **Growth Narrative**: Articuler l'histoire de croissance

**Exemple concret:**

```
Python: "NVDA a un ROE de 28%, debt/equity de 0.2 (excellent)"

AI: "NVDA's exceptional ROE of 28% reflects its dominant position in
AI accelerators (80%+ datacenter GPU market share). The low leverage
(0.2 debt/equity) provides flexibility to invest in R&D ($9B annually)
while returning cash to shareholders ($25B buyback program).

Key differentiators:
1. CUDA ecosystem lock-in effect (12+ years of developer mindshare)
2. Full-stack AI platform (hardware + software + cloud services)
3. First-mover advantage in AI inference chips (H100, B100 roadmap)

Management led by Jensen Huang has consistently anticipated technology
shifts (gaming → datacenter → AI), demonstrating strategic foresight."
```

### 3. Recommandations Actionnables

**Ce que Python ne peut PAS faire:**

- 🎯 **Timing**: Quand entrer/sortir
- 💰 **Position Sizing**: Combien investir
- 📊 **Scénarios**: Bull/base/bear cases avec probabilités
- 🔄 **Alternatives**: Suggestions de remplacements

**Exemple concret:**

```
Python: "AAPL grade A (0.87), recommendation: BUY"

AI: "AAPL Investment Strategy:

Entry Points:
- Primary: $170-175 (current support zone)
- Aggressive: $180-185 (on breakout with volume confirmation)

Position Sizing:
- 5-7% of portfolio (quality large-cap anchor)
- Scale in over 2-3 months to average entry price

Exit Strategy:
- Take profit: $200-210 (20%+ gain, resistance zone)
- Stop loss: Close below $160 (violation of 50-week MA)
- Trailing stop: 10% from peak to lock in gains

Scenarios (12-month horizon):
- Bull Case (30% probability): $220 target
  Catalysts: Vision Pro success, China demand recovery
- Base Case (50% probability): $185-195 target
  Scenario: Steady iPhone cycle, services growth
- Bear Case (20% probability): $150-160 target
  Risks: Regulatory headwinds, China weakness

Alternatives if AAPL not attractive:
- MSFT: Similar quality, better AI exposure
- GOOGL: Cheaper valuation, strong FCF generation"
```

---

## 🏗️ Architecture Hybride Proposée

### Principe Directeur

**"Python fait les calculs, AI fait l'analyse"**

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA COLLECTION                          │
│                    (Python Tools - No AI)                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    QUANTITATIVE ANALYSIS                         │
│                    (Python - Deterministic)                      │
│                                                                   │
│  ✅ Calculate: ROE, Debt/Equity, Growth, Margins                │
│  ✅ Calculate: RSI, MACD, Trend, Momentum                       │
│  ✅ Calculate: Volatility, Beta, Drawdown                       │
│  ✅ Compute: Composite Score, Grade                             │
│  ✅ Determine: Preliminary Recommendation                        │
│                                                                   │
│  Output: QuantitativeAnalysis (Pydantic)                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    QUALITATIVE ANALYSIS                          │
│                    (AI Agents - Contextual)                      │
│                                                                   │
│  INPUT: Python calculations as facts (no tool calling)          │
│                                                                   │
│  🤖 SEC Analyst:                                                 │
│     - Read Python metrics as context                            │
│     - Analyze 10-K/10-Q for qualitative insights               │
│     - Identify business model strengths/weaknesses             │
│                                                                   │
│  🤖 Fundamental Analyst:                                         │
│     - Read Python fundamental scores as baseline               │
│     - Add competitive positioning analysis                      │
│     - Identify growth drivers and catalysts                     │
│     - Assess management quality and capital allocation         │
│                                                                   │
│  🤖 Technical Analyst:                                           │
│     - Read Python technical indicators as data points          │
│     - Interpret chart patterns and volume behavior             │
│     - Provide entry/exit points with risk/reward              │
│                                                                   │
│  🤖 Risk Analyst:                                                │
│     - Read Python risk metrics as quantitative baseline        │
│     - Add contextual risk scenarios (regulatory, geopolitical) │
│     - Stress testing and black swan analysis                   │
│                                                                   │
│  🤖 Investment Strategist:                                       │
│     - Synthesize all analyses (quant + qual)                   │
│     - Create bull/base/bear scenarios                          │
│     - Refine recommendation with timing and sizing             │
│     - Suggest alternatives if needed                           │
│                                                                   │
│  Output: EnrichedAnalysis (Pydantic)                            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION SYNTHESIS                            │
│                    (Hybrid - Python + AI)                        │
│                                                                   │
│  Python Preliminary:     AI Contextual:                         │
│  • Grade: A              • Bull Case: BUY strong                │
│  • Score: 0.87           • Base Case: BUY moderate              │
│  • Rec: BUY              • Bear Case: HOLD                      │
│                          • Timing: Wait for $175 dip            │
│                                                                   │
│  Final Decision:                                                 │
│  • Grade: A (Python)                                            │
│  • Score: 0.87 (Python)                                         │
│  • Recommendation: BUY (Python baseline)                        │
│  • Confidence: HIGH (AI assessment)                             │
│  • Entry Strategy: $170-175 (AI insight)                        │
│  • Position Size: 5-7% (AI insight)                             │
│  • Alternatives: MSFT, GOOGL (AI suggestion)                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RICH REPORT GENERATION                        │
│                    (AI - Narrative + Python Facts)               │
│                                                                   │
│  ✍️ Executive Summary (AI narrative)                            │
│  📊 Quantitative Metrics (Python tables)                        │
│  🔬 Qualitative Analysis (AI insights)                          │
│  🎯 Investment Thesis (AI synthesis)                            │
│  📈 Scenarios & Catalysts (AI analysis)                         │
│  💡 Actionable Recommendations (AI strategy)                    │
│  🔄 Alternatives (AI suggestions)                               │
└─────────────────────────────────────────────────────────────────┘
```

### Nouveaux Schémas Pydantic

```python
class QuantitativeAnalysis(BaseModel):
    """Python-calculated quantitative metrics (deterministic)."""

    # Scores
    composite_score: float = Field(..., ge=0.0, le=1.0)
    fundamental_score: float = Field(..., ge=0.0, le=1.0)
    technical_score: float = Field(..., ge=0.0, le=1.0)
    risk_score: float = Field(..., ge=0.0, le=5.0)

    # Grade & Recommendation
    grade: str = Field(..., description="A+ to F")
    preliminary_recommendation: str = Field(..., description="BUY/HOLD/SELL")

    # Detailed metrics
    fundamental_metrics: dict[str, float]  # ROE, debt, growth, margins
    technical_indicators: dict[str, float]  # RSI, MACD, trend
    risk_metrics: dict[str, float]  # volatility, drawdown, beta

    # Metadata
    calculation_timestamp: datetime
    data_quality: DataQualityMetrics
    data_lineage: DataLineage


class QualitativeInsights(BaseModel):
    """AI-generated qualitative analysis (contextual)."""

    # SEC Analysis
    sec_insights: SecAnalysisInsights = Field(
        description="Business model, competitive advantages, risk factors from filings"
    )

    # Fundamental Analysis
    competitive_positioning: str = Field(description="Market position and competitive moat")
    growth_drivers: list[GrowthDriver] = Field(description="Key growth catalysts")
    management_assessment: ManagementQuality

    # Technical Analysis
    chart_patterns: list[ChartPattern]
    support_resistance: SupportResistanceLevels
    entry_exit_points: EntryExitStrategy

    # Risk Analysis
    contextual_risks: list[ContextualRisk] = Field(
        description="Regulatory, geopolitical, competitive risks"
    )
    stress_scenarios: list[StressScenario]

    # Investment Strategy
    investment_thesis: str = Field(description="Narrative thesis")
    bull_case: InvestmentScenario
    base_case: InvestmentScenario
    bear_case: InvestmentScenario

    # Recommendations
    entry_strategy: EntryStrategy
    position_sizing: PositionSizingAdvice
    alternatives: list[AlternativeHolding]


class EnrichedAnalysis(BaseModel):
    """Combined Python calculations + AI insights."""

    ticker: str
    asset_class: str
    analysis_date: datetime

    # Python (deterministic)
    quantitative: QuantitativeAnalysis

    # AI (contextual)
    qualitative: QualitativeInsights

    # Final synthesis
    final_grade: str = Field(description="From Python")
    final_score: float = Field(description="From Python")
    final_recommendation: str = Field(description="Python baseline")
    recommendation_confidence: str = Field(description="AI confidence level: LOW/MEDIUM/HIGH")

    # Rich output
    executive_summary: str = Field(description="AI-written summary")
    investment_rationale: str = Field(description="Detailed AI narrative")
    action_plan: ActionPlan = Field(description="Step-by-step AI guidance")
```

### Workflow Détaillé

#### Phase 1: Data Collection (Python - Pas de changement)

```python
# Existing: collect_data_with_python()
raw_data = {
    "price": 150.25,
    "roe": 0.25,
    "debt_to_equity": 0.3,
    "revenue_growth": 0.15,
    "rsi": 58,
    "volatility": 0.22,
    # ... all metrics
}
```

#### Phase 2: Quantitative Analysis (Python - Pas de changement)

```python
scorer = DeepAnalysisScorer()
quant_analysis = scorer.calculate_composite_score(ticker, asset_class, raw_data)

# Output:
QuantitativeAnalysis(
    composite_score=0.87,
    grade="A",
    preliminary_recommendation="BUY",
    fundamental_metrics={"roe": 0.25, "debt": 0.3, ...},
    technical_indicators={"rsi": 58, "trend": "upward", ...},
    risk_metrics={"volatility": 0.22, "drawdown": -0.15, ...}
)
```

#### Phase 3: Qualitative Analysis (AI - NOUVEAU)

```python
# AI agents receive Python results as CONTEXT (not to recalculate)

crew_inputs = {
    "ticker": "AAPL",
    "asset_class": "stock",

    # Python calculations as CONTEXT (read-only)
    "quantitative_analysis": quant_analysis.model_dump(),
    "grade": "A",  # Pre-calculated
    "score": 0.87,  # Pre-calculated
    "recommendation": "BUY",  # Preliminary

    # AI should focus on qualitative analysis
    "focus_areas": [
        "Analyze SEC 10-K for business model insights",
        "Assess competitive positioning in tech sector",
        "Identify growth drivers and catalysts",
        "Evaluate management quality and capital allocation",
        "Provide entry/exit strategy with timing",
        "Suggest alternatives if recommendation is SELL"
    ]
}

# AI Crew kickoff
result = DeepAnalysisCrew().kickoff(inputs=crew_inputs)

# Output:
QualitativeInsights(
    sec_insights=SecInsights(...),
    competitive_positioning="AAPL has strong moat...",
    growth_drivers=[...],
    investment_thesis="AAPL represents a high-quality...",
    bull_case=Scenario(target=210, probability=0.3, catalysts=[...]),
    entry_strategy=EntryStrategy(price_range=(170, 175), timing="Wait for dip"),
    alternatives=[Alternative(ticker="MSFT", rationale="Better AI exposure")]
)
```

#### Phase 4: Synthesis (Hybrid)

```python
enriched = EnrichedAnalysis(
    ticker="AAPL",
    quantitative=quant_analysis,  # Python
    qualitative=qual_insights,  # AI

    # Final decision (Python baseline + AI confidence)
    final_grade="A",  # From Python
    final_score=0.87,  # From Python
    final_recommendation="BUY",  # From Python (baseline)
    recommendation_confidence="HIGH",  # From AI (context assessment)

    # Rich narrative (AI)
    executive_summary="Apple represents a high-quality...",  # AI-written
    investment_rationale="...",  # AI-written
    action_plan=ActionPlan(...)  # AI-created
)
```

---

## 📋 Spécification Détaillée des Tâches AI

### Stock Crew - Tâches Refactorisées

#### Task 1: SEC Analysis (Qualitative Only)

```yaml
sec_analysis_task:
  description: >
    Analyze SEC 10-K and 10-Q filings for {ticker} to extract qualitative insights.

    CONTEXT PROVIDED (Do NOT recalculate):
    - Python has already calculated ROE: {roe}
    - Python has already calculated debt/equity: {debt_to_equity}
    - Python grade: {grade}, score: {score}

    YOUR FOCUS (Qualitative Analysis):
    1. Business Model Analysis
       - What is the company's core business?
       - What are the revenue streams?
       - How does the business model create value?

    2. Competitive Advantages
       - What makes this company different?
       - What are the moats (brand, network effects, patents, etc.)?
       - How sustainable are these advantages?

    3. Risk Factors from Filings
       - What risks does management disclose?
       - Are there red flags in footnotes or MD&A?
       - How do risks compare to previous filings?

    4. Strategic Direction
       - What is management's stated strategy?
       - Are there recent strategic shifts?
       - What are the key initiatives?

  expected_output: >
    SecAnalysisInsights Pydantic object with:
    - business_model: str (narrative description)
    - competitive_advantages: list[CompetitiveAdvantage]
    - risk_factors: list[RiskFactor] (from filings, not calculations)
    - strategic_initiatives: list[StrategicInitiative]
    - red_flags: list[str] (if any)

  agent: sec_analyst
  output_pydantic: SecAnalysisInsights
```

#### Task 2: Fundamental Context (Qualitative Only)

```yaml
fundamental_context_task:
  description: >
    Provide qualitative fundamental analysis context for {ticker}.

    CONTEXT PROVIDED (Do NOT recalculate):
    - Python fundamental score: {fundamental_score}
    - Python metrics: {fundamental_metrics}
    - Python grade: {grade}

    YOUR FOCUS (Contextual Analysis):
    1. Industry Dynamics
       - What is the current state of the {industry} sector?
       - What are the key trends affecting this industry?
       - How does {ticker} compare to industry peers?

    2. Growth Drivers
       - What are the specific catalysts for growth?
       - Which drivers are short-term vs long-term?
       - What is the TAM expansion potential?

    3. Competitive Positioning
       - Who are the main competitors?
       - What is {ticker}'s market share?
       - Is the competitive position strengthening or weakening?

    4. Management Quality
       - What is the track record of the management team?
       - How effective is capital allocation?
       - Are there governance concerns?

    DO NOT recalculate ROE, margins, or growth rates - focus on WHY and CONTEXT.

  expected_output: >
    FundamentalContextInsights with:
    - industry_analysis: IndustryAnalysis
    - growth_drivers: list[GrowthDriver]
    - competitive_analysis: CompetitiveAnalysis
    - management_assessment: ManagementQuality

  agent: fundamental_analyst
  output_pydantic: FundamentalContextInsights
  depends_on:
    - sec_analysis_task
```

#### Task 3: Technical Strategy (Interpretation Only)

```yaml
technical_strategy_task:
  description: >
    Provide technical analysis INTERPRETATION for {ticker}.

    CONTEXT PROVIDED (Do NOT recalculate):
    - Python technical score: {technical_score}
    - Python indicators: {technical_indicators}
      * RSI: {rsi}
      * MACD: {macd}
      * Trend: {trend_direction}

    YOUR FOCUS (Interpretation & Strategy):
    1. Chart Pattern Analysis
       - What patterns are visible on the chart?
       - Are there breakout/breakdown signals?
       - What is the volume behavior?

    2. Support & Resistance
       - Identify key support levels with context
       - Identify resistance levels with context
       - Are these levels being tested?

    3. Entry/Exit Strategy
       - What are optimal entry price points?
       - What are take-profit targets?
       - Where should stop-loss be placed?
       - What is the risk/reward ratio?

    4. Timing Considerations
       - Is this a good time to enter?
       - Should we wait for a pullback?
       - What are the short-term vs long-term signals?

    DO NOT recalculate RSI, MACD - use Python values and INTERPRET them.

  expected_output: >
    TechnicalStrategyInsights with:
    - chart_patterns: list[ChartPattern]
    - support_resistance: SupportResistanceLevels
    - entry_exit_strategy: EntryExitStrategy
    - timing_assessment: TimingAssessment

  agent: technical_analyst
  output_pydantic: TechnicalStrategyInsights
```

#### Task 4: Contextual Risk Assessment

```yaml
contextual_risk_task:
  description: >
    Assess CONTEXTUAL and QUALITATIVE risks for {ticker}.

    CONTEXT PROVIDED (Do NOT recalculate):
    - Python risk score: {risk_score}
    - Python metrics: {risk_metrics}
      * Volatility: {volatility}
      * Beta: {beta}
      * Max Drawdown: {max_drawdown}

    YOUR FOCUS (Contextual Risks):
    1. Regulatory Risks
       - Are there pending regulations affecting {ticker}?
       - What is the regulatory environment in key markets?
       - How might policy changes impact the business?

    2. Geopolitical Risks
       - What geopolitical exposures exist?
       - Are there supply chain risks?
       - Currency or trade war risks?

    3. Competitive Risks
       - Are new competitors emerging?
       - Is market share being eroded?
       - Technology disruption risks?

    4. Operational Risks
       - Are there execution risks for growth plans?
       - Supply chain vulnerabilities?
       - Key person dependencies?

    5. Stress Scenarios
       - What would happen in a recession?
       - What if key assumptions fail?
       - Black swan event analysis?

    DO NOT recalculate volatility/beta - provide CONTEXT for these metrics.

  expected_output: >
    ContextualRiskInsights with:
    - regulatory_risks: list[RegulatoryRisk]
    - geopolitical_risks: list[GeopoliticalRisk]
    - competitive_risks: list[CompetitiveRisk]
    - operational_risks: list[OperationalRisk]
    - stress_scenarios: list[StressScenario]

  agent: risk_assessor
  output_pydantic: ContextualRiskInsights
  depends_on:
    - sec_analysis_task
```

#### Task 5: Investment Synthesis (Strategy & Narrative)

```yaml
investment_synthesis_task:
  description: >
    Synthesize all analyses into a comprehensive investment strategy for {ticker}.

    CONTEXT PROVIDED:
    - Python grade: {grade}
    - Python score: {score}
    - Python preliminary recommendation: {preliminary_recommendation}
    - SEC insights: {sec_insights}
    - Fundamental context: {fundamental_context}
    - Technical strategy: {technical_strategy}
    - Contextual risks: {contextual_risks}

    YOUR ROLE (Synthesis & Strategy):
    1. Investment Thesis
       - Write a cohesive investment thesis (2-3 paragraphs)
       - Synthesize quant + qual analyses
       - What is the core investment case?

    2. Scenario Analysis
       - Bull Case: What if everything goes right? (price target, probability, catalysts)
       - Base Case: Most likely scenario (price target, probability)
       - Bear Case: What could go wrong? (downside target, probability, risks)

    3. Refined Recommendation
       - START with Python preliminary recommendation: {preliminary_recommendation}
       - Based on qualitative insights, is this recommendation APPROPRIATE?
       - Provide confidence level: LOW/MEDIUM/HIGH
       - If confidence is LOW, explain why and suggest HOLD or wait

    4. Action Plan
       - Entry Strategy: What prices, what timing?
       - Position Sizing: How much to invest?
       - Exit Strategy: Take profit targets, stop loss
       - Monitoring: What to watch going forward?

    5. Alternatives (if SELL or low confidence)
       - If recommendation is SELL, suggest 2-3 alternatives
       - If confidence is LOW, suggest what to wait for

  expected_output: >
    InvestmentSynthesis with:
    - investment_thesis: str (narrative)
    - bull_case: InvestmentScenario
    - base_case: InvestmentScenario
    - bear_case: InvestmentScenario
    - final_recommendation: str (BUY/HOLD/SELL - from Python or refined)
    - recommendation_confidence: str (LOW/MEDIUM/HIGH)
    - confidence_rationale: str (why this confidence level?)
    - action_plan: ActionPlan
    - alternatives: list[AlternativeHolding] (if applicable)

  agent: investment_strategist
  output_pydantic: InvestmentSynthesis
  depends_on:
    - sec_analysis_task
    - fundamental_context_task
    - technical_strategy_task
    - contextual_risk_task
```

---

## 🚀 Plan de Migration

### Phase 1: Nouveaux Schémas Pydantic (Semaine 1)

**Objectif**: Définir les nouveaux schémas pour la séparation Python/AI

**Tâches**:

- [ ] Créer `QuantitativeAnalysis` schema
- [ ] Créer `QualitativeInsights` schema
- [ ] Créer `EnrichedAnalysis` schema
- [ ] Créer sous-schemas (SecAnalysisInsights, FundamentalContextInsights, etc.)
- [ ] Tests unitaires pour validation Pydantic

**Localisation**: `src/finwiz/schemas/enriched_analysis.py`

### Phase 2: Refactor Deep Analysis Orchestrator (Semaine 2)

**Objectif**: Modifier le orchestrator pour séparer quant/qual

**Tâches**:

- [ ] Modifier `_process_single_holding()` pour retourner `QuantitativeAnalysis`
- [ ] Créer nouvelle méthode `_enrich_with_qualitative_analysis()`
- [ ] Passer les résultats Python comme INPUT au crew (pas comme résultat final)
- [ ] Merger quant + qual dans `EnrichedAnalysis`

**Localisation**: `src/finwiz/orchestrators/deep_analysis_orchestrator.py`

### Phase 3: Refactor Stock Crew Tasks (Semaine 3)

**Objectif**: Réécrire les tâches pour éliminer doublons et focus sur qualité

**Tâches**:

- [ ] Réécrire `sec_analysis_task` (qualitative only)
- [ ] Réécrire `fundamental_context_task` (contextual only)
- [ ] Réécrire `technical_strategy_task` (interpretation only)
- [ ] Réécrire `contextual_risk_task` (contextual risks only)
- [ ] Réécrire `investment_synthesis_task` (synthesis + strategy)
- [ ] Supprimer les tool calls redondants

**Localisation**: `src/finwiz/crews/stock_crew/config/tasks.yaml`

### Phase 4: Refactor Deep Analysis Crew (Semaine 4)

**Objectif**: Adapter le deep analysis crew au nouveau pattern

**Tâches**:

- [ ] Appliquer le même pattern que stock_crew
- [ ] Focus sur KEEP/SELL decision avec justification riche
- [ ] Ajouter alternatives suggestion quand SELL

**Localisation**: `src/finwiz/crews/deep_analysis/`

### Phase 5: Report Generation Enhancement (Semaine 5)

**Objectif**: Générer des rapports riches combinant quant + qual

**Tâches**:

- [ ] Nouveau template HTML pour EnrichedAnalysis
- [ ] Section quantitative (tables Python)
- [ ] Section qualitative (AI narrative)
- [ ] Executive summary (AI synthesis)
- [ ] Action plan (AI guidance)

**Localisation**: `src/finwiz/reporting/enriched_report_generator.py`

### Phase 6: Testing & Validation (Semaine 6)

**Objectif**: Valider que la qualité est restaurée sans perdre performance

**Tâches**:

- [ ] Tests unitaires pour nouveaux schemas
- [ ] Tests d'intégration pour workflow complet
- [ ] Comparaison qualitative: rapports AVANT vs APRÈS
- [ ] Validation performance: temps d'exécution acceptable
- [ ] Validation coûts: LLM costs sous contrôle

---

## 📊 Métriques de Succès

### Performance (maintenir)

- ✅ Temps d'exécution ≤ 30s par holding
- ✅ Coût LLM ≤ \$0.10 per holding
- ✅ Calculs déterministes (100% consistants)

### Qualité (restaurer)

- ✅ Rapports ≥ 2000 mots (vs ~500 actuellement)
- ✅ 5+ insights qualitatifs par rapport
- ✅ Scénarios bull/base/bear présents
- ✅ Action plan avec entry/exit strategy
- ✅ Alternatives suggérées pour SELL decisions

### User Satisfaction (mesurer)

- ✅ Rapports "actionnables" (feedback utilisateur)
- ✅ Insights "non évidents" présents
- ✅ Contextualisation sectorielle présente

---

## ✅ Prochaines Étapes

1. **Validation de cette analyse** avec l'équipe
2. **Priorisation** des phases de migration
3. **Création des tickets** détaillés pour chaque phase
4. **POC** sur un holding test (ex: AAPL) pour valider le concept
5. **Itération** basée sur le POC avant rollout complet

---

**Document créé le**: 2025-11-21
**Version**: 1.0 (Draft)
**Prochaine révision**: Après validation POC
