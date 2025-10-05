# Investment Discovery Extension Guide

## Overview

This guide provides comprehensive instructions for extending the A+ Investment Discovery system to support new asset classes, custom scoring models, and additional market data sources. The system is designed with extensibility in mind, allowing developers to add new functionality without modifying core components.

## Architecture for Extensions

### Extension Points

The discovery system provides several well-defined extension points:

1. **Asset Type Extensions**: Add support for new asset classes
2. **Scoring Model Extensions**: Implement custom scoring algorithms
3. **Data Provider Extensions**: Integrate new market data sources
4. **Agent Extensions**: Create specialized discovery agents
5. **Criteria Extensions**: Define custom screening criteria
6. **Report Extensions**: Add new report sections and formats

### Core Interfaces

```python
# Base interfaces for extensions
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from finwiz.schemas.investment_discovery import InvestmentCandidate, APlusAnalysis

class AssetTypeExtension(ABC):
    """Base class for asset type extensions."""
    
    @abstractmethod
    def get_asset_type(self) -> str:
        """Return the asset type identifier."""
        pass
    
    @abstractmethod
    def get_screening_criteria(self) -> Dict[str, Any]:
        """Return default screening criteria for this asset type."""
        pass
    
    @abstractmethod
    def calculate_fundamental_score(self, data: Dict[str, Any]) -> float:
        """Calculate fundamental score for this asset type."""
        pass

class ScoringModelExtension(ABC):
    """Base class for custom scoring models."""
    
    @abstractmethod
    def score_investment(self, candidate: InvestmentCandidate, 
                        market_context: Dict[str, Any]) -> APlusAnalysis:
        """Score an investment candidate."""
        pass

class DataProviderExtension(ABC):
    """Base class for data provider extensions."""
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name."""
        pass
    
    @abstractmethod
    def fetch_data(self, symbol: str, asset_type: str) -> Dict[str, Any]:
        """Fetch data for a symbol."""
        pass
```

## Adding New Asset Classes

### Example: Adding Commodities Support

Let's walk through adding support for commodities as a new asset class.

#### Step 1: Define the Asset Type Extension

```python
# src/finwiz/extensions/commodities_extension.py
from typing import Dict, Any, List
from finwiz.extensions.base import AssetTypeExtension
from finwiz.schemas.investment_discovery import InvestmentCandidate
from pydantic import BaseModel, Field

class CommodityScreeningCriteria(BaseModel):
    """Screening criteria specific to commodities."""
    min_liquidity_millions: float = Field(default=100.0, ge=0)
    max_storage_cost_percent: float = Field(default=2.0, ge=0, le=10)
    min_market_cap_billions: float = Field(default=1.0, ge=0)
    require_physical_backing: bool = Field(default=True)
    max_tracking_error: float = Field(default=0.005, ge=0, le=0.1)
    min_history_years: int = Field(default=2, ge=1, le=10)

class CommodityExtension(AssetTypeExtension):
    """Extension for commodity investments (ETFs, futures, etc.)."""
    
    def get_asset_type(self) -> str:
        return "commodity"
    
    def get_screening_criteria(self) -> Dict[str, Any]:
        """Return default screening criteria for commodities."""
        criteria = CommodityScreeningCriteria()
        return criteria.model_dump()
    
    def calculate_fundamental_score(self, data: Dict[str, Any]) -> float:
        """Calculate fundamental score for commodities."""
        
        # Liquidity score (30% weight)
        liquidity_score = min(1.0, data.get('daily_volume', 0) / 100e6)
        
        # Cost efficiency score (25% weight)
        expense_ratio = data.get('expense_ratio', 1.0)
        cost_score = max(0, 1 - (expense_ratio / 0.75))  # Target ≤ 0.75%
        
        # Storage/contango score (20% weight)
        storage_cost = data.get('storage_cost_percent', 5.0)
        storage_score = max(0, 1 - (storage_cost / 2.0))
        
        # Tracking quality score (15% weight)
        tracking_error = data.get('tracking_error', 0.01)
        tracking_score = max(0, 1 - (tracking_error / 0.005))
        
        # Market structure score (10% weight)
        structure_score = 1.0 if data.get('physical_backing', False) else 0.5
        
        # Weighted composite score
        fundamental_score = (
            liquidity_score * 0.30 +
            cost_score * 0.25 +
            storage_score * 0.20 +
            tracking_score * 0.15 +
            structure_score * 0.10
        )
        
        return min(1.0, fundamental_score)
```

#### Step 2: Create Commodity-Specific Tools

