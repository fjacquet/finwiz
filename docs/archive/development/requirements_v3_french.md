# Document d'Exigences Maître : Architecture Hybride FinWiz (v3.0)

**Objectif :** Définir une architecture performante, fiable et maintenable en combinant un moteur Python déterministe pour l'analyse de portefeuille avec des Crews IA spécialisées pour la découverte.

**Architecture Cible :** Hybride (Option A)

- **Moteur d'Analyse (Calculs) :** 100% Python (`PortfolioDeepAnalyzer`, `DeepAnalysisScorer`).
- **Moteur de Découverte (Raisonnement) :** Crews IA (`InvestmentDiscoveryCrew`, `Perplexity`).
- **Persistance (Cache & RAG) :** Supabase (PostgreSQL + `pgvector`).
- **Flux de Données :** Exports JSON explicites vers `output/`.
- **Reporting & Consolidation :** 100% Python (Fonctions pures + Jinja2).

---

## 1. 🚀 Phase 1 : Exigences Fondamentales (Bloqueurs P0)

*Objectif : Réparer la fondation technique (base de données et flux de données) pour débloquer toutes les autres fonctionnalités.*

### 1.1. Réparation et Intégration de Supabase (Cache & RAG)

*Raison d'être : Le Cache (performance) et le RAG (contexte IA) dépendent tous deux de Supabase, qui est actuellement en échec (100% de timeouts).*

**Story 1.1.1 : Diagnostiquer et Établir une Connexion Fiable**
*En tant que Développeur, je veux un script de diagnostic pour isoler et corriger la cause racine des timeouts de Supabase.*

- **AC 1.1.1.1 :** Créer un script `scripts/diagnose_supabase.py` (autonome) qui tente une connexion et une requête `SELECT 1`.
- **AC 1.1.1.2 :** Le script DOIT utiliser les variables d'environnement (`SUPABASE_URL`, `SUPABASE_KEY`) et un timeout explicite (10s).
- **AC 1.1.1.3 :** Le script DOIT logger l'erreur exacte (ex: `TimeoutError`, `AuthenticationError`).
- **AC 1.1.1.4 :** La configuration réseau (Firewall Supabase, DNS) ou les clés DOIVENT être corrigées jusqu'à ce que le script réussisse.

**Story 1.1.2 : Implémenter un Disjoncteur (Circuit Breaker) Résilient**
*En tant qu'Architecte, je veux que FinWiz continue de fonctionner si Supabase tombe en panne, sans jamais ralentir l'utilisateur.*

- **AC 1.1.2.1 :** Créer une classe singleton `SupabaseManager` qui encapsule TOUTES les interactions avec la base de données.
- **AC 1.1.2.2 :** Le manager DOIT implémenter un état (OUVERT, FERMÉ, MI-OUVERT).
- **AC 1.1.2.3 :** **Seuil d'Échec :** 3 échecs consécutifs (ex: timeouts) FONT PASSER l'état à `OUVERT`.
- **AC 1.1.2.4 :** **État `OUVERT` :** Tous les appels (ex: `get_from_cache`) échouent *instantanément* (retournent `None`) sans tentative de connexion réseau.
- **AC 1.1.2.5 :** **Délai de Réinitialisation :** L'état reste `OUVERT` pendant 5 minutes.
- **AC 1.1.2.6 :** **État `MI-OUVERT` :** Après 5 minutes, le prochain appel est autorisé. S'il réussit, l'état passe à `FERMÉ`. S'il échoue, l'état repasse à `OUVERT`.
- **AC 1.1.2.7 :** Des logs clairs (`CRITICAL: Supabase Circuit Breaker OPENED`) DOIVENT être émis lors des changements d'état.

**Story 1.1.3 : Activer le Cache de Contenu (Lecture)**
*En tant qu'Utilisateur, je veux des analyses quasi-instantanées si les données ont été calculées récemment.*

- **AC 1.1.3.1 :** Définir la table `analysis_cache` (champs: `cache_key`, `ticker`, `analysis_json`, `created_at`).
- **AC 1.1.3.2 :** Implémenter `SupabaseManager.get_from_cache(cache_key)`.
- **AC 1.1.3.3 :** La lecture DOIT avoir un timeout strict de **2 secondes**.
- **AC 1.1.3.4 :** La fonction DOIT retourner `None` si le disjoncteur est `OUVERT`, si la lecture time out, ou si l'enregistrement n'est pas trouvé.
- **AC 1.1.3.5 :** **TTL (Time-To-Live) :** La fonction DOIT retourner `None` si `(now() - created_at) > 24 heures` (données périmées).
- **AC 1.1.3.6 :** Logger les statuts (`Cache HIT`, `Cache MISS`, `Cache STALE`).

