# Developer Guide - A+ Investment Discovery System

## Architecture Overview

The A+ Investment Discovery system is built on CrewAI Flow architecture with specialized agents for different asset classes. This guide provides technical details for developers who want to extend, customize, or integrate with the discovery system.

## Core Components

### 1. CrewAI Agents Architecture

```python
# src/finwiz/crews/investment_discovery_crew/investment_discovery_crew.py
from crewai import Agent, Task, Crew
from crewai.flow import flow, start, listen

class InvestmentDiscoveryCrew:
    """Main crew orchestrating A+ investment discovery."""
    
    @agent
    def etf_discovery_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['etf_discovery_agent'],
            tools=self._get_etf_tools(),
            verbose=True
        )
    
    @agent
    def stock_discovery_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['stock_discovery_agent'],
            tools=self._get_stock_tools(),
            verbose=True
        )
    
    @task
    def etf_discovery_task(self) -> Task:
        return Task(
            config=self.tasks_config['etf_discovery_task'],
            agent=self.etf_discovery_agent(),
            output_pydantic=APlusDiscoveryResult
        )
```

### 2. Tool Architecture

#### A+ Scoring Tool

```python
# src/finwiz/tools/a_plus_scoring_tool.py
from crewai_tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class APlusScoringInput(BaseModel):
    symbol: str = Field(..., description="Asset symbol")
    asset_type: str = Field(..., pattern="^(etf|stock|crypto)$")
    fundamental_data: Dict = Field(..., description="Fundamental metrics")
    market_context: Optional[Dict] = Field(None, description="Market conditions")

class APlusScoringTool(BaseTool):
    name: str = "A+ Investment Scoring Tool"
    description: str = """
    Calculates comprehensive A+ scores for investment candidates using dynamic
    criteria that adapt to market conditions. Integrates with existing FinWiz
    grading system (A+ to F scale).
    """
    
    def _run(self, 
             symbol: str, 
             asset_type: str,
             fundamental_data: dict,
             market_context: dict = None) -> dict:
        """Calculate A+ score with detailed breakdown."""
        
        scorer = self._get_scorer(asset_type)
        market_regime = self._analyze_market_context(market_context)
        
        # Dynamic criteria adjustment based on market conditions
        criteria = self._adjust_criteria_for_market(asset_type, market_regime)
        
        # Calculate component scores
        scores = {
            'fundamental_score': scorer.calculate_fundamental_score(
                fundamental_data, criteria
            ),
            'quality_score': scorer.calculate_quality_score(
                fundamental_data, criteria
            ),
            'risk_score': scorer.calculate_risk_score(
                fundamental_data, market_context
            ),
            'cost_score': scorer.calculate_cost_score(
                fundamental_data, asset_type
            )
        }
        
        # Weighted final score
        final_score = self._calculate_weighted_score(scores, asset_type)
        grade = self._score_to_grade(final_score)
        
        return {
            'symbol': symbol,
            'final_score': final_score,
            'grade': grade,
            'component_scores': scores,
            'criteria_used': criteria,
            'market_context': market_regime,
            'confidence_level': self._calculate_confidence(scores),
            'rationale': self._generate_rationale(scores, criteria)
        }
```

#### Market Screening Tool

```python
# src/finwiz/tools/market_screening_tool.py
class MarketScreeningTool(BaseTool):
    name: str = "Market Screening Tool"
    description: str = """
    Screens large universes of investments using quantitative filters
    to identify A+ candidates efficiently. Supports ETFs, stocks, and crypto.
    """
    
    def _run(self,
             asset_type: str,
             screening_criteria: dict,
             market_region: str = "global",
             max_results: int = 50) -> dict:
        """Screen market for A+ candidates."""
        
        screener = self._get_screener(asset_type)
        
        # Apply quantitative filters
        candidates = screener.screen_universe(
            criteria=screening_criteria,
            region=market_region
        )
        
        # Rank by preliminary A+ potential
        ranked_candidates = self._rank_by_a_plus_potential(candidates)
        
        return {
            'asset_type': asset_type,
            'total_screened': len(candidates),
            'candidates': ranked_candidates[:max_results],
            'screening_criteria': screening_criteria,
            'market_region': market_region
        }
```

### 3. Data Models and Schemas

