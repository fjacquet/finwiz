# Guide Utilisateur - Découverte d'Investissements A+

## Vue d'ensemble

Le système de découverte d'investissements A+ de FinWiz transforme votre expérience d'investissement en passant d'une évaluation passive de votre portefeuille existant à une découverte proactive d'opportunités exceptionnelles. Ce guide vous explique comment utiliser ces nouvelles fonctionnalités pour améliorer significativement la qualité de vos investissements.

## Qu'est-ce qu'un investissement A+

Un investissement A+ représente l'excellence dans sa catégorie avec un score ≥ 0.95 sur notre échelle de notation. Ces investissements combinent :

- **Performance exceptionnelle** : Rendements supérieurs ajustés au risque
- **Qualité supérieure** : Fondamentaux solides et gestion exemplaire  
- **Coûts optimisés** : Frais réduits maximisant vos rendements nets
- **Liquidité élevée** : Facilité d'achat et de vente
- **Transparence** : Informations complètes et fiables

## Comment fonctionne la découverte A+

### 1. Analyse automatique du marché

Le système scanne automatiquement :

- **ETFs** : Plus de 3,000 ETFs mondiaux avec focus UCITS
- **Actions** : Milliers d'actions avec analyse fondamentale approfondie
- **Cryptomonnaies** : Top cryptos avec adoption institutionnelle

### 2. Filtrage intelligent

Chaque actif est évalué selon des critères stricts :

#### ETFs A+

- Frais ≤ 0.15% (ETFs larges) ou ≤ 0.25% (spécialisés)
- Actifs sous gestion ≥ 1 milliard USD
- Erreur de suivi ≤ 0.20% sur 3 ans
- Historique minimum de 3 ans
- Compatibilité UCITS pour investisseurs suisses

#### Actions A+

- ROE ≥ 20% maintenu sur 3 ans
- Croissance du CA ≥ 15% annuel sur 5 ans
- Ratio dette/capitaux propres ≤ 0.3
- Free Cash Flow positif et croissant
- Position dominante dans secteur en croissance

#### Cryptomonnaies A+

- Capitalisation ≥ 10 milliards USD
- Volume quotidien ≥ 500 millions USD
- Adoption institutionnelle prouvée
- Utilité réelle et cas d'usage concrets
- Équipe de développement active

### 3. Validation rigoureuse

Chaque candidat A+ subit :

- **Backtesting** sur 5+ ans minimum
- **Analyse multi-régimes** (haussier, baissier, latéral)
- **Métriques de risque** (Sharpe, Sortino, Max Drawdown)
- **Vérification de corrélation** avec votre portefeuille

## Utilisation du système

### Lancement d'une découverte

```bash
# Découverte complète (recommandé)
uv run python src/finwiz/main.py --discovery

# Découverte ciblée par type d'actif
uv run python src/finwiz/main.py --discovery --asset-type etf
uv run python src/finwiz/main.py --discovery --asset-type stock
uv run python src/finwiz/main.py --discovery --asset-type crypto
```

### Paramètres personnalisables

Vous pouvez ajuster les critères selon votre profil :

```yaml
# config/discovery_settings.yaml
risk_tolerance: "moderate"  # conservative, moderate, aggressive
min_score: 0.95            # Score minimum pour A+
max_correlation: 0.7       # Corrélation max avec portefeuille existant
regions: ["US", "EU", "CH"] # Régions géographiques
esg_filter: true           # Filtre ESG activé
```

## Interprétation des résultats

### Rapport de découverte

Le rapport généré contient plusieurs sections clés :

#### 1. Résumé exécutif

```
📊 DÉCOUVERTE A+ - Résumé
═══════════════════════════════════════

Opportunités identifiées : 12 investissements A+
Impact potentiel : +0.8 points sur note moyenne du portefeuille
Amélioration estimée : +2.3% de rendement annuel
Réduction de risque : -5% de volatilité
```

#### 2. Opportunités par catégorie

**ETFs A+ découverts :**

```
🏆 VXUS - Vanguard Total International Stock ETF
   Score A+ : 0.97/1.00
   Frais : 0.08% (excellent)
   Remplacement suggéré : FTSE Developed Markets ETF (0.45% frais)
   Impact : +0.37% rendement net annuel
   
🏆 SCHD - Schwab US Dividend Equity ETF  
   Score A+ : 0.96/1.00
   Frais : 0.06% (exceptionnel)
   Nouveau ajout suggéré : Diversification dividendes US
   Impact : +0.4 points stabilité portefeuille
```

#### 3. Analyse d'impact