**Story 1.1.4 : Activer le Cache de Contenu (Écriture Asynchrone)**
*En tant qu'Architecte, je veux que la sauvegarde des résultats n'ait AUCUN impact sur la performance perçue par l'utilisateur.*

- **AC 1.1.4.1 :** Implémenter `SupabaseManager.write_to_cache_async(cache_key, result_json)`.
- **AC 1.1.4.2 :** Cette fonction DOIT s'exécuter dans un **thread d'arrière-plan** (non bloquant). Le flux principal DOIT continuer immédiatement.
- **AC 1.1.4.3 :** L'écriture doit être un "upsert" (met à jour si `cache_key` existe, sinon crée).
- **AC 1.1.4.4 :** Les échecs d'écriture (timeout, disjoncteur ouvert) DOIVENT être *uniquement* loggués et NE DOIVENT JAMAIS interrompre le flux principal.

**Story 1.1.5 : Activer la Base Vectorielle (RAG)**
*En tant qu'Agent IA, j'ai besoin d'accéder aux analyses passées pour améliorer mes recommandations de découverte.*

- **AC 1.1.5.1 :** Activer l'extension `pgvector` et créer la table `analysis_embeddings` (champs: `analysis_cache_id`, `content_summary` (text), `embedding` (vector, 1536 dims)).
- **AC 1.1.5.2 :** Mettre à jour `write_to_cache_async` (Story 1.1.4) :
    1. *Après* l'écriture du cache, générer un résumé du `result_json`.
    2. Générer un embedding pour ce résumé via `text-embedding-3-small` (1536 dims).
    3. Sauvegarder l'embedding dans `analysis_embeddings`.
- **AC 1.1.5.3 :** Implémenter `SupabaseManager.search_rag_context(query_text)` (pour les Crews IA).
- **AC 1.1.5.4 :** La recherche RAG DOIT avoir un timeout strict de **3 secondes**.

---

### 1.2. Intégrité du Flux de Données (Exports JSON)

*Raison d'être : Corrige la cause racine de la perte de données (ex: Grade A+ devenant Grade D) en passant de la mémoire au fichier.*

**Story 1.2.1 : Standardiser les Exports JSON Validés**
*En tant que Développeur, je veux que tous les moteurs (Python et IA) exportent leurs résultats dans un format fiable et standardisé.*

- **AC 1.2.1.1 :** Tous les moteurs (Python Pur et Crews IA) DOIVENT exporter leurs résultats finaux dans un fichier `.json`.
- **AC 1.2.1.2 :** Cet export DOIT être validé par un schéma Pydantic strict (`extra='forbid'`) avant d'être écrit.
- **AC 1.2.1.3 :** Les fichiers DOIVENT être sauvegardés dans une structure de répertoires standardisée (`output/reports/{session_id}/{crew_name}/`).
- **AC 1.2.1.4 :** Ces fichiers JSON (et non la mémoire du flux) deviennent la **source de vérité** pour la consolidation.

---

### 1.3. Tolérance Zéro pour les Données Factices

*Raison d'être : La confiance de l'utilisateur est non négociable. Nous devons éliminer toutes les données de test, de remplissage et les hallucinations.*

**Story 1.3.1 : Éliminer les Valeurs Codées en Dur et les Hallucinations**
*En tant qu'Analyste Financier, je veux que chaque chiffre et chaque note dans mon rapport soit réel et traçable.*

- **AC 1.3.1.1 :** Éliminer à 100% les valeurs codées en dur ("hardcoded") pour les scores, notes (ex: fallback "Grade D"), ou métriques de risque.
- **AC 1.3.1.2 :** Éliminer à 100% les URLs factices (ex: "example.com", "test.com").
- **AC 1.3.1.3 :** Toute URL citée (ex: SEC EDGAR, sources de sentiment) DOIT être une URL réelle, fonctionnelle et vérifiable.
- **AC 1.3.1.4 :** Si une donnée (URL, score) est *réellement* indisponible, le rapport DOIT afficher "Non disponible" ou "N/A" et non une valeur inventée ou un ancien placeholder.
- **AC 1.3.1.5 :** Les scores de backtesting DOIVENT être complets (Sortino, Calmar, etc.) ou marqués "N/A", mais jamais omis ou remplis avec "Données non disponibles".

