"""
Mock data generation for stock screening.

This module provides utilities for generating mock stock data for testing.
"""

import random

from finwiz.quantitative.screening_filters import StockData


class MockDataGenerator:
    """Generates mock stock data for screening."""

    @staticmethod
    def generate_stock_data(symbol: str) -> StockData:
        """Generate mock stock data for testing."""
        # Mock company data
        sectors = ["Technology", "Healthcare", "Financial", "Consumer", "Industrial", "Energy"]
        industries = ["Software", "Biotechnology", "Banking", "Retail", "Manufacturing", "Oil & Gas"]

        return StockData(
            symbol=symbol,
            company_name=f"{symbol} Corporation",
            sector=random.choice(sectors),
            industry=random.choice(industries),
            market_cap=random.uniform(1e9, 500e9),
            price=random.uniform(10, 500),
            pe_ratio=random.uniform(5, 50) if random.random() > 0.1 else None,
            pb_ratio=random.uniform(0.5, 10) if random.random() > 0.1 else None,
            ps_ratio=random.uniform(0.5, 20) if random.random() > 0.1 else None,
            dividend_yield=random.uniform(0, 0.08) if random.random() > 0.3 else None,
            roe=random.uniform(-0.2, 0.4) if random.random() > 0.1 else None,
            roa=random.uniform(-0.1, 0.2) if random.random() > 0.1 else None,
            debt_to_equity=random.uniform(0, 2) if random.random() > 0.1 else None,
            current_ratio=random.uniform(0.5, 5) if random.random() > 0.1 else None,
            quick_ratio=random.uniform(0.3, 3) if random.random() > 0.1 else None,
            revenue_growth=random.uniform(-0.3, 0.5) if random.random() > 0.1 else None,
            earnings_growth=random.uniform(-0.5, 1.0) if random.random() > 0.1 else None,
            eps_growth=random.uniform(-0.5, 1.0) if random.random() > 0.1 else None,
            rsi=random.uniform(20, 80) if random.random() > 0.1 else None,
            price_change_1m=random.uniform(-0.3, 0.3) if random.random() > 0.1 else None,
            price_change_3m=random.uniform(-0.5, 0.5) if random.random() > 0.1 else None,
            price_change_1y=random.uniform(-0.8, 1.5) if random.random() > 0.1 else None,
            volume_avg_3m=random.uniform(100000, 10000000) if random.random() > 0.1 else None,
            beta=random.uniform(0.3, 2.5) if random.random() > 0.1 else None,
            analyst_rating=random.uniform(1, 5) if random.random() > 0.2 else None,
            price_target=random.uniform(10, 600) if random.random() > 0.2 else None,
        )