```python
# src/finwiz/tools/commodity_analysis_tool.py
from crewai.tools import BaseTool
from typing import Dict, Any
from pydantic import BaseModel, Field

class CommodityAnalysisInput(BaseModel):
    symbol: str = Field(..., description="Commodity symbol (e.g., GLD, SLV, DJP)")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis to perform")

class CommodityAnalysisTool(BaseTool):
    name: str = "Commodity Analysis Tool"
    description: str = """
    Analyzes commodity investments including ETFs, futures, and physical commodity exposure.
    Evaluates storage costs, contango/backwardation, supply/demand dynamics, and inflation hedging properties.
    """
    
    def _run(self, symbol: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analyze commodity investment."""
        
        # Fetch commodity-specific data
        commodity_data = self._fetch_commodity_data(symbol)
        
        # Analyze supply/demand fundamentals
        supply_demand = self._analyze_supply_demand(symbol, commodity_data)
        
        # Evaluate inflation hedging properties
        inflation_hedge = self._evaluate_inflation_hedging(commodity_data)
        
        # Assess storage and carry costs
        carry_analysis = self._analyze_carry_costs(commodity_data)
        
        return {
            'symbol': symbol,
            'commodity_type': commodity_data.get('commodity_type'),
            'fundamental_metrics': {
                'supply_demand_balance': supply_demand['balance_score'],
                'inflation_correlation': inflation_hedge['correlation'],
                'carry_cost_annual': carry_analysis['annual_cost_percent']
            },
            'investment_structure': self._analyze_investment_structure(commodity_data),
            'risk_factors': self._identify_commodity_risks(commodity_data)
        }
```

#### Step 3: Register the Extension

```python
# src/finwiz/extensions/registry.py
from typing import Dict, Type
from finwiz.extensions.base import AssetTypeExtension
from finwiz.extensions.commodities_extension import CommodityExtension

class ExtensionRegistry:
    """Registry for asset type extensions."""
    
    def __init__(self):
        self._extensions: Dict[str, AssetTypeExtension] = {}
        self._register_default_extensions()
    
    def _register_default_extensions(self):
        """Register default extensions."""
        # Register commodity extension
        self.register_extension(CommodityExtension())
    
    def register_extension(self, extension: AssetTypeExtension):
        """Register a new asset type extension."""
        asset_type = extension.get_asset_type()
        self._extensions[asset_type] = extension
        print(f"Registered extension for asset type: {asset_type}")
    
    def get_extension(self, asset_type: str) -> AssetTypeExtension:
        """Get extension for asset type."""
        if asset_type not in self._extensions:
            raise ValueError(f"No extension registered for asset type: {asset_type}")
        return self._extensions[asset_type]

# Global registry instance
extension_registry = ExtensionRegistry()
```

## Custom Scoring Models

### Creating a Custom ESG-Focused Scoring Model

```python
# src/finwiz/extensions/esg_scoring_model.py
from finwiz.extensions.base import ScoringModelExtension
from finwiz.schemas.investment_discovery import InvestmentCandidate, APlusAnalysis
from typing import Dict, Any

class ESGScoringModel(ScoringModelExtension):
    """ESG-focused scoring model that emphasizes sustainability factors."""
    
    def __init__(self, esg_weight: float = 0.4):
        self.esg_weight = esg_weight
        self.traditional_weight = 1.0 - esg_weight
    
    def score_investment(self, candidate: InvestmentCandidate, 
                        market_context: Dict[str, Any]) -> APlusAnalysis:
        """Score investment with ESG emphasis."""
        
        # Get traditional scores
        traditional_scores = self._calculate_traditional_scores(candidate)
        
        # Calculate ESG scores
        esg_scores = self._calculate_esg_scores(candidate)
        
        # Weighted combination
        final_scores = {
            'fundamental_score': (
                traditional_scores['fundamental'] * self.traditional_weight +
                esg_scores['environmental'] * self.esg_weight
            ),
            'technical_score': traditional_scores['technical'],
            'quality_score': (
                traditional_scores['quality'] * self.traditional_weight +
                esg_scores['governance'] * self.esg_weight
            ),
            'risk_score': (
                traditional_scores['risk'] * self.traditional_weight +
                esg_scores['social_risk'] * self.esg_weight
            )
        }
        
        # Calculate composite score
        composite_score = (
            final_scores['fundamental_score'] * 0.35 +
            final_scores['technical_score'] * 0.20 +
            final_scores['quality_score'] * 0.30 +
            final_scores['risk_score'] * 0.15
        )
        
        # Generate ESG-focused rationale
        rationale = self._generate_esg_rationale(esg_scores, traditional_scores)
        
        return APlusAnalysis(
            candidate=candidate,
            fundamental_score=final_scores['fundamental_score'],
            technical_score=final_scores['technical_score'],
            quality_score=final_scores['quality_score'],
            risk_score=final_scores['risk_score'],
            final_grade=self._score_to_grade(composite_score),
            confidence_level=self._calculate_confidence(final_scores, esg_scores),
            rationale=rationale
        )
```

