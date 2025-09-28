"""
Tests to validate dynamic test data integration with Faker and pytest-mock.

This module verifies that Faker generates appropriate data types and ranges,
and that test fixtures properly combine Faker data with pytest-mock responses.
"""

import re
from datetime import datetime

import pytest
from faker import Faker
from fixtures.api_test_mocks import APITestMocks


class TestFakerDataGeneration:
    """Test Faker data generation for financial test scenarios."""

    @pytest.fixture
    def faker_instance(self):
        """Create a Faker instance for testing."""
        return Faker()

    def test_should_generate_valid_ticker_symbols(self, faker_instance):
        """Test that Faker generates valid ticker symbols."""
        # Generate multiple ticker symbols
        tickers = [faker_instance.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(10)]

        # Verify all tickers are valid
        for ticker in tickers:
            assert len(ticker) == 4
            assert ticker.isalpha()
            assert ticker.isupper()
            assert re.match(r"^[A-Z]{4}$", ticker)

    def test_should_generate_realistic_financial_data(self, faker_instance):
        """Test that Faker generates realistic financial metrics."""
        for _ in range(20):  # Test multiple iterations
            # Generate financial data
            price = faker_instance.pyfloat(min_value=1.0, max_value=1000.0, right_digits=2)
            volume = faker_instance.pyint(min_value=1000, max_value=100000000)
            market_cap = faker_instance.pyint(min_value=1000000, max_value=1000000000000)
            pe_ratio = faker_instance.pyfloat(min_value=5.0, max_value=50.0, right_digits=2)

            # Verify data ranges
            assert 1.0 <= price <= 1000.0
            assert isinstance(price, float)
            assert len(str(price).split(".")[1]) <= 2  # Max 2 decimal places

            assert 1000 <= volume <= 100000000
            assert isinstance(volume, int)

            assert 1000000 <= market_cap <= 1000000000000
            assert isinstance(market_cap, int)

            assert 5.0 <= pe_ratio <= 50.0
            assert isinstance(pe_ratio, float)

    def test_should_generate_consistent_user_profiles(self, faker_instance):
        """Test that Faker generates consistent user profile data."""
        for _ in range(15):  # Test multiple profiles
            # Generate user profile
            name = faker_instance.name()
            email = faker_instance.email()
            phone = faker_instance.phone_number()
            age = faker_instance.random_int(min=18, max=80)

            # Verify data types and formats
            assert isinstance(name, str)
            assert len(name) > 0
            assert " " in name  # Should contain first and last name

            assert isinstance(email, str)
            assert "@" in email
            assert "." in email
            assert re.match(r"^[^@]+@[^@]+\.[^@]+$", email)

            assert isinstance(phone, str)
            assert len(phone) > 0

            assert isinstance(age, int)
            assert 18 <= age <= 80

    def test_should_generate_varied_crypto_data(self, faker_instance):
        """Test that Faker generates appropriate crypto-related data."""
        crypto_symbols = ["BTC", "ETH", "ADA", "DOT", "LINK", "UNI", "AAVE", "COMP"]

        for _ in range(10):
            # Generate crypto data
            symbol = faker_instance.random_element(crypto_symbols)
            price = faker_instance.pyfloat(min_value=0.01, max_value=100000.0, right_digits=8)
            market_cap = faker_instance.pyint(min_value=1000000, max_value=1000000000000)
            volume_24h = faker_instance.pyint(min_value=100000, max_value=50000000000)

            # Verify crypto-specific ranges
            assert symbol in crypto_symbols
            assert 0.01 <= price <= 100000.0
            assert 1000000 <= market_cap <= 1000000000000
            assert 100000 <= volume_24h <= 50000000000

    def test_should_generate_time_based_data(self, faker_instance):
        """Test that Faker generates appropriate time-based data."""
        base_date = datetime.now()

        for _ in range(10):
            # Generate time-based data
            past_date = faker_instance.date_time_between(start_date="-1y", end_date="now")
            future_date = faker_instance.date_time_between(start_date="now", end_date="+1y")

            # Verify time ranges
            assert isinstance(past_date, datetime)
            assert isinstance(future_date, datetime)
            assert past_date < base_date
            assert future_date > base_date
            assert (base_date - past_date).days <= 365
            assert (future_date - base_date).days <= 365

    def test_should_generate_reproducible_data_with_seed(self, faker_instance):
        """Test that Faker generates reproducible data when seeded."""
        # Set seed and generate data
        faker_instance.seed_instance(12345)
        first_name = faker_instance.name()
        first_ticker = faker_instance.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        first_price = faker_instance.pyfloat(min_value=1.0, max_value=1000.0, right_digits=2)

        # Reset seed and generate again
        faker_instance.seed_instance(12345)
        second_name = faker_instance.name()
        second_ticker = faker_instance.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        second_price = faker_instance.pyfloat(min_value=1.0, max_value=1000.0, right_digits=2)

        # Verify reproducibility
        assert first_name == second_name
        assert first_ticker == second_ticker
        assert first_price == second_price