#### Core Discovery Models

```python
# src/finwiz/schemas/investment_discovery.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class AssetType(str, Enum):
    ETF = "etf"
    STOCK = "stock"
    CRYPTO = "crypto"

class Grade(str, Enum):
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    C_PLUS = "C+"
    C = "C"
    C_MINUS = "C-"
    D = "D"
    F = "F"

class InvestmentCandidate(BaseModel):
    """Represents a potential A+ investment candidate."""
    symbol: str = Field(..., description="Asset symbol")
    name: str = Field(..., description="Full asset name")
    asset_type: AssetType
    current_price: float = Field(..., gt=0)
    market_cap: Optional[float] = Field(None, gt=0)
    preliminary_score: float = Field(..., ge=0, le=1)
    discovery_date: datetime = Field(default_factory=datetime.now)
    
class APlusAnalysis(BaseModel):
    """Complete A+ analysis result for an investment candidate."""
    candidate: InvestmentCandidate
    fundamental_score: float = Field(..., ge=0, le=1)
    technical_score: float = Field(..., ge=0, le=1)
    quality_score: float = Field(..., ge=0, le=1)
    risk_score: float = Field(..., ge=0, le=1)
    final_grade: Grade
    confidence_level: float = Field(..., ge=0, le=1)
    rationale: List[str] = Field(..., min_items=1)
    
class PortfolioImprovement(BaseModel):
    """Represents a suggested portfolio improvement using A+ discoveries."""
    current_holding: Optional[str] = Field(None, description="Current position symbol")
    recommended_replacement: InvestmentCandidate
    expected_grade_improvement: float = Field(..., description="Grade points improvement")
    risk_impact: Dict[str, float] = Field(..., description="Risk metrics impact")
    cost_analysis: Dict[str, float] = Field(..., description="Cost comparison")
    implementation_priority: int = Field(..., ge=1, le=5, description="1=Highest priority")

class APlusDiscoveryResult(BaseModel):
    """Complete result of A+ discovery process."""
    discovery_date: datetime = Field(default_factory=datetime.now)
    asset_type: AssetType
    total_screened: int = Field(..., ge=0)
    a_plus_candidates: List[APlusAnalysis] = Field(..., max_items=20)
    portfolio_improvements: List[PortfolioImprovement] = Field(default_factory=list)
    market_context: Dict[str, any] = Field(default_factory=dict)
    execution_time_seconds: float = Field(..., gt=0)
```

#### Screening Criteria Models

```python
# src/finwiz/schemas/screening_criteria.py
from pydantic import BaseModel, Field
from typing import List, Optional

class ETFScreeningCriteria(BaseModel):
    """Screening criteria specific to ETFs."""
    max_expense_ratio: float = Field(0.15, gt=0, le=2.0)
    min_aum_billions: float = Field(1.0, gt=0)
    max_tracking_error: float = Field(0.002, gt=0, le=0.1)
    min_history_years: int = Field(3, ge=1, le=20)
    required_regions: List[str] = Field(default_factory=list)
    ucits_compliant: bool = Field(True, description="UCITS compliance required")
    
class StockScreeningCriteria(BaseModel):
    """Screening criteria specific to stocks."""
    min_roe: float = Field(0.20, ge=0, le=1.0)
    min_revenue_growth: float = Field(0.15, ge=-1.0, le=5.0)
    max_debt_to_equity: float = Field(0.3, ge=0, le=5.0)
    min_market_cap_billions: float = Field(1.0, gt=0)
    required_free_cash_flow: bool = Field(True)
    min_profit_margin: float = Field(0.10, ge=0, le=1.0)
    
class CryptoScreeningCriteria(BaseModel):
    """Screening criteria specific to cryptocurrencies."""
    min_market_cap_billions: float = Field(10.0, gt=0)
    min_daily_volume_millions: float = Field(500.0, gt=0)
    min_age_months: int = Field(36, ge=1)
    required_institutional_adoption: bool = Field(True)
    max_volatility_90d: float = Field(1.0, gt=0, le=5.0)
```

## Extending the System

### Adding New Asset Types

To add support for a new asset type (e.g., commodities):

1. **Update AssetType enum:**