---
---

## 2. 💻 Phase 2 : Moteur "Pure Python" (Analyse de Portefeuille)

*Objectif : Mettre en œuvre l'architecture "PURE PYTHON FIRST" pour 90% du travail d'analyse, garantissant performance et fiabilité.*

### 2.1. Moteur d'Analyse (Scoring) Python

*Raison d'être : Remplacer l'analyse IA (lente, coûteuse) par du Python pur (rapide, gratuit, déterministe).*

**Story 2.1.1 : Remplacer la `DeepAnalysisCrew` (IA)**
*En tant qu'Architecte, je veux que l'analyse de portefeuille soit déterministe et 10-20x plus rapide.*

- **AC 2.1.1.1 :** L'ancienne `DeepAnalysisCrew` (IA) est OBSOLÈTE et SUPPRIMÉE pour l'analyse de portefeuille.
- **AC 2.1.1.2 :** L'analyse est désormais gérée par la classe Python `PortfolioDeepAnalyzer`.
- **AC 2.1.1.3 :** `PortfolioDeepAnalyzer` DOIT instancier et utiliser la classe `DeepAnalysisScorer` pour tous les calculs.

**Story 2.1.2 : Implémenter le `DeepAnalysisScorer`**
*En tant que Développeur, je veux une classe Python testable pour tous les calculs de scoring.*

- **AC 2.1.2.1 :** Le `DeepAnalysisScorer` DOIT implémenter la logique de calcul déterministe (formules Python) pour :
    1. Score Composite (ex: 40% fondamental + 30% technique + 30% risque).
    2. Note (A+ à F) basée sur des seuils de score (ex: A+ si >= 0.90).
    3. Recommandation (BUY/KEEP/SELL) basée sur des règles (ex: "BUY si Grade A et Risque <= 3.0").
- **AC 2.1.2.2 :** Les calculs DOIVENT utiliser les métriques réelles (volatilité, ROE, etc.) et non des valeurs codées en dur (Req 1.3.1).

**Story 2.1.3 : Implémenter le `PortfolioDeepAnalyzer`**
*En tant que Développeur, je veux un orchestrateur Python pour analyser l'ensemble du portefeuille.*

- **AC 2.1.3.1 :** Le `PortfolioDeepAnalyzer` DOIT charger TOUS les portefeuilles (ex: `stock.csv`, `etf.csv`, et `crypto.csv`).
- **AC 2.1.3.2 :** Pour chaque holding, il DOIT :
    1. Générer un `cache_key`.
    2. Tenter de lire depuis Supabase : `SupabaseManager.get_from_cache(cache_key)` (Story 1.1.3).
    3. **Si Cache MISS/STALE :** Exécuter les outils de collecte de données (ex: `QuantitativeAnalysisTool`), appliquer le `DeepAnalysisScorer` (Story 2.1.2), et générer le `result_json`.
    4. **Si Cache HIT :** Utiliser le `result_json` du cache.
    5. Sauvegarder le `result_json` dans un fichier JSON explicite (Req 1.2.1) dans `output/`.
    6. Lancer l'écriture asynchrone vers Supabase : `SupabaseManager.write_to_cache_async(cache_key, result_json)` (Story 1.1.4).
- **AC 2.1.3.3 :** L'analyse de 66 holdings DOIT être parallélisée (ex: `threading` ou `asyncio`) pour respecter les objectifs de performance (10-30 minutes max).

---

### 2.2. Consolidation (Python Pur)

*Raison d'être : Remplacer l'Aggregator Crew (IA) par une fonction Python simple et fiable.*

**Story 2.2.1 : Implémenter le Consolidateur Python**
*En tant que Développeur, je veux une fonction simple pour fusionner tous les résultats avant le reporting.*