class TestAPITestMocksIntegration:
    """Test integration of APITestMocks with Faker data."""

    def test_should_setup_yahoo_finance_mock_with_dynamic_data(self, mocker, faker_instance):
        """Test Yahoo Finance mock setup with dynamic data."""
        # Setup mock with TEST ticker
        mock_api = APITestMocks.setup_yahoo_finance_mock(mocker, ticker="TEST")

        # Verify mock configuration
        assert mock_api is not None
        mock_api.assert_not_called()  # Should not be called yet

        # Test mock behavior
        ticker_instance = mock_api.return_value
        result = ticker_instance.info
        assert result["symbol"] == "TEST"
        assert isinstance(result["currentPrice"], float)
        assert isinstance(result["trailingPE"], float)
        assert isinstance(result["marketCap"], int)

    def test_should_setup_alpha_vantage_mock_with_realistic_news(self, mocker, faker_instance):
        """Test Alpha Vantage mock setup with realistic news data."""
        # Setup mock
        mock_api = APITestMocks.setup_alpha_vantage_mock(mocker)

        # Verify mock configuration - Alpha Vantage mock returns an async mock
        # We need to simulate the async context manager behavior
        async_mock = mock_api.return_value.__aenter__.return_value
        result_data = async_mock.json.return_value

        assert "feed" in result_data
        assert len(result_data["feed"]) == 2

        # Verify news article structure
        for article in result_data["feed"]:
            assert "title" in article
            assert "summary" in article
            assert "overall_sentiment_score" in article
            assert "ticker_sentiment" in article
            assert isinstance(float(article["overall_sentiment_score"]), float)
            assert -1.0 <= float(article["overall_sentiment_score"]) <= 1.0

    def test_should_combine_faker_data_with_mock_responses(self, mocker, faker_instance):
        """Test combining Faker-generated data with mock API responses."""
        # Generate dynamic test data
        test_ticker = faker_instance.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        test_price = faker_instance.pyfloat(min_value=10.0, max_value=500.0, right_digits=2)
        test_volume = faker_instance.pyint(min_value=100000, max_value=10000000)

        # Setup mock with dynamic data
        mock_api = mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool._run")
        mock_api.return_value = {
            "symbol": test_ticker,
            "current_price": test_price,
            "volume": test_volume,
            "pe_ratio": faker_instance.pyfloat(min_value=10.0, max_value=30.0, right_digits=2),
            "market_cap": faker_instance.pyint(min_value=1000000000, max_value=100000000000),
        }

        # Test the mock behavior
        result = mock_api.return_value
        assert result["symbol"] == test_ticker
        assert result["current_price"] == test_price
        assert result["volume"] == test_volume
        assert 10.0 <= result["pe_ratio"] <= 30.0
        assert 1000000000 <= result["market_cap"] <= 100000000000

    def test_should_handle_multiple_api_mocks_with_faker_data(self, mocker, faker_instance):
        """Test handling multiple API mocks with Faker-generated data."""
        # Generate test data for multiple APIs
        faker_instance.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        faker_instance.random_element(["BTC", "ETH", "ADA"])

        # Setup multiple mocks
        yahoo_mock = APITestMocks.setup_yahoo_finance_mock(mocker)
        alpha_mock = APITestMocks.setup_alpha_vantage_mock(mocker)
        crypto_mock = APITestMocks.setup_coinmarketcap_mock(mocker)

        # Verify all mocks are configured
        assert yahoo_mock is not None
        assert alpha_mock is not None
        assert crypto_mock is not None

        # Test mock interactions
        yahoo_ticker = yahoo_mock.return_value
        yahoo_result = yahoo_ticker.info
        alpha_result = alpha_mock.return_value
        crypto_result = crypto_mock.return_value

        assert "symbol" in yahoo_result
        # For alpha and crypto, check if they have the expected structure
        if hasattr(alpha_result, "json"):
            alpha_data = alpha_result.json()
        else:
            alpha_data = alpha_result
        if hasattr(crypto_result, "json"):
            crypto_data = crypto_result.json()
        else:
            crypto_data = crypto_result

        assert "feed" in alpha_data or hasattr(alpha_result, "feed")
        assert "data" in crypto_data or hasattr(crypto_result, "data")