```python
class AssetType(str, Enum):
    ETF = "etf"
    STOCK = "stock"
    CRYPTO = "crypto"
    COMMODITY = "commodity"  # New asset type
```

1. **Create screening criteria:**

```python
class CommodityScreeningCriteria(BaseModel):
    min_liquidity: float = Field(1000000, gt=0)
    storage_costs_max: float = Field(0.02, ge=0, le=0.1)
    contango_backwardation_neutral: bool = Field(True)
```

1. **Implement scorer:**

```python
class CommodityScorer(BaseScorer):
    def calculate_fundamental_score(self, data: dict, criteria: dict) -> float:
        # Implement commodity-specific fundamental scoring
        pass
```

1. **Add agent configuration:**

```yaml
# config/agents.yaml
commodity_discovery_agent:
  role: "Commodity Market Specialist"
  goal: "Identify A+ grade commodity investments with strong fundamentals"
  backstory: >
    Expert in commodity markets with deep understanding of supply/demand
    dynamics, storage costs, and macroeconomic factors affecting prices.
  tools:
    - commodity_analysis_tool
    - a_plus_scoring_tool
    - commodity_screening_tool
```

### Customizing Scoring Criteria

The scoring system is designed to be flexible and adaptable:

```python
# src/finwiz/scoring/custom_criteria.py
class CustomScoringCriteria:
    """Allows customization of A+ scoring criteria."""
    
    def __init__(self, user_preferences: dict):
        self.preferences = user_preferences
        
    def adjust_etf_criteria(self, base_criteria: ETFScreeningCriteria) -> ETFScreeningCriteria:
        """Adjust ETF criteria based on user preferences."""
        if self.preferences.get('cost_sensitive', False):
            base_criteria.max_expense_ratio *= 0.8  # More strict on costs
            
        if self.preferences.get('risk_averse', False):
            base_criteria.min_aum_billions *= 2  # Require larger funds
            
        return base_criteria
```

### Market Context Integration

The system adapts to market conditions through the MarketContextAnalyzer:

```python
# src/finwiz/analysis/market_context.py
from enum import Enum
from dataclasses import dataclass

class MarketRegime(Enum):
    BULL_MARKET = "bull"
    BEAR_MARKET = "bear"
    SIDEWAYS_MARKET = "sideways"
    HIGH_VOLATILITY = "high_vol"
    LOW_VOLATILITY = "low_vol"

@dataclass
class MacroIndicators:
    inflation_rate: float
    interest_rates: float
    vix_level: float
    yield_curve_slope: float
    dollar_strength_index: float

class MarketContextAnalyzer:
    def get_current_market_regime(self) -> MarketRegime:
        """Identify current market regime based on multiple indicators."""
        indicators = self._fetch_market_indicators()
        
        if indicators.vix_level > 25:
            return MarketRegime.HIGH_VOLATILITY
        elif indicators.yield_curve_slope < 0:
            return MarketRegime.BEAR_MARKET
        # ... additional logic
        
    def adjust_criteria_for_regime(self, 
                                   base_criteria: dict, 
                                   regime: MarketRegime) -> dict:
        """Adjust scoring criteria based on market regime."""
        adjusted = base_criteria.copy()
        
        if regime == MarketRegime.HIGH_VOLATILITY:
            # Emphasize quality and stability
            adjusted['quality_weight'] *= 1.2
            adjusted['volatility_penalty'] *= 1.5
            
        elif regime == MarketRegime.BEAR_MARKET:
            # Focus on defensive characteristics
            adjusted['dividend_yield_bonus'] *= 1.3
            adjusted['debt_penalty'] *= 1.4
            
        return adjusted
```

## Testing Framework

### Unit Testing A+ Components