- **AC 2.2.1.1 :** Créer une fonction Python pure (ex: `consolidate_all_results(flow_state)`).
- **AC 2.2.1.2 :** Cette fonction NE DOIT PAS être une Crew IA.
- **AC 2.2.1.3 :** Elle doit lire les *chemins* des fichiers JSON depuis l'état du flux (Flow state).
- **AC 2.2.1.4 :** Elle doit lire le contenu de chaque fichier JSON (`deep_analysis.json`, `discovery.json`, etc.) depuis `output/`.
- **AC 2.2.1.5 :** Elle doit fusionner toutes les données en un seul objet Python (dict) ou `consolidated.json`.

---

### 2.3. Génération des Rapports (Jinja2)

*Raison d'être : Standardiser la génération de rapports pour qu'elle soit instantanée, gratuite et cohérente.*

**Story 2.3.1 : Standardiser sur Jinja2**
*En tant qu'Architecte, je veux que Jinja2 soit le seul outil de génération de HTML.*

- **AC 2.3.1.1 :** **Jinja2** est le standard unique pour la génération de rapports HTML.
- **AC 2.3.1.2 :** L'utilisation de `bs4` pour la *génération* (Doc 7) est OBSOLÈTE (Jinja2 le remplace). `bs4` peut être utilisé pour le *parsing* si nécessaire.
- **AC 2.3.1.3 :** Toute génération de rapport par IA est OBSOLÈTE et SUPPRIMÉE.

**Story 2.3.2 : Implémenter le `PythonReportGenerator`**
*En tant que Développeur, je veux une classe testable pour transformer les données JSON en rapport HTML.*

- **AC 2.3.2.1 :** Créer une classe `PythonReportGenerator` qui charge les templates `.j2` de Jinja2.
- **AC 2.3.2.2 :** La classe doit avoir une méthode `generate_report(data)` qui prend l'objet consolidé (de Story 2.2.1) en entrée.
- **AC 2.3.2.3 :** Le template DOIT être en **français** et respecter les standards de qualité (responsive, mode clair/sombre, emojis).
- **AC 2.3.2.4 :** Le rapport HTML final (ex: `final_report.html`) est la sortie.

---
---

## 3. 🧠 Phase 3 : Moteur "IA" (Découverte & Recherche)

*Objectif : Conserver l'IA pour les tâches de haut niveau (raisonnement, recherche, créativité) où elle excelle.*

### 3.1. Crews de Découverte (IA)

*Raison d'être : Utiliser l'IA pour trouver de *nouvelles* opportunités, une tâche non déterministe.*

**Story 3.1.1 : Conserver les Crews de Découverte IA**
*En tant qu'Investisseur, je veux que l'IA trouve des opportunités A+ que je ne connais pas.*

- **AC 3.1.1.1 :** Les crews IA (`InvestmentDiscoveryCrew`, `StockCrew`, `ETFCrew`, `CryptoCrew`) sont CONSERVÉES pour leur rôle de **Découverte de *nouvelles* opportunités**.
- **AC 3.1.1.2 :** Leur rôle d'analyse de portefeuille *existant* est OBSOLÈTE (transféré à la Phase 2).
- **AC 3.1.1.3 :** Ces crews DOIVENT exporter leurs résultats au format JSON (Req 1.2.1).

---

### 3.2. Intégration du RAG (IA + Supabase)

*Raison d'être : Améliorer la qualité des recommandations IA en leur donnant un contexte historique.*

**Story 3.2.1 : Connecter le RAG aux Crews de Découverte**
*En tant qu'Agent IA, je veux savoir ce que le système a déjà analysé pour affiner mes nouvelles découvertes.*

- **AC 3.2.1.1 :** Les Crews de Découverte (IA) (Story 3.1.1) DOIVENT être équipées d'un outil qui appelle `SupabaseManager.search_rag_context()` (Story 1.1.5).
- **AC 3.2.1.2 :** Le RAG (contexte historique) est injecté dans le prompt de l'agent IA pour améliorer ses recommandations.
- **AC 3.2.1.3 :** Cette fonctionnalité est conditionnée au succès de la Story 1.1.

---

### 3.3. Outils de Recherche Avancée (IA)

*Raison d'être : Permettre aux agents IA d'accéder à des informations fraîches du web.*

**Story 3.3.1 : Fournir des Outils de Recherche Web aux Crews IA**
*En tant qu'Agent IA, j'ai besoin de connaître les nouvelles du marché pour fonder mes découvertes.*

