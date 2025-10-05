# Guide de Migration vers Faker

## Vue d'ensemble

Ce guide explique comment migrer vos tests existants de données statiques vers des données dynamiques générées par Faker. Cette approche améliore la robustesse des tests en utilisant des données réalistes et variées.

## Installation et Configuration

### 1. Ajout de la dépendance

Faker a été ajouté aux dépendances de développement dans `pyproject.toml` :

```toml
[dependency-groups]
dev = [
    "faker>=33.1.0",
    # ... autres dépendances
]
```

### 2. Configuration des fixtures

Le fichier `tests/conftest.py` contient toutes les fixtures Faker configurées :

```python
@pytest.fixture(scope="session")
def faker_instance():
    """Instance Faker avec seed fixe pour reproductibilité."""
    fake = Faker('fr_FR')
    fake.seed_instance(12345)  # Garantit des résultats reproductibles
    return fake
```

## Patterns de Migration

### Avant : Données Statiques

```python
def test_client_profile_creation():
    # ❌ Données codées en dur
    client_name = "Jean Dupont"
    client_age = 45
    investment_horizon = "10-15 ans"
    monthly_budget = "2000 CHF"
    
    profile = ClientProfile(
        name=client_name,
        age=client_age,
        investment_horizon=investment_horizon,
        monthly_budget=monthly_budget
    )
    
    assert profile.name == "Jean Dupont"
    assert profile.age == 45
```

### Après : Données Dynamiques avec Faker

```python
def test_client_profile_creation(fake_client_profile):
    # ✅ Données générées dynamiquement
    profile = ClientProfile(
        name=fake_client_profile["name"],
        age=fake_client_profile["age"],
        investment_horizon=fake_client_profile["investment_horizon"],
        monthly_budget=fake_client_profile["monthly_budget"]
    )
    
    # Assertions dynamiques
    assert profile.name == fake_client_profile["name"]
    assert profile.age == fake_client_profile["age"]
    assert 25 <= profile.age <= 75  # Validation des contraintes métier
    assert "CHF" in profile.monthly_budget
```

## Fixtures Disponibles

### 1. `fake_client_profile`

Génère un profil client complet :

```python
def test_with_client_profile(fake_client_profile):
    # Contient : name, age, investment_horizon, monthly_budget, risk_tolerance, etc.
    assert fake_client_profile["name"] is not None
    assert 25 <= fake_client_profile["age"] <= 75
```

### 2. `fake_financial_data`

Génère des données financières :

```python
def test_with_financial_data(fake_financial_data):
    # Contient : plan_id, portfolio_value, annual_income, etc.
    assert fake_financial_data["plan_id"] is not None
    assert fake_financial_data["portfolio_value"] > 0
```

### 3. `fake_stock_data`

Génère des données d'actions :

```python
def test_with_stock_data(fake_stock_data):
    # Contient : ticker, company_name, price, recommendation, etc.
    assert fake_stock_data["ticker"] in ["FAKE", "TEST", "DEMO", "MOCK", "SMPL"]
    assert fake_stock_data["recommendation"] in ["BUY", "HOLD", "SELL"]
```

### 4. `fake_portfolio_holdings`

Génère une liste de positions de portefeuille :

```python
def test_with_portfolio_holdings(fake_portfolio_holdings):
    assert len(fake_portfolio_holdings) >= 2
    for holding in fake_portfolio_holdings:
        assert holding["ticker"] is not None
        assert holding["decision"] in ["KEEP", "SELL"]
```

### 5. `fake_data_generator`

Générateur avancé pour HTML complet :

```python
def test_with_html_generator(fake_client_profile, fake_portfolio_holdings, 
                           fake_investment_recommendations, fake_data_generator):
    html = fake_data_generator.generate_session_html(
        fake_client_profile, 
        fake_portfolio_holdings, 
        fake_investment_recommendations
    )
    assert "<!doctype html>" in html.lower()
```

## Meilleures Pratiques

### 1. Utilisation de Seeds pour la Reproductibilité

```python
def test_reproducible_data(faker_instance):
    # Réinitialise la seed pour des résultats identiques
    faker_instance.seed_instance(42)
    first_name = faker_instance.name()
    
    faker_instance.seed_instance(42)
    second_name = faker_instance.name()
    
    assert first_name == second_name  # Identiques grâce à la seed
```

### 2. Validation des Contraintes Métier

```python
def test_business_constraints(fake_client_profile):
    # ✅ Toujours valider les règles métier
    assert 25 <= fake_client_profile["age"] <= 75
    assert fake_client_profile["risk_tolerance"] in ["Conservative", "Moderate", "Aggressive"]
    assert any(currency in fake_client_profile["monthly_budget"] 
              for currency in ["CHF", "EUR", "USD"])
```