```python
# tests/unit/test_a_plus_scoring.py
import pytest
from unittest.mock import Mock, patch
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool
from finwiz.schemas.investment_discovery import AssetType

class TestAPlusScoringTool:
    def test_should_return_a_plus_score_when_excellent_etf_metrics(self, mocker):
        # Arrange
        tool = APlusScoringTool()
        mock_data = {
            'expense_ratio': 0.05,
            'aum': 5_000_000_000,
            'tracking_error': 0.001,
            'history_years': 5
        }
        
        # Act
        result = tool._run(
            symbol='VTI',
            asset_type='etf',
            fundamental_data=mock_data
        )
        
        # Assert
        assert result['final_score'] >= 0.95
        assert result['grade'] == 'A+'
        assert 'Low expense ratio' in result['rationale']
        
    def test_should_adjust_criteria_for_high_volatility_market(self, mocker):
        # Arrange
        tool = APlusScoringTool()
        mock_market_context = {'vix_level': 35, 'regime': 'high_volatility'}
        
        # Act
        criteria = tool._adjust_criteria_for_market('stock', mock_market_context)
        
        # Assert
        assert criteria['quality_weight'] > 1.0  # Increased quality emphasis
        assert criteria['volatility_penalty'] > 1.0  # Higher volatility penalty
```

### Integration Testing

```python
# tests/integration/test_discovery_workflow.py
import pytest
from finwiz.crews.investment_discovery_crew import InvestmentDiscoveryCrew

class TestDiscoveryWorkflow:
    @pytest.mark.integration
    def test_should_complete_full_discovery_workflow(self, mocker):
        # Arrange
        mock_market_data = mocker.patch('finwiz.tools.market_screening_tool.get_market_data')
        mock_market_data.return_value = self._get_mock_market_data()
        
        crew = InvestmentDiscoveryCrew()
        
        # Act
        result = crew.kickoff()
        
        # Assert
        assert result.a_plus_candidates
        assert len(result.a_plus_candidates) > 0
        assert all(candidate.final_grade == 'A+' for candidate in result.a_plus_candidates)
```

## Performance Optimization

### Caching Strategy

```python
# src/finwiz/cache/discovery_cache.py
from functools import lru_cache
from typing import Dict, List
import hashlib
import json

class DiscoveryCache:
    """Caches expensive discovery operations."""
    
    @lru_cache(maxsize=1000)
    def get_screening_results(self, 
                              asset_type: str, 
                              criteria_hash: str) -> List[Dict]:
        """Cache screening results for 24 hours."""
        # Implementation with TTL cache
        pass
    
    def _hash_criteria(self, criteria: dict) -> str:
        """Create hash of screening criteria for cache key."""
        return hashlib.md5(
            json.dumps(criteria, sort_keys=True).encode()
        ).hexdigest()
```

### Parallel Processing

```python
# src/finwiz/processing/parallel_discovery.py
import asyncio
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

class ParallelDiscoveryProcessor:
    """Processes multiple asset discoveries in parallel."""
    
    async def discover_all_assets(self, 
                                  asset_types: List[str]) -> Dict[str, any]:
        """Run discovery for multiple asset types in parallel."""
        
        tasks = [
            self._discover_asset_type(asset_type) 
            for asset_type in asset_types
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            asset_type: result 
            for asset_type, result in zip(asset_types, results)
            if not isinstance(result, Exception)
        }
    
    async def _discover_asset_type(self, asset_type: str) -> Dict:
        """Discover A+ candidates for specific asset type."""
        # Implementation with async processing
        pass
```

## Monitoring and Observability

### Performance Metrics

```python
# src/finwiz/monitoring/discovery_metrics.py
from dataclasses import dataclass
from typing import Dict, List
import time

@dataclass
class DiscoveryMetrics:
    discovery_duration_seconds: float
    candidates_screened: int
    a_plus_candidates_found: int
    api_calls_made: int
    cache_hit_rate: float
    
class DiscoveryMonitor:
    """Monitors discovery performance and quality."""
    
    def track_discovery_performance(self, 
                                    asset_type: str, 
                                    metrics: DiscoveryMetrics):
        """Track performance metrics for analysis."""
        # Log to monitoring system
        pass
    
    def calculate_precision_recall(self, 
                                   predictions: List[str], 
                                   actual_performance: List[float]) -> Dict[str, float]:
        """Calculate precision/recall of A+ predictions."""
        # Implementation for model validation
        pass
```

## API Integration

### REST API Endpoints

