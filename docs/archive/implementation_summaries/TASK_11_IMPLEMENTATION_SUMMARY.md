# Task 11 Implementation Summary: Update Report Crew Task Configuration

## Overview
Updated `src/finwiz/crews/report_crew/config/tasks.yaml` to incorporate new data accessors and validators, ensuring transparent handling of unavailable data and eliminating data hallucination.

## Changes Made

### 1. Added Data Quality and Transparency Rules Section

Added a new critical section after the anti-hallucination rules:

```yaml
⚠️ DATA QUALITY AND TRANSPARENCY RULES ⚠️

1. **USE NEW DATA ACCESSORS**: All data must be accessed through validated accessors:
   - SECFilingURLGenerator for SEC filing URLs (never hardcode URLs)
   - PortfolioHoldingsProcessor for portfolio data (processes ALL holdings)
   - APlusDiscoveryAccessor for A+ opportunities (checks if discovery ran)
   - BacktestingMetricsExtractor for backtesting data (handles missing metrics)
   - DataAvailabilityTracker for data source status (tracks freshness)

2. **DISPLAY "DATA NOT AVAILABLE" INSTEAD OF GENERATING FAKE DATA**:
   - When SEC filings are unavailable: Display "No SEC filings available"
   - When A+ discovery hasn't run: Display inputs.discovery_status.message
   - When backtesting data is missing: Display inputs.backtesting_status.message
   - When sentiment data is unavailable: Display "Sentiment data not available"
   - NEVER generate fake URLs, fake metrics, or placeholder data

3. **INCLUDE DATA AVAILABILITY SUMMARY**:
   - Use inputs.data_availability_summary for comprehensive status
   - Display total_sources, available_sources, unavailable_sources, stale_sources
   - Show source_details for each data source (status, age, record count)
   - Include this summary in report footer and annexes section

4. **SHOW FRESHNESS WARNINGS**:
   - Use inputs.data_availability_summary.freshness_warnings
   - Display warnings for data older than 7 days with ⚠️ icon
   - Indicate data age in days/hours
   - Recommend refreshing stale data sources

5. **TRANSPARENT ERROR HANDLING**:
   - When data is missing: Explain why and what it means
   - When validation fails: Show which holdings failed and why
   - When URLs are invalid: Display "URL not available" instead of broken links
   - Always provide context for missing or incomplete data
```

### 2. Enhanced SEC/EDGAR Citation Instructions

Updated Key Step 3 to emphasize using SECFilingURLGenerator:

```yaml
3. **REVIEW SEC/EDGAR CITATIONS** (ONLY for validated tickers):
   - Use ONLY URLs provided by SECFilingURLGenerator (never hardcode URLs)
   - If URL is None or empty: Display "No SEC filings available" for that ticker
   - Verify all SEC URLs are in current EDGAR format (not old formats)
   - Include filing dates and excerpts ONLY when URLs are valid
   - Never generate fake CIK numbers or filing URLs
```

### 3. Enhanced Market Sentiment Instructions

Updated Key Step 4 to ensure transparent handling of sentiment data:

```yaml
4. **ANALYZE MARKET SENTIMENT DATA**:
   - Use aggregated scores and top 3 sources with URLs and dates
   - If sentiment data is unavailable: Display "Sentiment data not available"
   - Verify all news URLs are real and accessible (no example.com or test URLs)
   - Include publication dates and confidence scores when available
```

### 4. Enhanced Portfolio Review Section

Updated the portfolio review section to emphasize using PortfolioHoldingsProcessor:

```yaml
📦 Revue du portefeuille: Conserver ou Vendre (section spéciale)
  - **UTILISER PortfolioHoldingsProcessor**: Toutes les positions sont traitées via le processeur
  - **INCLURE TOUTES LES POSITIONS**: Le processeur garantit que 100% des positions CSV sont incluses
  - **AFFICHER LE STATUT DE VALIDATION**: Indiquer si la position a réussi ou échoué la validation
  - Si validation échouée: Afficher la raison et les alternatives suggérées
  - **RÉSUMÉ DE TRAITEMENT**: Afficher le nombre de positions traitées vs positions dans les CSV
  - **SI DES POSITIONS SONT MANQUANTES**: Expliquer pourquoi et afficher les positions exclues avec raisons
```