class TestDynamicTestDataFixtures:
    """Test fixtures that combine Faker data with pytest-mock responses."""

    @pytest.fixture
    def dynamic_stock_data(self, faker_instance):
        """Fixture providing dynamic stock data."""
        return {
            "symbol": faker_instance.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            "current_price": faker_instance.pyfloat(min_value=1.0, max_value=1000.0, right_digits=2),
            "volume": faker_instance.pyint(min_value=1000, max_value=100000000),
            "pe_ratio": faker_instance.pyfloat(min_value=5.0, max_value=50.0, right_digits=2),
            "market_cap": faker_instance.pyint(min_value=1000000, max_value=1000000000000),
        }

    @pytest.fixture
    def dynamic_user_profile(self, faker_instance):
        """Fixture providing dynamic user profile data."""
        return {
            "name": faker_instance.name(),
            "email": faker_instance.email(),
            "phone": faker_instance.phone_number(),
            "age": faker_instance.random_int(min=25, max=75),
            "investment_horizon": faker_instance.random_element(["5-10 years", "10-15 years", "15-20 years"]),
            "risk_tolerance": faker_instance.random_element(["Conservative", "Moderate", "Aggressive"]),
        }

    @pytest.fixture
    def dynamic_financial_news(self, faker_instance):
        """Fixture providing dynamic financial news data."""
        return [
            {
                "headline": f"{faker_instance.lexify(text='????')} "
                f"{faker_instance.random_element(['Surges', 'Falls', 'Holds Steady'])} on "
                f"{faker_instance.random_element(['Earnings', 'News', 'Market Sentiment'])}",
                "content": faker_instance.text(max_nb_chars=200),
                "sentiment_score": faker_instance.pyfloat(min_value=-1.0, max_value=1.0, right_digits=2),
                "published_date": faker_instance.date_time_between(start_date="-30d", end_date="now"),
                "source": faker_instance.random_element(["Reuters", "Bloomberg", "Yahoo Finance", "MarketWatch"]),
            }
            for _ in range(faker_instance.random_int(min=3, max=10))
        ]

    def test_should_use_dynamic_stock_data_fixture(self, dynamic_stock_data):
        """Test using dynamic stock data fixture."""
        # Verify fixture data structure
        assert "symbol" in dynamic_stock_data
        assert "current_price" in dynamic_stock_data
        assert "volume" in dynamic_stock_data
        assert "pe_ratio" in dynamic_stock_data
        assert "market_cap" in dynamic_stock_data

        # Verify data types and ranges
        assert isinstance(dynamic_stock_data["symbol"], str)
        assert len(dynamic_stock_data["symbol"]) == 4
        assert 1.0 <= dynamic_stock_data["current_price"] <= 1000.0
        assert 1000 <= dynamic_stock_data["volume"] <= 100000000

    def test_should_use_dynamic_user_profile_fixture(self, dynamic_user_profile):
        """Test using dynamic user profile fixture."""
        # Verify fixture data structure
        required_fields = ["name", "email", "phone", "age", "investment_horizon", "risk_tolerance"]
        for field in required_fields:
            assert field in dynamic_user_profile

        # Verify data types
        assert isinstance(dynamic_user_profile["name"], str)
        assert isinstance(dynamic_user_profile["email"], str)
        assert isinstance(dynamic_user_profile["age"], int)
        assert 25 <= dynamic_user_profile["age"] <= 75

    def test_should_use_dynamic_financial_news_fixture(self, dynamic_financial_news):
        """Test using dynamic financial news fixture."""
        # Verify fixture data structure
        assert isinstance(dynamic_financial_news, list)
        assert 3 <= len(dynamic_financial_news) <= 10

        # Verify news article structure
        for article in dynamic_financial_news:
            assert "headline" in article
            assert "content" in article
            assert "sentiment_score" in article
            assert "published_date" in article
            assert "source" in article
            assert -1.0 <= article["sentiment_score"] <= 1.0

    def test_should_combine_fixtures_with_mocks(self, mocker, dynamic_stock_data, dynamic_user_profile):
        """Test combining dynamic fixtures with pytest-mock."""
        # Setup mock using dynamic data
        mock_api = mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool._run")
        mock_api.return_value = dynamic_stock_data

        # Setup user session mock
        mock_session = mocker.patch("finwiz.utils.session_manager.SessionManager.create_new_session")
        mock_session.return_value.client_profile = dynamic_user_profile

        # Test mock behavior with dynamic data
        stock_result = mock_api.return_value
        assert stock_result["symbol"] == dynamic_stock_data["symbol"]
        assert stock_result["current_price"] == dynamic_stock_data["current_price"]

        session_result = mock_session.return_value
        assert session_result.client_profile == dynamic_user_profile