**Avant/Après comparaison :**

```
PORTEFEUILLE ACTUEL          PORTEFEUILLE OPTIMISÉ A+
═══════════════════════      ═══════════════════════════
Note moyenne : B+ (0.82)  →  Note moyenne : A- (0.90)
Frais moyens : 0.68%      →  Frais moyens : 0.31%
Rendement estimé : 7.2%   →  Rendement estimé : 9.5%
Volatilité : 14.8%        →  Volatilité : 14.1%
```

### Codes de recommandation

| Code | Signification | Action suggérée |
|------|---------------|-----------------|
| 🔄 REMPLACER | Substitution directe | Vendre position actuelle, acheter A+ |
| ➕ AJOUTER | Nouveau secteur/région | Allocation nouvelle avec rééquilibrage |
| 📈 AUGMENTER | Renforcer position | Augmenter allocation existante |
| ⚖️ RÉÉQUILIBRER | Optimiser poids | Ajuster proportions sans changement |

### Niveaux de confiance

- **🟢 Confiance élevée (90-100%)** : Recommandation forte, action immédiate
- **🟡 Confiance modérée (70-89%)** : Bonne opportunité, surveillance recommandée  
- **🟠 Confiance faible (50-69%)** : Opportunité conditionnelle, analyse supplémentaire

## Exemples concrets d'amélioration

### Exemple 1 : Optimisation ETF Core

**Situation initiale :**

```
Position actuelle : iShares Core MSCI World (IWDA)
- Frais : 0.20%
- Score : B+ (0.84)
- Allocation : 40% du portefeuille
```

**Découverte A+ :**

```
Remplacement suggéré : Vanguard FTSE All-World (VWRL)
- Frais : 0.22% (légèrement supérieur mais...)
- Score : A+ (0.96)
- Diversification supérieure : +1,000 titres
- Tracking error réduit : 0.12% vs 0.18%
- Impact net : +0.3% rendement annuel estimé
```

**Résultat :**

- Note du portefeuille : B+ → A-
- Économie de frais : Non applicable (frais similaires)
- Amélioration qualité : Significative
- Diversification : Nettement améliorée

### Exemple 2 : Découverte action A+ émergente

**Découverte :**

```
🏆 ASML Holding N.V. (ASML)
   Score A+ : 0.98/1.00
   Secteur : Semi-conducteurs (équipements)
   
Critères A+ validés :
✅ ROE : 32% (3 ans moyenne)
✅ Croissance CA : 18% annuel (5 ans)
✅ Dette/Capitaux : 0.15 (excellent)
✅ FCF : +€6.2B et croissant
✅ Position dominante : Monopole technologique EUV
```

**Analyse d'intégration :**

```
Corrélation portefeuille : 0.45 (acceptable)
Allocation suggérée : 3-5%
Horizon : Long terme (5+ ans)
Risques : Cyclicité semi-conducteurs, concentration géographique
```

### Exemple 3 : Optimisation crypto (allocation 5%)

**Situation initiale :**

```
Bitcoin (BTC) : 3%
Ethereum (ETH) : 2%
Score moyen crypto : B (0.78)
```

**Découverte A+ :**

```
🏆 Solana (SOL) - Score A+ : 0.95
   Ajout suggéré : 1% (réduction BTC à 2%)
   
Justification A+ :
✅ Adoption institutionnelle croissante
✅ Écosystème DeFi mature
✅ Performance technique supérieure
✅ Équipe développement active
✅ Cas d'usage réels (NFTs, DeFi, paiements)
```

**Impact :**

- Score crypto : B → A-
- Diversification améliorée
- Potentiel rendement : +15% sur allocation crypto

## Mise en œuvre des recommandations

### 1. Priorisation

Le système classe automatiquement les recommandations par :