### 5. Enhanced Data Availability Report Section

Significantly expanded the data availability section:

```yaml
- **Rapport de Disponibilité des Données** 📊 (NOUVELLE SECTION REQUISE):
  * **UTILISER DataAvailabilityTracker via inputs.data_availability_summary**
  * **CETTE SECTION EST OBLIGATOIRE - NE JAMAIS L'OMETTRE**
  * Statut global: COMPLETE/PARTIAL/INSUFFICIENT
  * Résumé des sources de données with icons: ✅ disponible, ❌ indisponible, ⚠️ périmé
  * Détails par source including age in hours and record counts
  * **Avertissements de fraîcheur** with impact explanation
  * **Transparence sur les données manquantes** with reasons and suggested actions
```

### 6. Added Strict "No Data Generation" Rules

Added comprehensive rules at the end of the task description:

```yaml
⚠️ RÈGLES STRICTES - PAS DE GÉNÉRATION DE DONNÉES ⚠️

1. **JAMAIS GÉNÉRER DE FAUSSES DONNÉES**:
   - Ne jamais inventer des URLs SEC/EDGAR
   - Ne jamais créer de faux numéros CIK
   - Ne jamais générer de fausses métriques de backtesting
   - Ne jamais inventer des scores de sentiment
   - Ne jamais créer de fausses opportunités A+

2. **TOUJOURS AFFICHER "NON DISPONIBLE" QUAND LES DONNÉES MANQUENT**:
   - SEC filings: "No SEC filings available" ou "SEC data not available"
   - A+ discovery: Afficher inputs.discovery_status.message
   - Backtesting: Afficher inputs.backtesting_status.message
   - Sentiment: "Sentiment data not available" si aucune source
   - Portfolio: "Portfolio data incomplete" avec détails

3. **EXPLIQUER POURQUOI LES DONNÉES MANQUENT**:
   - Discovery pas exécuté: "Use --discovery flag to enable A+ opportunity discovery"
   - Backtesting indisponible: "Backtesting requires discovery to be run first"
   - SEC filings introuvables: "No recent SEC filings found for this ticker"
   - Sentiment indisponible: "No recent news articles found for sentiment analysis"

4. **UTILISER LES ACCESSEURS DE DONNÉES**:
   - SECFilingURLGenerator: Pour tous les URLs SEC (jamais hardcodés)
   - APlusDiscoveryAccessor: Pour vérifier si discovery a été exécuté
   - BacktestingMetricsExtractor: Pour extraire les métriques (None si manquantes)
   - DataAvailabilityTracker: Pour le statut de toutes les sources

5. **VALIDATION DES URLS**:
   - Tous les URLs doivent être vérifiés avant inclusion
   - URLs invalides ou None: Afficher "URL not available"
   - Ne jamais inclure d'URLs de test (example.com, test.com, etc.)
   - Tous les URLs SEC doivent être au format EDGAR actuel
```

### 7. Enhanced Expected Output Section

Added critical data quality requirements to the expected output:

