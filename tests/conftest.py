"""
Configuration et fixtures partagées pour les tests FinWiz.

Ce module fournit des fixtures Faker configurées pour générer
des données de test réalistes et cohérentes.
"""

from typing import Any

import pytest
from faker import Faker


@pytest.fixture(scope="session")
def faker_instance():
    """
    Instance Faker configurée avec les providers nécessaires.

    Utilise une seed fixe pour garantir la reproductibilité des tests.
    """
    fake = Faker("fr_FR")  # Utilisation d'une seule locale pour éviter les problèmes de proxy
    fake.seed_instance(12345)  # Seed fixe pour reproductibilité

    # Les providers sont déjà inclus par défaut dans Faker
    # Pas besoin de les ajouter explicitement

    return fake


@pytest.fixture
def fake_client_profile(faker_instance):
    """
    Génère un profil client réaliste pour les tests.

    Returns:
        Dict contenant les données d'un client fictif

    """
    fake = faker_instance

    return {
        "name": fake.name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "age": fake.random_int(min=25, max=75),
        "address": fake.address().replace("\n", ", "),
        "city": fake.city(),
        "country": fake.country(),
        "investment_horizon": fake.random_element(["5-10 ans", "10-15 ans", "15-20 ans", "20+ ans"]),
        "monthly_budget": f"{fake.random_int(min=500, max=5000)} CHF",
        "risk_tolerance": fake.random_element(["Conservative", "Moderate", "Aggressive"]),
        "occupation": fake.job(),
        "company": fake.company(),
    }


@pytest.fixture
def fake_financial_data(faker_instance):
    """
    Génère des données financières réalistes pour les tests.

    Returns:
        Dict contenant des données financières fictives

    """
    fake = faker_instance

    return {
        "plan_id": fake.uuid4(),
        "account_number": fake.bban(),
        "portfolio_value": fake.pydecimal(left_digits=6, right_digits=2, positive=True),
        "annual_income": fake.random_int(min=50000, max=200000),
        "net_worth": fake.random_int(min=100000, max=1000000),
        "investment_amount": fake.random_int(min=1000, max=50000),
        "currency": fake.random_element(["CHF", "EUR", "USD"]),
    }


@pytest.fixture
def fake_stock_data(faker_instance):
    """
    Génère des données d'actions réalistes pour les tests.

    Returns:
        Dict contenant des données d'actions fictives

    """
    fake = faker_instance

    # Tickers réalistes mais fictifs
    fake_tickers = ["FAKE", "TEST", "DEMO", "MOCK", "SMPL"]

    return {
        "ticker": fake.random_element(fake_tickers),
        "company_name": fake.company(),
        "price": fake.pydecimal(left_digits=3, right_digits=2, positive=True),
        "pe_ratio": fake.pydecimal(left_digits=2, right_digits=2, positive=True),
        "market_cap": fake.random_int(min=1000000, max=1000000000),
        "sector": fake.random_element(["Technology", "Healthcare", "Finance", "Energy", "Consumer Goods"]),
        "recommendation": fake.random_element(["BUY", "HOLD", "SELL"]),
        "confidence_score": fake.pydecimal(left_digits=0, right_digits=2, positive=True, max_value=1),
    }


@pytest.fixture
def fake_timestamps(faker_instance):
    """
    Génère des timestamps cohérents pour les tests.

    Returns:
        Dict contenant des timestamps fictifs mais logiques

    """
    fake = faker_instance

    # Génère des dates dans une séquence logique
    created_at = fake.date_time_between(start_date="-1y", end_date="-1m")
    last_updated = fake.date_time_between(start_date=created_at, end_date="now")

    return {
        "created_at": created_at,
        "last_updated": last_updated,
        "analysis_date": fake.date_time_between(start_date=created_at, end_date=last_updated),
        "report_date": last_updated,
    }


@pytest.fixture
def fake_html_metadata(faker_instance):
    """
    Génère des métadonnées HTML réalistes pour les tests.

    Returns:
        Dict contenant des métadonnées HTML fictives

    """
    fake = faker_instance

    return {
        "plan_id": fake.uuid4(),
        "title": f"Plan Financier - {fake.name()}",
        "description": fake.text(max_nb_chars=200),
        "author": fake.name(),
        "language": fake.random_element(["fr", "en", "de"]),
        "charset": "utf-8",
    }


@pytest.fixture
def fake_portfolio_holdings(faker_instance):
    """
    Génère une liste de positions de portefeuille réalistes.

    Returns:
        List de dictionnaires représentant des positions

    """
    fake = faker_instance

    holdings = []
    companies = [
        ("AAPL", "Apple Inc."),
        ("MSFT", "Microsoft Corp."),
        ("GOOGL", "Alphabet Inc."),
        ("TSLA", "Tesla Inc."),
        ("AMZN", "Amazon.com Inc."),
    ]

    for ticker, name in fake.random_elements(companies, length=fake.random_int(min=2, max=4), unique=True):
        holdings.append(
            {
                "ticker": ticker,
                "name": name,
                "decision": fake.random_element(["KEEP", "SELL"]),
                "composite_score": str(fake.pydecimal(left_digits=0, right_digits=2, positive=True, max_value=1)),
                "risk_level": fake.random_element(["Low", "Medium", "High"]),
                "quantity": fake.random_int(min=1, max=100),
                "current_price": fake.pydecimal(left_digits=3, right_digits=2, positive=True),
            }
        )

    return holdings