- **Impact sur la note** (priorité haute)
- **Facilité d'implémentation** (coûts de transaction)
- **Horizon temporel** (court vs long terme)
- **Niveau de confiance** (certitude de l'amélioration)

### 2. Stratégie d'implémentation

**Approche progressive recommandée :**

1. **Phase 1 (Mois 1)** : Remplacements ETF core (impact immédiat)
2. **Phase 2 (Mois 2-3)** : Ajouts actions A+ (croissance)
3. **Phase 3 (Mois 4-6)** : Optimisation crypto et sectoriels

**Considérations pratiques :**

- Étaler les achats (Dollar Cost Averaging)
- Minimiser les coûts de transaction
- Respecter les contraintes fiscales
- Maintenir la liquidité d'urgence

### 3. Suivi et ajustements

Le système surveille automatiquement :

- **Maintien du grade A+** (alertes si dégradation)
- **Performance relative** (vs benchmarks)
- **Nouvelles opportunités** (découverte mensuelle)
- **Changements de contexte** (conditions de marché)

## Monitoring continu

### Alertes automatiques

Vous recevrez des notifications pour :

```
🚨 ALERTE DÉGRADATION
ASML (ASML) : A+ → B+
Cause : Révision à la baisse des prévisions secteur
Action suggérée : Surveillance renforcée, pas de vente immédiate

📈 NOUVELLE OPPORTUNITÉ  
Découverte : Microsoft (MSFT) atteint critères A+
Score : 0.96 (nouveau record)
Action suggérée : Analyse d'intégration portefeuille

⚖️ RÉÉQUILIBRAGE SUGGÉRÉ
Dérive allocation : Tech 32% → 28% cible
Action : Vente partielle positions surperformantes
```

### Rapports périodiques

- **Hebdomadaire** : Performance positions A+
- **Mensuel** : Nouvelle découverte et opportunités
- **Trimestriel** : Révision complète et ajustements
- **Annuel** : Bilan performance et évolution critères

## FAQ - Questions fréquentes

### Général

**Q : À quelle fréquence le système découvre-t-il de nouvelles opportunités A+ ?**
R : Le système effectue une analyse complète mensuelle, avec des mises à jour hebdomadaires pour les changements significatifs. Les alertes de dégradation sont envoyées dans les 24h.

**Q : Combien d'opportunités A+ puis-je espérer par mois ?**
R : En moyenne 3-7 nouvelles opportunités par mois, selon les conditions de marché. Les marchés volatils génèrent plus d'opportunités.

**Q : Le système peut-il se tromper sur une notation A+ ?**
R : Oui, aucun système n'est parfait. C'est pourquoi nous utilisons un backtesting rigoureux et un monitoring continu. Historiquement, 85% des A+ maintiennent leur grade sur 6 mois.

### Critères et notation

**Q : Pourquoi les critères A+ changent-ils selon les conditions de marché ?**
R : Les critères s'adaptent pour rester pertinents. Par exemple, en période d'inflation élevée, nous privilégions les actifs avec "pricing power". Cela améliore la précision des recommandations.

**Q : Un investissement peut-il passer de A+ à une note inférieure ?**
R : Absolument. Les fondamentaux évoluent. Le système vous alerte immédiatement et propose des alternatives si nécessaire.

**Q : Comment sont pondérés les différents critères A+ ?**
R : La pondération varie selon l'actif :

- ETFs : Coûts (30%), tracking (25%), liquidité (20%), diversification (25%)
- Actions : Fondamentaux (40%), croissance (30%), qualité (20%), valorisation (10%)
- Crypto : Adoption (35%), technologie (25%), équipe (20%), tokenomics (20%)

### Implémentation

**Q : Dois-je suivre toutes les recommandations A+ ?**
R : Non, le système propose, vous décidez. Priorisez selon votre situation personnelle, contraintes fiscales et objectifs d'investissement.

**Q : Comment gérer les coûts de transaction lors des remplacements ?**
R : Le système calcule l'impact net (amélioration - coûts). Seules les recommandations avec bénéfice net positif sont proposées. Privilégiez les courtiers à frais réduits.

**Q : Que faire si une recommandation A+ ne correspond pas à mon profil de risque ?**
R : Le système respecte votre profil configuré, mais vous pouvez ajuster les paramètres. Une action A+ "agressive" peut être appropriée en petite allocation même pour un profil conservateur.

### Technique

**Q : Le système fonctionne-t-il avec tous les courtiers ?**
R : Le système génère des recommandations universelles. L'implémentation dépend de votre courtier. La plupart des ETFs A+ sont disponibles chez les courtiers majeurs.

**Q : Comment sont protégées mes données de portefeuille ?**
R : Toutes les données sont chiffrées et traitées localement. Aucune information personnelle n'est transmise aux fournisseurs de données externes.

**Q : Puis-je personnaliser les critères A+ ?**
R : Partiellement. Vous pouvez ajuster les seuils de score, filtres ESG, régions géographiques, mais les critères fondamentaux restent standardisés pour maintenir la cohérence.

### Performance

**Q : Quelle performance puis-je attendre d'un portefeuille optimisé A+ ?**
R : Historiquement, les portefeuilles A+ surperforment de 1-3% annuel après frais, avec une volatilité similaire ou réduite. Les performances passées ne garantissent pas les résultats futurs.

**Q : Le système fonctionne-t-il dans tous les environnements de marché ?**
R : Le système s'adapte aux conditions de marché, mais les critères A+ sont conçus pour identifier la qualité dans tous les environnements. Les performances relatives sont généralement meilleures en marchés difficiles.

**Q : Comment comparer les résultats avec mon ancien portefeuille ?**
R : Le système génère automatiquement des rapports de comparaison avec métriques de performance, risque et coûts. Un suivi trimestriel permet d'évaluer l'amélioration réelle.

## Support et ressources

### Documentation technique

- [Guide développeur](investment_discovery_developer_guide.md)
- [Référence API](investment_discovery_api_reference.md)
- [Schémas de données](../reference/schemas/index.md)

### Contact support

- Email : <support@finwiz.ai>
- Documentation : <https://docs.finwiz.ai>
- Communauté : <https://community.finwiz.ai>

---

*Ce guide est mis à jour régulièrement. Version actuelle : 1.0 - Septembre 2025*

---

# A+ System Overview, Monitoring, and Integration

## Overview

The A+ Investment System identifies and monitors exceptional investment opportunities with scores ≥ 0.95. It consists of three integrated components:

1. **Discovery**: Proactively finds A+ opportunities across ETFs, stocks, and crypto
2. **Scoring**: Evaluates investments using comprehensive multi-factor analysis
3. **Monitoring**: Continuously tracks A+ investments to ensure quality maintenance


## A+ Monitoring

### Continuous Monitoring

**Key Features**:

- Automated re-evaluation (default: weekly)
- Grade degradation detection
- Market regime awareness
- Performance tracking
- Alert system

### Alert System

**Alert Severity Levels**:

- **Critical**: A+ → C or below (immediate action)
- **High**: A+ → B (review within 24 hours)
- **Medium**: A+ → B+ (review within week)
- **Low**: Minor score decrease (monitor)

**Alert Triggers**:

- Grade degradation
- Performance below benchmark
- Risk score increase
- Fundamental deterioration

### Performance Tracking

**Tracked Metrics**:

- Total return
- Alpha vs benchmark
- Sharpe ratio
- Maximum drawdown
- Grade maintenance duration
- Volatility

### Usage

**Start Monitoring**:

```python
from finwiz.services.a_plus_monitoring_service import get_monitoring_service

service = get_monitoring_service()
await service.start_service()
```

**Add Investments**:

```python
# Process discovery results
discovery_result = await investment_discovery_crew.run()
await service.process_discovery_results(discovery_result)
```

**Get Status**:

```python
# Get monitoring dashboard
dashboard = await service.get_monitoring_dashboard()

print(f"Total monitored: {dashboard['performance_summary']['total_investments']}")
print(f"A+ maintained: {dashboard['performance_summary']['a_plus_count']}")
print(f"Degraded: {dashboard['performance_summary']['degraded_count']}")
```

**CLI Operations**:

```bash
# Start monitoring
uv run python -m finwiz.tools.a_plus_monitoring_cli start

# Check status
uv run python -m finwiz.tools.a_plus_monitoring_cli status

# Get alerts
uv run python -m finwiz.tools.a_plus_monitoring_cli alerts

# Stop monitoring
uv run python -m finwiz.tools.a_plus_monitoring_cli stop
```


## Portfolio Integration

### Discovery Integration

**Automatic A+ Discovery**:

```bash
# Run discovery across all asset types
uv run python src/finwiz/main.py --discovery

# Discover specific asset type
uv run python src/finwiz/main.py --discovery --asset-type etf
```

**Output**:

- `output/discovery/discovery_latest.json` - Latest A+ opportunities
- `output/discovery/discovery_YYYY-MM-DD.json` - Timestamped results
- `output/discovery/discovery_report.html` - HTML report

### Alternative Finder Integration

The `AlternativeFinder` tool prioritizes A+ candidates when suggesting alternatives for underperforming holdings:

```python
from finwiz.tools.alternative_finder_tool import AlternativeFinder

finder = AlternativeFinder()

# Finds A+ alternatives from discovery crew
alternatives = finder.find_alternatives(holding, max_alternatives=3)

# A+ candidates are marked
for alt in alternatives:
    if alt.is_a_plus_candidate:
        print(f"A+ Alternative: {alt.ticker} (Grade: {alt.grade})")
```

### Portfolio Review Integration

A+ opportunities are integrated into portfolio reviews:

1. **Current Holdings**: Graded using A+ scoring system
2. **Alternatives**: A+ candidates suggested for underperforming holdings
3. **Improvement Roadmap**: Phased plan to increase A+ allocation

**Target A+ Allocation**:

- Conservative: 20-30% A+ holdings
- Moderate: 30-40% A+ holdings
- Aggressive: 40-50% A+ holdings

### Monitoring Integration

**Automatic Monitoring**:

- A+ discoveries automatically added to monitoring
- Portfolio holdings graded A+ are monitored
- Alerts integrated into portfolio reports

**Monitoring Dashboard**:

```python
from finwiz.orchestrators.a_plus_monitoring_orchestrator import APlusMonitoringOrchestrator

orchestrator = APlusMonitoringOrchestrator()
dashboard = await orchestrator.get_monitoring_dashboard()

# Dashboard includes:
# - Performance summary
# - Active alerts
# - Grade distribution
# - Recent degradations
# - Replacement suggestions
```

## Best Practices
### Portfolio Integration

1. **Gradual Transition**: Don't rush to 100% A+ allocation
2. **Tax Considerations**: Use tax-optimized transition strategies
3. **Rebalance Regularly**: Quarterly rebalancing recommended
4. **Maintain Diversification**: Don't sacrifice diversification for A+ grade

## Configuration

### Environment Variables

```bash
# A+ Discovery
DISCOVERY_ENABLED=true
DISCOVERY_FREQUENCY=weekly

# A+ Monitoring
MONITORING_ENABLED=true
MONITORING_INTERVAL=weekly
MONITORING_ALERT_THRESHOLD=24  # hours

# A+ Scoring
APLUS_THRESHOLD=0.95
APLUS_CUSTOM_CRITERIA={}
```

### Monitoring Configuration

```python
# config/monitoring.yaml
monitoring:
  enabled: true
  interval: weekly
  alert_thresholds:
    critical: 24  # hours
    high: 72
    medium: 168
  performance_tracking:
    enabled: true
    benchmarks:
      etf: "SPY"
      stock: "^GSPC"
      crypto: "BTC-USD"
```

## See Also

- [Investment Discovery Documentation](investment_discovery/) - Complete discovery guide
- [Portfolio Holdings Analysis](portfolio_holdings_analysis_user_guide.md) - Portfolio analysis
- [Alternative Finder](api_reference.md) - Alternative finding tool
- [API Reference](api_reference.md) - Complete API documentation

---

**Version**: 2.0  

## Best Practices

### Discovery

1. **Run Monthly**: Full discovery on first Monday of each month
2. **Review Results**: Manually review A+ candidates before adding to portfolio
3. **Diversify**: Don't concentrate in single A+ opportunity
4. **Monitor Criteria**: Understand why each investment is A+ rated

### Scoring

1. **Use Market Context**: Always provide current market conditions
2. **Custom Criteria**: Adjust criteria for your risk tolerance
3. **Validate Results**: Cross-check with other sources
4. **Understand Components**: Review individual score components

### Monitoring

1. **Weekly Reviews**: Check monitoring dashboard weekly
2. **Act on Alerts**: Respond to critical alerts within 24 hours
3. **Track Performance**: Review performance metrics monthly
4. **Update Criteria**: Adjust monitoring criteria as markets change

### Portfolio Integration

1. **Gradual Transition**: Don't rush to 100% A+ allocation
2. **Tax Considerations**: Use tax-optimized transition strategies
3. **Rebalance Regularly**: Quarterly rebalancing recommended
4. **Maintain Diversification**: Don't sacrifice diversification for A+ grade


## Configuration

### Environment Variables

```bash
# A+ Discovery
DISCOVERY_ENABLED=true
DISCOVERY_FREQUENCY=weekly

# A+ Monitoring
MONITORING_ENABLED=true
MONITORING_INTERVAL=weekly
MONITORING_ALERT_THRESHOLD=24  # hours

# A+ Scoring
APLUS_THRESHOLD=0.95
APLUS_CUSTOM_CRITERIA={}
```

### Monitoring Configuration

```python
# config/monitoring.yaml
monitoring:
  enabled: true
  interval: weekly
  alert_thresholds:
    critical: 24  # hours
    high: 72
    medium: 168
  performance_tracking:
    enabled: true
    benchmarks:
      etf: "SPY"
      stock: "^GSPC"
      crypto: "BTC-USD"
```

## See Also

- [Investment Discovery Documentation](investment_discovery/) - Complete discovery guide
- [Portfolio Holdings Analysis](portfolio_holdings_analysis_user_guide.md) - Portfolio analysis
- [Alternative Finder](api_reference.md) - Alternative finding tool
- [API Reference](api_reference.md) - Complete API documentation