## Adding New Data Providers

### Example: Adding Bloomberg Data Provider

```python
# src/finwiz/extensions/bloomberg_provider.py
from finwiz.extensions.base import DataProviderExtension
from typing import Dict, Any
import requests
from datetime import datetime

class BloombergDataProvider(DataProviderExtension):
    """Bloomberg data provider extension."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.bloomberg.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def get_provider_name(self) -> str:
        return "bloomberg"
    
    def fetch_data(self, symbol: str, asset_type: str) -> Dict[str, Any]:
        """Fetch data from Bloomberg API."""
        
        try:
            # Fetch basic security data
            security_data = self._fetch_security_data(symbol)
            
            # Fetch financial data based on asset type
            if asset_type == 'stock':
                financial_data = self._fetch_stock_financials(symbol)
            elif asset_type == 'etf':
                financial_data = self._fetch_etf_data(symbol)
            elif asset_type == 'commodity':
                financial_data = self._fetch_commodity_data(symbol)
            else:
                financial_data = {}
            
            # Combine all data
            combined_data = {
                **security_data,
                **financial_data,
                'data_provider': 'bloomberg',
                'fetch_timestamp': datetime.now().isoformat()
            }
            
            return combined_data
            
        except Exception as e:
            raise DataProviderError(f"Bloomberg data fetch failed for {symbol}: {e}")
```

## Testing Extensions

### Extension Testing Framework

```python
# tests/extensions/test_extension_framework.py
import pytest
from finwiz.extensions.registry import extension_registry
from finwiz.extensions.commodities_extension import CommodityExtension

class TestExtensionFramework:
    
    def test_commodity_extension_registration(self):
        """Test commodity extension registration."""
        
        # Register extension
        commodity_ext = CommodityExtension()
        extension_registry.register_extension(commodity_ext)
        
        # Verify registration
        assert 'commodity' in extension_registry.get_supported_asset_types()
        
        # Test extension retrieval
        retrieved_ext = extension_registry.get_extension('commodity')
        assert isinstance(retrieved_ext, CommodityExtension)
    
    def test_commodity_scoring(self):
        """Test commodity scoring functionality."""
        
        commodity_ext = CommodityExtension()
        
        # Test data
        test_data = {
            'daily_volume': 150e6,  # $150M daily volume
            'expense_ratio': 0.005,  # 0.5% expense ratio
            'storage_cost_percent': 1.5,  # 1.5% storage cost
            'tracking_error': 0.003,  # 0.3% tracking error
            'physical_backing': True,
            'provider_rating': 4,  # 4/5 rating
            'regulated_exchange': True,
            'transparency_score': 0.8
        }
        
        # Test fundamental scoring
        fundamental_score = commodity_ext.calculate_fundamental_score(test_data)
        assert 0.0 <= fundamental_score <= 1.0
        assert fundamental_score > 0.7  # Should be high for good data
```

## Configuration and Deployment

### Configuration for Extensions

```yaml
# config/extensions.yaml
extensions:
  asset_types:
    - name: "commodity"
      enabled: true
      config:
        min_liquidity_millions: 100.0
        max_storage_cost_percent: 2.0
        require_physical_backing: true
    
    - name: "reit"
      enabled: false  # Disabled for now
      config:
        min_funds_from_operations: 0.05
        max_debt_to_assets: 0.6
  
  scoring_models:
    - name: "esg_focused"
      enabled: true
      config:
        esg_weight: 0.4
        traditional_weight: 0.6
    
    - name: "growth_focused"
      enabled: false
      config:
        growth_weight: 0.5
        quality_weight: 0.3
  
  data_providers:
    - name: "bloomberg"
      enabled: false  # Requires API key
      config:
        timeout_seconds: 30
        retry_attempts: 3
    
    - name: "refinitiv"
      enabled: false
      config:
        timeout_seconds: 45
        cache_ttl_hours: 6
  
  report_extensions:
    - name: "esg_analysis"
      enabled: true
    
    - name: "sector_breakdown"
      enabled: true
    
    - name: "risk_attribution"
      enabled: false
```

---

This extension guide provides a comprehensive framework for extending the A+ Investment Discovery system. The modular architecture allows for easy addition of new asset classes, scoring models, data providers, and report formats while maintaining system stability and performance.