### 3. Tests avec Données Multiples

```python
def test_multiple_scenarios(faker_instance):
    # Test avec plusieurs jeux de données
    for i in range(10):
        client_name = faker_instance.name()
        client_age = faker_instance.random_int(min=25, max=75)
        
        profile = ClientProfile(name=client_name, age=client_age)
        
        # Validation pour chaque jeu de données
        assert len(profile.name.strip()) > 0
        assert 25 <= profile.age <= 75
```

### 4. Gestion des Cas Limites

```python
def test_edge_cases(faker_instance):
    # Test des valeurs limites
    min_age_profile = ClientProfile(age=25)  # Âge minimum
    max_age_profile = ClientProfile(age=75)  # Âge maximum
    
    assert min_age_profile.age == 25
    assert max_age_profile.age == 75
    
    # Test avec des noms très longs
    long_name = faker_instance.text(max_nb_chars=200)
    profile = ClientProfile(name=long_name[:100])  # Troncature
    assert len(profile.name) <= 100
```

## Fonctions Faker Recommandées

### Données Personnelles

- `fake.name()` - Nom complet
- `fake.first_name()` - Prénom
- `fake.last_name()` - Nom de famille
- `fake.email()` - Adresse email
- `fake.phone_number()` - Numéro de téléphone
- `fake.address()` - Adresse complète

### Données Financières

- `fake.iban()` - Numéro IBAN
- `fake.currency_code()` - Code devise (EUR, USD, etc.)
- `fake.pydecimal(left_digits=6, right_digits=2)` - Montants
- `fake.random_int(min=1000, max=100000)` - Entiers dans une plage

### Données Temporelles

- `fake.date_time_between(start_date='-1y', end_date='now')` - Dates dans une plage
- `fake.date_time()` - Date/heure aléatoire
- `fake.future_datetime()` - Date future

### Données Textuelles

- `fake.text(max_nb_chars=200)` - Texte de longueur limitée
- `fake.sentence()` - Phrase
- `fake.company()` - Nom d'entreprise
- `fake.job()` - Profession

### Sélection d'Éléments

- `fake.random_element(['A', 'B', 'C'])` - Choix dans une liste
- `fake.random_elements(['A', 'B', 'C'], length=2)` - Plusieurs éléments
- `fake.random_int(min=1, max=10)` - Entier dans une plage

## Exemples de Migration Complète

### Migration d'un Test de Session

```python
# AVANT
def test_session_creation():
    session = SessionManager("test.html").create_new_session()
    session.client_profile.name = "Test Client"
    session.client_profile.age = 50
    
    assert session.client_profile.name == "Test Client"
    assert session.client_profile.age == 50

# APRÈS
def test_session_creation(fake_client_profile):
    session = SessionManager("test.html").create_new_session()
    session.client_profile.name = fake_client_profile["name"]
    session.client_profile.age = fake_client_profile["age"]
    
    assert session.client_profile.name == fake_client_profile["name"]
    assert session.client_profile.age == fake_client_profile["age"]
    assert 25 <= session.client_profile.age <= 75  # Validation métier
```

### Migration d'un Test de Parsing HTML

```python
# AVANT
def test_html_parsing():
    html = """<div class="meta">Client: Jean Dupont, 45 ans</div>"""
    # ... parsing logic
    
# APRÈS
def test_html_parsing(fake_client_profile, fake_data_generator):
    html = fake_data_generator.generate_session_html(
        fake_client_profile, [], {}
    )
    # ... parsing logic avec données dynamiques
```

## Avantages de cette Approche

1. **Robustesse** : Tests avec des données variées révèlent plus de bugs
2. **Réalisme** : Données proches de la production
3. **Maintenance** : Moins de données codées en dur à maintenir
4. **Reproductibilité** : Seeds fixes garantissent des résultats cohérents
5. **Couverture** : Tests automatiques de cas limites et variations

## Commandes Utiles

```bash
# Installation des dépendances
uv sync

# Exécution des tests Faker
uv run pytest tests/test_session_manager_with_faker.py -v

# Test spécifique
uv run pytest tests/test_session_manager_with_faker.py::test_faker_integration_example -v -s

# Tests sans couverture (plus rapide pour le développement)
uv run pytest tests/test_session_manager_with_faker.py --no-cov
```

Cette migration vers Faker améliore significativement la qualité et la robustesse de vos tests en remplaçant les données statiques par des données réalistes et variées.
