# Code Snippets Guide

Guide pour importer des extraits de code source dans la documentation.

## Utilisation de pymdownx.snippets

Le plugin `pymdownx.snippets` est déjà activé et permet d'importer du code depuis les fichiers source.

### Syntaxe de base

```markdown
--8<-- "src/finwiz/tools/portfolio_price_service.py"
```

Cela importe tout le fichier avec coloration syntaxique automatique.

> **Note** : l'outil Yahoo Finance lui-même vit désormais dans le paquet
> central `crewai_custom_tools` (`YahooFinanceTickerInfoTool`), et non plus
> dans `src/finwiz/tools/`. Pour illustrer un extrait de code source du
> dépôt, préférez un fichier qui existe réellement dans `src/finwiz/`, comme
> `portfolio_price_service.py` qui consomme cet outil.

### Importer des lignes spécifiques

```markdown
--8<-- "src/finwiz/tools/portfolio_price_service.py:1:20"
```

Importe les lignes 10 à 25 du fichier.

### Importer plusieurs extraits

```markdown
--8<-- "src/finwiz/schemas/common.py:1:10"
--8<-- "src/finwiz/schemas/common.py:50:60"
```

### Avec bloc de code explicite

```markdown
```python
--8<-- "src/finwiz/tools/portfolio_price_service.py:1:20"
\```
```

## Avantages

✅ **Code toujours à jour** - Reflète automatiquement les changements du code source
✅ **Pas de duplication** - Une seule source de vérité
✅ **Maintenance facile** - Pas besoin de copier-coller manuellement
✅ **Coloration syntaxique** - Détection automatique du langage

## Exemples d'utilisation

### Documenter une fonction

```markdown
## Fonction analyze_stock

Voici l'implémentation complète:

```python
--8<-- "src/finwiz/crews/stock_crew/stock_crew.py:45:75"
\```
```

### Documenter un schéma Pydantic

```markdown
## Schéma TenKInsight

```python
--8<-- "src/finwiz/schemas/stock.py:11:27"
\```
```

## Configuration

La configuration dans `mkdocs.yml`:

```yaml
markdown_extensions:
  - pymdownx.snippets:
      auto_append:
        - includes/abbreviations.md
```

## Documentation officielle

- [PyMdown Extensions - Snippets](https://facelessuser.github.io/pymdown-extensions/extensions/snippets/)
- [Material for MkDocs - Code blocks](https://squidfunk.github.io/mkdocs-material/reference/code-blocks/)

---

**Version**: 1.0
**Last Updated**: 2025-11-01