```yaml
**EXIGENCES DE QUALITÉ DES DONNÉES** (CRITIQUES):

1. **ZÉRO URLS HALLUCINÉS**: Tous les URLs SEC/EDGAR doivent être réels et vérifiés
   - Utiliser SECFilingURLGenerator pour tous les URLs SEC
   - Si URL est None: Afficher "No SEC filings available"
   - Jamais d'URLs hardcodés ou inventés

2. **TRANSPARENCE TOTALE SUR LES DONNÉES MANQUANTES**:
   - Afficher clairement "Data not available" quand applicable
   - Expliquer pourquoi les données manquent
   - Indiquer comment obtenir les données manquantes

3. **RÉSUMÉ DE DISPONIBILITÉ DES DONNÉES OBLIGATOIRE**:
   - Section dédiée dans les annexes
   - Pied de page avec résumé formaté
   - Icônes de statut: ✅ disponible, ⚠️ périmé, ❌ indisponible

4. **AVERTISSEMENTS DE FRAÎCHEUR**:
   - Afficher tous les avertissements
   - Indiquer l'âge des données
   - Recommander le rafraîchissement si > 7 jours

5. **PORTFOLIO COMPLET**:
   - Inclure 100% des positions des fichiers CSV
   - Afficher le statut de validation
   - Expliquer les positions exclues
   - Résumé: positions traitées vs positions dans CSV
```

### 8. Enhanced Report Footer Requirements

Updated footer requirements to emphasize data availability:

```yaml
**PIED DE PAGE DU RAPPORT** (REQUIS):
- **INCLURE LE RÉSUMÉ DE DISPONIBILITÉ DES DONNÉES** (obligatoire)
- Utiliser inputs.data_availability_summary_formatted pour le contenu
- Afficher les icônes de statut: ✅ disponible, ⚠️ périmé, ❌ indisponible
- Indiquer le nombre total de sources et leur statut
- Lister les avertissements de fraîcheur s'il y en a
- Ajouter l'horodatage de génération du rapport
- **TRANSPARENCE TOTALE**: Le pied de page doit clairement indiquer quelles données sont disponibles/manquantes
```

## Requirements Addressed

This implementation addresses the following requirements from the spec:

### Requirement 1.1, 1.2, 1.3 (Real Sentiment Data)
- Added instructions to display "Sentiment data not available" when unavailable
- Emphasized verifying all news URLs are real and accessible
- Prohibited generating fake sentiment data

### Requirement 2.5 (Valid SEC Filing URLs)
- Added instructions to use SECFilingURLGenerator exclusively
- Emphasized displaying "No SEC filings available" when URLs are None
- Prohibited hardcoding or inventing SEC URLs
- Required verification of URL format

### Requirement 4.5 (A+ Discovery Integration)
- Added instructions to check discovery_status before displaying opportunities
- Emphasized displaying discovery_status.message when discovery hasn't run
- Prohibited inventing fake A+ opportunities

### Requirement 6.1, 6.2 (Data Availability Transparency)
- Made data availability summary section mandatory
- Required display of freshness warnings
- Emphasized transparent communication of missing data
- Required explanation of why data is missing and how to obtain it

## Impact

These changes ensure that:

1. **Zero Hallucinated Data**: All data must come from validated sources or be marked as unavailable
2. **Complete Transparency**: Users always know which data is available, stale, or missing
3. **Clear Guidance**: When data is missing, users are told why and how to get it
4. **Proper Tool Usage**: All data access goes through the new accessor components
5. **Portfolio Completeness**: 100% of portfolio holdings are processed and reported
6. **Data Freshness**: Stale data is clearly flagged with age and refresh recommendations

## Testing Recommendations

To verify these changes work correctly:

1. Run report generation with missing SEC filings - should show "No SEC filings available"
2. Run report without --discovery flag - should show discovery_status.message
3. Run report with stale data (>7 days) - should show freshness warnings
4. Run report with incomplete portfolio - should show all holdings with validation status
5. Verify data availability summary appears in both annexes and footer
6. Verify no hallucinated URLs or fake data in any scenario

## Files Modified

- `src/finwiz/crews/report_crew/config/tasks.yaml` - Updated all task descriptions with data quality rules

## Next Steps

1. Test report generation with various data availability scenarios
2. Verify all data accessors are properly integrated in the report crew
3. Ensure data availability summary is correctly displayed in reports
4. Validate that no fake data is generated in any scenario
5. Confirm freshness warnings appear for stale data
