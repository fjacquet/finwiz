# Plan d'Amélioration Technique FinWiz

**Date**: 2025-12-30
**État actuel**: Post-refactoring Phase 1-5

---

## Résumé de la Dette Technique

| Métrique | Valeur Actuelle | Cible | Écart |
|----------|-----------------|-------|-------|
| Couverture de tests | 61% | 65% | -4% |
| Erreurs Mypy | 1,895 | 0 | -1,895 |
| Fichiers >300 lignes | ~20 | 0 | -20 |
| Fichiers >600 lignes | 10 | 0 | -10 |
| Issues Bandit (high) | 0 | 0 | ✅ |
| Issues Vulture | 0 | 0 | ✅ |
| Issues Ruff | 0 | 0 | ✅ |

---

## Phase 6: Couverture de Tests (+4%)

**Objectif**: Atteindre 65% de couverture

### Priorité 1: Modules Non Couverts

```bash
# Identifier les fichiers avec couverture < 50%
uv run pytest --cov=src/finwiz --cov-report=html
# Consulter htmlcov/index.html
```

### Actions

| Module | Couverture Estimée | Tests à Ajouter |
|--------|-------------------|-----------------|
| `orchestrators/deep_analysis_*.py` | ~40% | Tests d'intégration |
| `flows/hybrid_*.py` | ~35% | Tests de flux |
| `tools/quantitative_*.py` | ~50% | Tests unitaires |
| `supabase/client_*.py` | ~30% | Mocks Supabase |

### Commandes

```bash
# Tester un module spécifique avec couverture
uv run pytest tests/unit/orchestrators/ --cov=src/finwiz/orchestrators --cov-report=term-missing

# Générer rapport HTML
uv run pytest --cov=src/finwiz --cov-report=html
```

---

## Phase 7: Type Hints (Mypy)

**Objectif**: Réduire les erreurs mypy de 1,895 à <500

### Stratégie Progressive

1. **Semaine 1-2**: Corriger les modules critiques (orchestrators, flows)
2. **Semaine 3-4**: Corriger les modules quantitatifs
3. **Semaine 5-6**: Corriger les utilitaires et outils

### Fichiers Prioritaires (par nombre d'erreurs)

```bash
# Identifier les fichiers avec le plus d'erreurs
uv run mypy src/finwiz --ignore-missing-imports 2>&1 | grep "error:" | cut -d: -f1 | sort | uniq -c | sort -rn | head -20
```

### Patterns Communs à Corriger

```python
# Pattern 1: Optional types
# Avant
def process(data):
    ...
# Après
def process(data: dict[str, Any] | None) -> dict[str, Any]:
    ...

# Pattern 2: Return types
# Avant
def get_result():
    return {"score": 0.85}
# Après
def get_result() -> dict[str, float]:
    return {"score": 0.85}

# Pattern 3: Class attributes
# Avant
class Analyzer:
    def __init__(self):
        self.cache = {}
# Après
class Analyzer:
    cache: dict[str, Any]

    def __init__(self) -> None:
        self.cache = {}
```

---

## Phase 8: Découpage des Fichiers Restants

**Objectif**: Tous les fichiers < 300 lignes

### Fichiers à Découper (>500 lignes)

| Fichier | Lignes | Stratégie de Découpage |
|---------|--------|------------------------|
| `supabase/utils/monitoring.py` | 681 | Base + Metrics + Alerts |
| `orchestrators/reporting_orchestrator.py` | 649 | Sections + Renderers |
| `tools/portfolio_holdings_html_generator.py` | 617 | Sections + Templates |
| `tools/standardized_sentiment_tool.py` | 612 | Analyzers + Formatters |
| `tools/perplexity_analysis_integration.py` | 611 | Client + Processors |
| `tools/notification_service.py` | 610 | Channels + Formatters |
| `quantitative/rebalancing_history_tracker.py` | 599 | Storage + Analysis |
| `tools/enhanced_sec_tool.py` | 581 | Extractors + Parsers |
| `tools/backtesting_tool.py` | 578 | Engine + Reporters |
| `utils/batch_data_prefetcher.py` | 578 | Fetchers + Coordinators |

### Template de Découpage

```
fichier_original.py (600 lignes)
├── fichier_core.py (~200 lignes)     # Logique métier principale
├── fichier_helpers.py (~150 lignes)  # Fonctions utilitaires
└── fichier_models.py (~100 lignes)   # Classes de données
```

---

## Phase 9: Qualité de Code Avancée

### 9.1 Documentation

- [ ] Docstrings manquantes (pydocstyle)
- [ ] README par module
- [ ] Diagrammes d'architecture (Mermaid)

### 9.2 Complexité Cyclomatique

```bash
# Identifier les fonctions trop complexes
uv run radon cc src/finwiz -a -s
```

### 9.3 Dépendances Circulaires

```bash
# Détecter les imports circulaires
uv run pydeps src/finwiz --cluster
```

---

## Phase 10: Sécurité

### Issues Bandit Restantes

| Sévérité | Nombre | Action |
|----------|--------|--------|
| High | 0 | ✅ Résolu |
| Medium | 3 | Pickle pour cache local - acceptable |
| Low | 66 | Évaluer cas par cas |

### Actions Recommandées

1. **Pickle (Medium)**: Documenter que c'est pour cache local uniquement
2. **assert statements (Low)**: Remplacer par exceptions explicites
3. **subprocess (Low)**: Vérifier les inputs non sanitizés

---

## Calendrier Proposé

| Phase | Durée | Priorité | Impact |
|-------|-------|----------|--------|
| Phase 6: Tests +4% | 1 semaine | HAUTE | Stabilité |
| Phase 7: Mypy | 2-3 semaines | MOYENNE | Maintenabilité |
| Phase 8: Fichiers | 2 semaines | MOYENNE | Lisibilité |
| Phase 9: Qualité | Continu | BASSE | Excellence |
| Phase 10: Sécurité | 1 semaine | BASSE | Conformité |

---

## Métriques de Suivi

### Commandes de Vérification

```bash
# Qualité globale
make check                    # Lint + Tests + Docs

# Métriques détaillées
uv run pytest --cov=src/finwiz --cov-fail-under=65  # Couverture
uv run mypy src/finwiz --ignore-missing-imports      # Types
uv run ruff check src/finwiz                         # Lint
uv run vulture src/finwiz --min-confidence 100       # Dead code
uv run bandit -r src/finwiz -ll                      # Sécurité

# Taille des fichiers
find src/finwiz -name "*.py" -exec wc -l {} + | sort -n | tail -20
```

### Dashboard de Santé

```
┌─────────────────────────────────────────────────────┐
│ FinWiz Code Health Dashboard                        │
├─────────────────────────────────────────────────────┤
│ Tests:     3233 passed ✅  │ Coverage:  61% ⚠️     │
│ Lint:      0 errors ✅     │ Types:     1895 ❌    │
│ Security:  0 high ✅       │ Files>300: ~20 ⚠️     │
│ Dead Code: 0 issues ✅     │                        │
└─────────────────────────────────────────────────────┘
```

---

## Ressources

- CLAUDE.md - Guide de développement (racine projet)
- CHANGELOG.md - Historique des changements (racine projet)
- pyproject.toml - Configuration des outils (racine projet)
- Makefile - Commandes disponibles