@pytest.fixture
def fake_investment_recommendations(faker_instance):
    """
    Génère des recommandations d'investissement réalistes.

    Returns:
        Dict contenant des recommandations par catégorie

    """
    fake = faker_instance

    stocks = [
        f"{fake.random_element(['NVDA', 'AMD', 'INTC'])} - {fake.company()}",
        f"{fake.random_element(['JPM', 'BAC', 'WFC'])} - {fake.company()}",
    ]

    etfs = [
        f"{fake.random_element(['VTI', 'SPY', 'QQQ'])} - {fake.company()} ETF",
        f"{fake.random_element(['AGG', 'BND', 'TLT'])} - {fake.company()} Bond ETF",
    ]

    crypto = [
        f"BTC ({fake.random_int(min=10, max=100)} CHF/mois)",
        f"ETH ({fake.random_int(min=5, max=50)} CHF/mois)",
    ]

    return {
        "stocks": stocks,
        "etfs": etfs,
        "crypto": crypto,
    }


class FakeDataGenerator:
    """
    Générateur de données de test centralisé utilisant Faker.

    Cette classe fournit des méthodes pratiques pour générer
    des données de test cohérentes et réalistes.
    """

    def __init__(self, faker_instance: Faker):
        self.fake = faker_instance

    def generate_session_html(
        self, client_profile: dict[str, Any], portfolio_holdings: list, recommendations: dict[str, list]
    ) -> str:
        """
        Génère un HTML de session complet avec des données réalistes.

        Args:
            client_profile: Profil client généré par fake_client_profile
            portfolio_holdings: Holdings générés par fake_portfolio_holdings
            recommendations: Recommandations générées par fake_investment_recommendations

        Returns:
            String HTML complète pour les tests

        """
        plan_id = self.fake.uuid4()
        created_at = self.fake.date_time_between(start_date="-1y", end_date="-1m")
        last_updated = self.fake.date_time_between(start_date=created_at, end_date="now")

        # Génération des lignes de tableau pour le portefeuille
        portfolio_rows = ""
        for holding in portfolio_holdings:
            portfolio_rows += f"""
                        <tr>
                            <td>{holding["name"]}</td>
                            <td>{holding["ticker"]}</td>
                            <td><span class="badge {"keep" if holding["decision"] == "KEEP" else "sell"}">{holding["decision"]}</span></td>
                            <td>{holding["composite_score"]}</td>
                            <td>{holding["risk_level"]}</td>
                        </tr>"""

        # Génération des listes de recommandations
        stock_items = "\n".join([f"<li>{stock}</li>" for stock in recommendations["stocks"]])
        etf_items = "\n".join([f"<li>{etf}</li>" for etf in recommendations["etfs"]])
        crypto_items = "\n".join([f"<li>{crypto}</li>" for crypto in recommendations["crypto"]])

        return f"""
        <!doctype html>
        <html lang="fr">
        <head>
            <meta charset="utf-8" />
            <meta name="plan-id" content="{plan_id}" />
            <meta name="created-at" content="{created_at.isoformat()}" />
            <meta name="last-updated" content="{last_updated.isoformat()}" />
            <title>Plan Financier Familial — {client_profile["name"]} ({last_updated.strftime("%d %B %Y")})</title>
        </head>
        <body>
            <div class="container">
                <header>
                    <div class="meta">Client: {client_profile["name"]}, {client_profile["age"]} ans • Horizon: {client_profile["investment_horizon"]} • Budget mensuel: {client_profile["monthly_budget"]}</div>
                </header>

                <section class="card">
                    <h2>📦 Revue du portefeuille: Conserver ou Vendre</h2>
                    <table>
                        <thead>
                            <tr><th>Nom</th><th>Ticker</th><th>Décision</th><th>Score composite</th><th>Risque</th></tr>
                        </thead>
                        <tbody>{portfolio_rows}
                        </tbody>
                    </table>
                </section>

                <section class="card">
                    <h2>💎 Recommandations d'Investissement</h2>
                    <h3>Sélection d'actions 📊</h3>
                    <ul>{stock_items}</ul>
                    <h3>Sélection d'ETFs 📈</h3>
                    <ul>{etf_items}</ul>
                    <h3>Allocation en cryptomonnaies ₿</h3>
                    <ul>{crypto_items}</ul>
                </section>
            </div>
        </body>
        </html>
        """


@pytest.fixture
def fake_data_generator(faker_instance):
    """Fixture qui fournit une instance du générateur de données de test."""
    return FakeDataGenerator(faker_instance)


@pytest.fixture
def mock_ticker(mocker):
    """
    Mock fixture for yfinance.Ticker.

    Returns a mock that can be configured in individual tests.
    """
    return mocker.patch("yfinance.Ticker")


@pytest.fixture
def mock_openai(mocker):
    """
    Mock fixture for OpenAI client.

    Returns a mock that can be configured in individual tests.
    """
    return mocker.patch("openai.OpenAI")


@pytest.fixture
def mock_get(mocker):
    """
    Mock fixture for HTTP GET requests.

    Returns a mock that can be configured in individual tests.
    """
    return mocker.patch("requests.get")
