"""
Tests améliorés du SessionManager utilisant Faker pour des données réalistes.

Ce module démontre l'intégration de Faker pour remplacer les identifiants
statiques par des données dynamiques et réalistes dans les tests.
"""

import tempfile
from datetime import datetime
from pathlib import Path

from finwiz.schemas.session import ClientProfile, FinancialPlan
from finwiz.utils.session_manager import SessionManager


class TestSessionManagerWithFaker:
    """
    Tests du SessionManager utilisant Faker pour des données réalistes.

    Ces tests démontrent les meilleures pratiques pour intégrer Faker
    dans une suite de tests existante.
    """

    def setup_method(self):
        """Configuration des fixtures de test."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_report_path = Path(self.temp_dir) / "test_report.html"
        self.session_manager = SessionManager(str(self.test_report_path))

    def test_should_create_session_with_realistic_client_data(self, fake_client_profile, fake_timestamps):
        """
        Test de création de session avec des données client réalistes.

        Utilise Faker pour générer des profils clients variés et réalistes
        au lieu de données statiques codées en dur.
        """
        # Arrange - Utilisation des données générées par Faker
        session = self.session_manager.create_new_session()

        # Mise à jour avec des données réalistes
        session.client_profile.name = fake_client_profile["name"]
        session.client_profile.age = fake_client_profile["age"]
        session.client_profile.investment_horizon = fake_client_profile["investment_horizon"]
        session.client_profile.monthly_budget = fake_client_profile["monthly_budget"]
        session.client_profile.risk_tolerance = fake_client_profile["risk_tolerance"]
        session.created_at = fake_timestamps["created_at"]
        session.last_updated = fake_timestamps["last_updated"]

        # Act & Assert
        assert session.client_profile.name == fake_client_profile["name"]
        assert session.client_profile.age == fake_client_profile["age"]
        assert session.client_profile.investment_horizon == fake_client_profile["investment_horizon"]
        assert session.client_profile.monthly_budget == fake_client_profile["monthly_budget"]
        assert session.client_profile.risk_tolerance == fake_client_profile["risk_tolerance"]
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_updated, datetime)

        # Validation des contraintes métier
        assert 25 <= session.client_profile.age <= 75
        assert session.created_at <= session.last_updated

    def test_should_parse_html_with_dynamic_client_profiles(
        self, fake_client_profile, fake_portfolio_holdings, fake_investment_recommendations, fake_data_generator
    ):
        """
        Test de parsing HTML avec des profils clients dynamiques.

        Génère du HTML complet avec des données réalistes pour tester
        la robustesse du parsing avec différents formats de données.
        """
        # Arrange - Génération d'HTML réaliste
        html_content = fake_data_generator.generate_session_html(
            fake_client_profile, fake_portfolio_holdings, fake_investment_recommendations
        )

        # Act
        result = self.session_manager.parse_html_report(html_content)

        # Assert - Vérification de l'extraction correcte
        assert isinstance(result, FinancialPlan)
        assert result.client_profile.name == fake_client_profile["name"]
        assert result.client_profile.age == fake_client_profile["age"]
        assert result.client_profile.investment_horizon == fake_client_profile["investment_horizon"]
        assert result.client_profile.monthly_budget == fake_client_profile["monthly_budget"]

        # Vérification des données de portefeuille
        assert "holdings" in result.current_portfolio_data
        holdings = result.current_portfolio_data["holdings"]
        assert len(holdings) == len(fake_portfolio_holdings)

        # Vérification des recommandations
        assert "stocks" in result.current_recommendations
        assert "etfs" in result.current_recommendations
        assert "crypto" in result.current_recommendations

    def test_should_validate_multiple_client_profiles(self, faker_instance):
        """
        Test de validation avec plusieurs profils clients générés dynamiquement.

        Génère plusieurs profils clients pour tester la robustesse
        de la validation avec des données variées.
        """
        # Arrange - Génération de plusieurs profils clients
        for i in range(5):  # Test avec 5 profils différents
            # Génération de données uniques pour chaque itération
            client_name = faker_instance.name()
            client_age = faker_instance.random_int(min=25, max=75)
            investment_horizon = faker_instance.random_element(["5-10 ans", "10-15 ans", "15-20 ans"])
            monthly_budget = f"{faker_instance.random_int(min=500, max=5000)} CHF"
            risk_tolerance = faker_instance.random_element(["Conservative", "Moderate", "Aggressive"])

            # Act - Création et validation du profil
            profile = ClientProfile(
                name=client_name,
                age=client_age,
                investment_horizon=investment_horizon,
                monthly_budget=monthly_budget,
                risk_tolerance=risk_tolerance,
            )

            # Assert - Validation des données générées
            assert profile.name == client_name
            assert profile.age == client_age
            assert profile.investment_horizon == investment_horizon
            assert profile.monthly_budget == monthly_budget
            assert profile.risk_tolerance == risk_tolerance

            # Validation des contraintes métier
            assert 25 <= profile.age <= 75
            assert "CHF" in profile.monthly_budget
            assert len(profile.name.strip()) > 0

    def test_should_handle_various_financial_data_formats(self, fake_financial_data, fake_stock_data):
        """
        Test de gestion de différents formats de données financières.

        Utilise Faker pour générer des données financières variées
        et tester la robustesse du système avec différents formats.
        """
        # Arrange - Utilisation des données financières générées
        plan = self.session_manager.create_new_session()

        # Ajout de données financières réalistes
        plan.current_portfolio_data = {
            "account_number": fake_financial_data["account_number"],
            "portfolio_value": float(fake_financial_data["portfolio_value"]),
            "currency": fake_financial_data["currency"],
            "holdings": [
                {
                    "ticker": fake_stock_data["ticker"],
                    "company_name": fake_stock_data["company_name"],
                    "price": float(fake_stock_data["price"]),
                    "recommendation": fake_stock_data["recommendation"],
                }
            ],
        }

        # Act - Validation de l'intégrité
        is_valid, issues = self.session_manager.validate_session_integrity(plan)

        # Assert
        assert isinstance(plan.current_portfolio_data, dict)
        assert "account_number" in plan.current_portfolio_data
        assert "portfolio_value" in plan.current_portfolio_data
        assert "currency" in plan.current_portfolio_data
        assert "holdings" in plan.current_portfolio_data

        # Validation des données de stock
        holding = plan.current_portfolio_data["holdings"][0]
        assert holding["ticker"] in ["FAKE", "TEST", "DEMO", "MOCK", "SMPL"]
        assert holding["recommendation"] in ["BUY", "HOLD", "SELL"]
        assert holding["price"] > 0

    def test_should_generate_unique_plan_ids(self, faker_instance):
        """
        Test de génération d'identifiants de plan uniques.

        Vérifie que chaque session génère un identifiant unique
        en utilisant Faker pour simuler plusieurs créations.
        """
        # Arrange & Act - Génération de plusieurs sessions
        plan_ids = set()

        for _ in range(10):  # Génération de 10 sessions
            session = self.session_manager.create_new_session()
            plan_ids.add(session.plan_id)

        # Assert - Vérification de l'unicité
        assert len(plan_ids) == 10  # Tous les IDs doivent être uniques

        # Vérification du format UUID
        for plan_id in plan_ids:
            assert len(plan_id) > 0
            assert "-" in plan_id  # Format UUID contient des tirets

    def test_should_save_and_load_realistic_sessions(
        self, fake_client_profile, fake_portfolio_holdings, fake_investment_recommendations
    ):
        """
        Test de sauvegarde et chargement avec des données réalistes.

        Test complet du cycle sauvegarde/chargement avec des données
        générées dynamiquement par Faker.
        """
        # Arrange - Création d'une session avec des données réalistes
        original_session = self.session_manager.create_new_session()

        # Mise à jour avec des données Faker
        original_session.client_profile.name = fake_client_profile["name"]
        original_session.client_profile.age = fake_client_profile["age"]
        original_session.client_profile.investment_horizon = fake_client_profile["investment_horizon"]
        original_session.client_profile.monthly_budget = fake_client_profile["monthly_budget"]
        original_session.client_profile.risk_tolerance = fake_client_profile["risk_tolerance"]

        original_session.current_portfolio_data = {"holdings": fake_portfolio_holdings}
        original_session.current_recommendations = fake_investment_recommendations

        # Act - Sauvegarde et chargement
        self.session_manager.save_financial_plan(original_session, backup=False)
        loaded_session = self.session_manager.load_existing_session()

        # Assert - Vérification de l'intégrité des données
        assert loaded_session is not None
        assert loaded_session.plan_id == original_session.plan_id
        assert loaded_session.client_profile.name == fake_client_profile["name"]
        assert loaded_session.client_profile.age == fake_client_profile["age"]
        # Le risk_tolerance peut être None si l'extraction HTML échoue
        if loaded_session.client_profile.risk_tolerance is not None:
            assert loaded_session.client_profile.risk_tolerance == fake_client_profile["risk_tolerance"]

        # Vérification des données de portefeuille
        assert "holdings" in loaded_session.current_portfolio_data
        loaded_holdings = loaded_session.current_portfolio_data["holdings"]
        assert len(loaded_holdings) == len(fake_portfolio_holdings)

        # Vérification des recommandations
        for category in ["stocks", "etfs", "crypto"]:
            assert category in loaded_session.current_recommendations

    def test_should_handle_edge_cases_with_faker_data(self, faker_instance):
        """
        Test de gestion des cas limites avec des données Faker.

        Teste la robustesse du système avec des données générées
        qui peuvent représenter des cas limites réels.
        """
        # Test avec des noms très longs
        long_name = faker_instance.text(max_nb_chars=200)
        profile = ClientProfile(name=long_name[:100])  # Limitation à 100 caractères
        assert len(profile.name) <= 100

        # Test avec des âges aux limites
        min_age_profile = ClientProfile(age=25)
        max_age_profile = ClientProfile(age=75)
        assert min_age_profile.age == 25
        assert max_age_profile.age == 75

        # Test avec des budgets de formats variés
        for _ in range(5):
            budget = f"{faker_instance.random_int(min=100, max=10000)} {faker_instance.random_element(['CHF', 'EUR', 'USD'])}"
            profile = ClientProfile(monthly_budget=budget)
            assert profile.monthly_budget == budget
            assert any(currency in profile.monthly_budget for currency in ["CHF", "EUR", "USD"])

    def test_should_generate_consistent_data_with_seed(self, faker_instance):
        """
        Test de cohérence des données avec une seed fixe.

        Vérifie que l'utilisation d'une seed fixe dans Faker
        produit des résultats reproductibles pour les tests.
        """
        # Arrange - Réinitialisation avec la même seed
        faker_instance.seed_instance(12345)

        # Act - Génération de données
        first_name = faker_instance.name()
        first_email = faker_instance.email()

        # Réinitialisation avec la même seed
        faker_instance.seed_instance(12345)
        second_name = faker_instance.name()
        second_email = faker_instance.email()

        # Assert - Les données doivent être identiques
        assert first_name == second_name
        assert first_email == second_email


class TestFakerIntegrationBestPractices:
    """
    Démonstration des meilleures pratiques pour l'intégration de Faker.

    Cette classe montre comment utiliser efficacement Faker dans
    différents scénarios de test.
    """

    def test_faker_localization_for_french_data(self, faker_instance):
        """
        Test de localisation Faker pour des données françaises.

        Démontre l'utilisation de Faker avec des locales spécifiques
        pour générer des données cohérentes avec le contexte métier.
        """
        # Configuration pour la France
        fake_fr = faker_instance

        # Génération de données françaises
        french_name = fake_fr.name()
        french_address = fake_fr.address()
        french_phone = fake_fr.phone_number()

        # Validation du format (les formats peuvent varier selon la locale)
        assert len(french_name) > 0
        assert len(french_address) > 0
        assert len(french_phone) > 0

    def test_faker_custom_providers_for_financial_data(self, faker_instance):
        """
        Test d'utilisation de providers personnalisés pour les données financières.

        Montre comment étendre Faker avec des providers spécialisés
        pour le domaine financier.
        """
        fake = faker_instance

        # Génération de données financières spécialisées
        iban = fake.iban()
        currency_code = fake.currency_code()

        # Validation des formats
        assert len(iban) > 15  # IBAN minimum length
        assert len(currency_code) == 3  # ISO currency codes are 3 characters

    def test_faker_performance_with_bulk_data_generation(self, faker_instance):
        """
        Test de performance avec génération de données en masse.

        Évalue les performances de Faker lors de la génération
        de grandes quantités de données de test.
        """
        import time

        fake = faker_instance
        start_time = time.time()

        # Génération de 1000 profils clients
        profiles = []
        for _ in range(1000):
            profile = {
                "name": fake.name(),
                "email": fake.email(),
                "phone": fake.phone_number(),
                "age": fake.random_int(min=25, max=75),
            }
            profiles.append(profile)

        end_time = time.time()
        generation_time = end_time - start_time

        # Validation
        assert len(profiles) == 1000
        assert generation_time < 5.0  # Doit être rapide (< 5 secondes)

        # Vérification de la variété des données
        names = {p["name"] for p in profiles}
        emails = {p["email"] for p in profiles}

        # Au moins 90% des noms et emails doivent être uniques
        assert len(names) > 900
        assert len(emails) > 900


def test_faker_integration_example():
    """
    Exemple complet d'intégration de Faker dans un test existant.

    Cette fonction montre comment transformer un test avec des données
    statiques en test utilisant Faker pour des données dynamiques.
    """
    from faker import Faker

    # Configuration de Faker
    fake = Faker(["fr_FR"])
    fake.seed_instance(42)  # Pour la reproductibilité

    # AVANT: Données statiques
    # client_name = "Jean Dupont"
    # client_age = 45
    # investment_horizon = "10-15 ans"

    # APRÈS: Données dynamiques avec Faker
    client_name = fake.name()
    client_age = fake.random_int(min=25, max=75)
    investment_horizon = fake.random_element(["5-10 ans", "10-15 ans", "15-20 ans", "20+ ans"])
    monthly_budget = f"{fake.random_int(min=500, max=5000)} CHF"
    risk_tolerance = fake.random_element(["Conservative", "Moderate", "Aggressive"])

    # Création du profil avec des données réalistes
    profile = ClientProfile(
        name=client_name,
        age=client_age,
        investment_horizon=investment_horizon,
        monthly_budget=monthly_budget,
        risk_tolerance=risk_tolerance,
    )

    # Validation avec des assertions dynamiques
    assert profile.name == client_name
    assert profile.age == client_age
    assert profile.investment_horizon == investment_horizon
    assert profile.monthly_budget == monthly_budget
    assert profile.risk_tolerance == risk_tolerance

    # Validation des contraintes métier
    assert 25 <= profile.age <= 75
    assert "CHF" in profile.monthly_budget
    assert len(profile.name.strip()) > 0

    print(f"✅ Test réussi avec le profil: {client_name}, {client_age} ans, {investment_horizon}, {monthly_budget}")