```python
# src/finwiz/api/discovery_endpoints.py
from fastapi import APIRouter, HTTPException
from finwiz.schemas.investment_discovery import APlusDiscoveryResult
from finwiz.crews.investment_discovery_crew import InvestmentDiscoveryCrew

router = APIRouter(prefix="/api/v1/discovery")

@router.post("/discover/{asset_type}", response_model=APlusDiscoveryResult)
async def discover_a_plus_investments(
    asset_type: str,
    custom_criteria: Optional[Dict] = None
):
    """Discover A+ investments for specified asset type."""
    try:
        crew = InvestmentDiscoveryCrew()
        result = await crew.discover_async(asset_type, custom_criteria)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monitor/{symbol}")
async def monitor_a_plus_status(symbol: str):
    """Monitor current A+ status of an investment."""
    # Implementation for real-time monitoring
    pass
```

## Configuration Management

### Environment Configuration

```python
# src/finwiz/config/discovery_config.py
from pydantic import BaseSettings, Field
from typing import Dict, List

class DiscoveryConfig(BaseSettings):
    """Configuration for A+ discovery system."""
    
    # Scoring thresholds
    a_plus_threshold: float = Field(0.95, ge=0.9, le=1.0)
    confidence_threshold: float = Field(0.8, ge=0.5, le=1.0)
    
    # Performance settings
    max_candidates_per_type: int = Field(50, ge=10, le=200)
    discovery_timeout_seconds: int = Field(600, ge=60, le=3600)
    
    # Market data settings
    data_providers: List[str] = Field(default=['yahoo', 'alpha_vantage'])
    cache_ttl_hours: int = Field(24, ge=1, le=168)
    
    # Regional settings
    default_regions: List[str] = Field(default=['US', 'EU', 'CH'])
    currency_preference: str = Field('USD')
    
    class Config:
        env_file = '.env'
        env_prefix = 'DISCOVERY_'
```

## Deployment Considerations

### Docker Configuration

```dockerfile
# Dockerfile for discovery service
FROM python:3.12-slim

WORKDIR /app

# Install uv package manager
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Set environment variables
ENV PYTHONPATH=/app/src
ENV DISCOVERY_CACHE_TTL_HOURS=24

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "from finwiz.health import check_discovery_health; check_discovery_health()"

# Run discovery service
CMD ["uv", "run", "python", "src/finwiz/main.py", "--discovery"]
```

### Kubernetes Deployment

```yaml
# k8s/discovery-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finwiz-discovery
spec:
  replicas: 2
  selector:
    matchLabels:
      app: finwiz-discovery
  template:
    metadata:
      labels:
        app: finwiz-discovery
    spec:
      containers:
      - name: discovery
        image: finwiz/discovery:latest
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: finwiz-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

## Security Considerations

### API Security

```python
# src/finwiz/security/discovery_auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

async def verify_discovery_access(token: str = Depends(security)):
    """Verify user has access to discovery features."""
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=["HS256"])
        if 'discovery' not in payload.get('permissions', []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Discovery access required"
            )
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
```

### Data Protection

```python
# src/finwiz/security/data_protection.py
from cryptography.fernet import Fernet
import os

class PortfolioDataProtection:
    """Protects sensitive portfolio data during discovery."""
    
    def __init__(self):
        self.cipher = Fernet(os.getenv('PORTFOLIO_ENCRYPTION_KEY'))
    
    def encrypt_portfolio_data(self, portfolio_data: dict) -> bytes:
        """Encrypt portfolio data before processing."""
        return self.cipher.encrypt(json.dumps(portfolio_data).encode())
    
    def decrypt_portfolio_data(self, encrypted_data: bytes) -> dict:
        """Decrypt portfolio data for analysis."""
        return json.loads(self.cipher.decrypt(encrypted_data).decode())