- **AC 3.3.1.1 :** Les Crews de Découverte (IA) DOIVENT avoir accès à des outils de recherche externes (ex: `PerplexityTool`, `TavilyTool`, `GoogleSearchTool`).
- **AC 3.3.1.2 :** Ces outils sont utilisés pour trouver des signaux de marché récents, des tendances, et des données non structurées.

---
---

## 4. 🛡️ Phase 4 : Exigences Transverses (Qualité & Résilience)

*Objectif : Assurer que l'ensemble du système est stable, testable et de haute qualité.*

### 4.1. Tests et Qualité du Code

*Raison d'être : Une base de code saine est nécessaire pour une livraison fiable.*

**Story 4.1.1 : Standardiser les Tests sur `pytest-mock`**
*En tant que Développeur, je veux un seul standard de mocking pour simplifier l'écriture des tests.*

- **AC 4.1.1.1 :** **`pytest-mock` est le standard unique** de mocking.
- **AC 4.1.1.2 :** L'importation et l'utilisation de `unittest.mock` sont INTERDITES.
- **AC 4.1.1.3 :** Tous les tests existants utilisant `unittest.mock` DOIVENT être migrés.

**Story 4.1.2 : Réparer la Suite de Tests Cassée**
*En tant que Développeur, je veux que `pytest` passe au vert pour avoir confiance dans mes changements.*

- **AC 4.1.2.1 :** Corriger toutes les `ImportError` dans la suite de tests.
- **AC 4.1.2.2 :** Corriger toutes les `TypeError: Object of type X is not JSON serializable` en implémentant des sérialiseurs corrects (ou en mockant les sorties).
- **AC 4.1.2.3 :** Utiliser `Faker` pour générer des données de test réalistes.

**Story 4.1.3 : Maintenir la Qualité du Code**
*En tant qu'Architecte, je veux que la base de code reste lisible et maintenable.*

- **AC 4.1.3.1 :** Appliquer les standards de linting (ex: Ruff, limite de 110 caractères).
- **AC 4.1.3.2 :** Refactoriser les fichiers de plus de 400 lignes en modules plus petits.

---

### 4.2. Résilience du Flux (Checkpointing)

*Raison d'être : Ne pas perdre tout le travail si une longue analyse (ex: IA de Découverte) échoue à mi-parcours.*

**Story 4.2.1 : Maintenir le Checkpointing de CrewAI Flow**
*En tant qu'Opérateur Système, je veux pouvoir relancer un flux interrompu sans tout recommencer.*

- **AC 4.2.1.1 :** Le système DOIT utiliser le décorateur `@persist()` de CrewAI Flow.
- **AC 4.2.1.2 :** **Clarification de la Distinction :**
  - `@persist()` = **Résilience de Flux** (Reprise sur erreur).
  - `Supabase` = **Cache de Contenu** (Performance).
- **AC 4.2.1.3 :** Le flux DOIT gérer la **dégradation gracieuse** : si une branche (ex: Branche B - IA) échoue, le flux doit quand même continuer pour consolider et rapporter la Branche A (Python).

---
---

## 5. 📊 Résumé du Flux de Données (Architecture Cible)

1. **Démarrage :** L'utilisateur lance une analyse de portefeuille.
2. **Flux Parallèles :**
    - **Branche A (Python Pur) :** `PortfolioDeepAnalyzer` se lance.
        - Pour chaque holding, il vérifie le cache Supabase (Req 1.1.3).
        - Si *Cache Miss* : Il exécute les calculs via `DeepAnalysisScorer` (Req 2.1.2).
        - Il exporte `deep_analysis.json` (Req 1.2.1).
        - Il lance l'écriture asynchrone vers Supabase (Req 1.1.4).
    - **Branche B (IA) :** `InvestmentDiscoveryCrew` se lance.
        - Il interroge Supabase/RAG (Req 1.1.5) pour le contexte historique.
        - Il utilise `Perplexity` (Req 3.3.1) pour les données web fraîches.
        - Il exporte `discovery.json` (Req 1.2.1).
3. **Consolidation (Python Pur) :** Une fonction Python (Req 2.2.1) attend la fin des branches A et B. Elle lit les fichiers JSON depuis `output/` et les fusionne en `consolidated.json`.
4. **Rapport (Python Pur) :** Le `PythonReportGenerator` (Req 2.3.2) prend `consolidated.json`, le passe dans un template **Jinja2** et génère le `final_report.html`.
5. **Fin.**