class TestExistingTestsWithDynamicData:
    """Test that existing tests work with dynamic data generation."""

    def test_should_validate_existing_test_patterns_work_with_faker(self, mocker, faker_instance):
        """Test that existing test patterns work with Faker data."""
        # Generate dynamic test data similar to existing tests
        test_ticker = faker_instance.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        test_data = {
            "symbol": test_ticker,
            "price": faker_instance.pyfloat(min_value=10.0, max_value=500.0, right_digits=2),
            "volume": faker_instance.pyint(min_value=100000, max_value=10000000),
        }

        # Mock API call with dynamic data
        mock_api = mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool._run")
        mock_api.return_value = test_data

        # Simulate existing test logic
        result = mock_api.return_value

        # Verify the test pattern works
        assert result["symbol"] == test_ticker
        assert isinstance(result["price"], float)
        assert isinstance(result["volume"], int)
        mock_api.assert_not_called()  # Mock was not actually called, just configured

    def test_should_handle_edge_cases_with_dynamic_data(self, faker_instance):
        """Test handling edge cases with dynamically generated data."""
        # Generate edge case data
        very_low_price = faker_instance.pyfloat(min_value=0.01, max_value=1.0, right_digits=4)
        very_high_price = faker_instance.pyfloat(min_value=1000.0, max_value=10000.0, right_digits=2)
        zero_volume = 0
        high_volume = faker_instance.pyint(min_value=100000000, max_value=1000000000)

        # Test edge case handling
        assert 0.01 <= very_low_price <= 1.0
        assert 1000.0 <= very_high_price <= 10000.0
        assert zero_volume == 0
        assert 100000000 <= high_volume <= 1000000000

    def test_should_maintain_test_performance_with_dynamic_data(self, faker_instance):
        """Test that dynamic data generation doesn't significantly impact test performance."""
        import time

        start_time = time.time()

        # Generate a reasonable amount of test data
        for _ in range(100):
            ticker = faker_instance.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            price = faker_instance.pyfloat(min_value=1.0, max_value=1000.0, right_digits=2)
            volume = faker_instance.pyint(min_value=1000, max_value=100000000)

            # Verify data is generated correctly
            assert len(ticker) == 4
            assert 1.0 <= price <= 1000.0
            assert 1000 <= volume <= 100000000

        end_time = time.time()
        execution_time = end_time - start_time

        # Verify performance is acceptable (should complete in under 1 second)
        assert execution_time < 1.0, f"Dynamic data generation took {execution_time:.2f} seconds, which is too slow"


class TestDataConsistencyAndQuality:
    """Test data consistency and quality with dynamic generation."""

    def test_should_generate_consistent_data_across_test_runs(self, faker_instance):
        """Test that data generation is consistent when using the same seed."""
        # First run with seed
        faker_instance.seed_instance(42)
        first_run_data = [
            {
                "ticker": faker_instance.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                "price": faker_instance.pyfloat(min_value=1.0, max_value=1000.0, right_digits=2),
                "volume": faker_instance.pyint(min_value=1000, max_value=100000000),
            }
            for _ in range(5)
        ]

        # Second run with same seed
        faker_instance.seed_instance(42)
        second_run_data = [
            {
                "ticker": faker_instance.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                "price": faker_instance.pyfloat(min_value=1.0, max_value=1000.0, right_digits=2),
                "volume": faker_instance.pyint(min_value=1000, max_value=100000000),
            }
            for _ in range(5)
        ]

        # Verify consistency
        assert first_run_data == second_run_data

    def test_should_generate_diverse_data_without_seed(self, faker_instance):
        """Test that data generation is diverse when not using a seed."""
        # Generate multiple datasets
        datasets = []
        for _ in range(10):
            dataset = {
                "ticker": faker_instance.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                "price": faker_instance.pyfloat(min_value=1.0, max_value=1000.0, right_digits=2),
                "name": faker_instance.name(),
            }
            datasets.append(dataset)

        # Verify diversity (at least some values should be different)
        tickers = [d["ticker"] for d in datasets]
        prices = [d["price"] for d in datasets]
        names = [d["name"] for d in datasets]

        # Should have some variety in generated data
        assert len(set(tickers)) > 1, "All tickers are the same, not enough diversity"
        assert len(set(prices)) > 1, "All prices are the same, not enough diversity"
        assert len(set(names)) > 1, "All names are the same, not enough diversity"