```

---

This developer guide provides comprehensive technical documentation for extending and customizing the A+ Investment Discovery system. For user-facing documentation, see the [User Guide](investment_discovery_user_guide.md).

---

# A+ Scoring Methodology

## A+ Scoring

### Core Principles

1. **Multi-Dimensional Analysis**: Each investment is evaluated across four key dimensions
2. **Dynamic Adaptation**: Criteria adjust based on market conditions and regimes
3. **Asset-Specific Optimization**: Different scoring models for ETFs, stocks, and crypto
4. **Risk-Adjusted Quality**: Emphasis on sustainable, high-quality investments
5. **Quantitative Rigor**: Data-driven approach with statistical validation

### Scoring Framework

**Composite Score Components**:

- **Fundamental Score** (35%): Asset-specific financial metrics
- **Technical Score** (20%): Momentum, trend strength, and technical indicators
- **Quality Score** (30%): Management, governance, structural quality
- **Risk Score** (15%): Risk-adjusted evaluation

**A+ Threshold**: Composite score ≥ 0.95

### Asset-Specific Criteria & Scoring

#### ETFs (A+ Criteria)

- Expense ratio ≤ 0.15% (broad market) or ≤ 0.25% (specialized)
- AUM ≥ $1 billion
- Tracking error ≤ 0.20% (3-year)
- History ≥ 3 years
- UCITS compliant (for European investors)

```python
def calculate_etf_fundamental_score(data: dict) -> float:
    """
    ETF fundamental scoring based on cost efficiency and structure quality.
    """
    expense_score = max(0, 1 - (data['expense_ratio'] / 0.15))
    aum_score = min(1, data['aum'] / 1e9)
    tracking_score = max(0, 1 - (data['tracking_error'] / 0.002))
    history_score = min(1, data['history_years'] / 5)
    
    return (expense_score * 0.4 + aum_score * 0.3 + 
            tracking_score * 0.2 + history_score * 0.1)
```

#### Stocks (A+ Criteria)

- ROE ≥ 20% (maintained 3+ years)
- Revenue growth ≥ 15% annually (5-year)
- Debt/equity ≤ 0.3
- Positive and growing free cash flow
- Dominant market position in growing sector

```python
def calculate_stock_fundamental_score(data: dict) -> float:
    """
    Stock fundamental scoring based on profitability and growth.
    """
    roe_score = min(1, data['roe'] / 0.20)
    growth_score = min(1, data['revenue_growth'] / 0.15)
    debt_score = max(0, 1 - (data['debt_to_equity'] / 0.3))
    fcf_score = 1.0 if data['fcf_positive'] else 0.0
    margin_score = min(1, data['profit_margin'] / 0.10)
    
    return (roe_score * 0.3 + growth_score * 0.25 + debt_score * 0.2 + 
            fcf_score * 0.15 + margin_score * 0.1)
```

#### Crypto (A+ Criteria)

- Market cap ≥ $10 billion
- Daily volume ≥ $500 million
- Institutional adoption proven
- Real utility and use cases
- Active development team

```python
def calculate_crypto_fundamental_score(data: dict) -> float:
    """
    Crypto fundamental scoring based on adoption and utility.
    """
    mcap_score = min(1, data['market_cap'] / 10e9)
    volume_score = min(1, data['daily_volume'] / 500e6)
    age_score = min(1, data['age_months'] / 36)
    adoption_score = 1.0 if data['institutional_adoption'] else 0.0
    utility_score = 1.0 if data['real_utility'] else 0.0
    
    return (mcap_score * 0.3 + volume_score * 0.2 + age_score * 0.2 + 
            adoption_score * 0.15 + utility_score * 0.15)
```

### Dynamic Criteria Adjustment

**Market Regime Adaptation**:

**High Inflation (>4%)**:

- Prioritize real assets (REITs, commodities)
- Emphasize pricing power for stocks
- Adjust nominal growth thresholds

**Rising Interest Rates**:

- Tighten criteria for REITs and utilities
- Favor low-debt companies
- Adjust valuation models

**High Volatility (VIX >25)**:

- Increase quality requirements
- Emphasize defensive characteristics
- Tighten risk score thresholds

### Usage

**Basic Scoring**:

```python
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool

tool = APlusScoringTool()

result = tool._run(
    symbol="VTI",
    asset_type="etf",
    fundamental_data={
        "expense_ratio": 0.03,
        "aum": 300e9,
        "tracking_error": 0.0005,
        "history_years": 20
    },
    market_context={"vix": 18, "inflation": 2.8}
)

print(f"Grade: {result['grade']}")
print(f"A+ Candidate: {result['is_a_plus_candidate']}")
print(f"Composite Score: {result['analysis_summary']['composite_score']:.3f}")
```

**Custom Criteria**:

```python
custom_criteria = {
    "etf_max_expense_ratio": 0.05,  # Stricter
    "stock_min_roe": 0.30           # Higher ROE
}

result = tool._run(
    symbol="SPY",
    asset_type="etf",
    fundamental_data=etf_data,
    custom_criteria=custom_criteria
)
```
