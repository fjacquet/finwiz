---
title: Python ABC and Strategy Pattern Standards
inclusion: fileMatch
fileMatchPattern: '*.py*'
---

# Python ABC and Strategy Pattern Standards

## Overview

This document defines standards for using Python's `abc` module (Abstract Base Classes) to implement the Strategy Pattern in FinWiz.

## When to Use Strategy Pattern

Use the Strategy Pattern when you have:

- **Multiple implementations** of the same algorithm for different contexts
- **Conditional logic** that switches between implementations (`if asset_class == "stock"`)
- **Duplicate code** across similar implementations
- **Need for extensibility** - easy to add new strategies without modifying existing code

## Python ABC Module Basics

### Import Pattern

```python
from abc import ABC, abstractmethod
```

### Abstract Base Class Definition

```python
from abc import ABC, abstractmethod
from typing import Any


class AssetAnalyzer(ABC):
    """
    Abstract base class for asset-specific analysis strategies.
    
    All concrete implementations must implement all abstract methods.
    """
    
    @abstractmethod
    def calculate_fundamental_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """
        Calculate fundamental score for this asset type.
        
        Args:
            data: Dictionary containing analysis data
            
        Returns:
            Tuple of (score, details_dict)
        """
        pass
    
    @abstractmethod
    def extract_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract asset-specific metrics from raw data."""
        pass
    
    @abstractmethod
    def validate_data(self, data: dict[str, Any]) -> bool:
        """Validate that required data fields are present."""
        pass
```

### Concrete Implementation

```python
class StockAnalyzer(AssetAnalyzer):
    """Stock-specific implementation of AssetAnalyzer."""
    
    def calculate_fundamental_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """Implement stock-specific scoring logic."""
        # Implementation here
        return score, details
    
    def extract_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract stock-specific metrics."""
        # Implementation here
        return metrics
    
    def validate_data(self, data: dict[str, Any]) -> bool:
        """Validate stock-specific data requirements."""
        # Implementation here
        return is_valid
```

## Factory Pattern Integration

### Factory Class

```python
class AnalyzerFactory:
    """Factory for creating asset-specific analyzers."""
    
    # Registry of available analyzers
    _ANALYZERS = {
        "stock": StockAnalyzer,
        "etf": ETFAnalyzer,
        "crypto": CryptoAnalyzer,
    }
    
    @classmethod
    def get_analyzer(cls, asset_class: str) -> AssetAnalyzer:
        """
        Get the appropriate analyzer for the given asset class.
        
        Args:
            asset_class: Asset class (stock, etf, crypto)
            
        Returns:
            AssetAnalyzer instance for the specified asset class
            
        Raises:
            ValueError: If asset_class is not recognized
        """
        # Normalize asset class to lowercase
        normalized_class = asset_class.lower().strip()
        
        # Look up analyzer class
        analyzer_class = cls._ANALYZERS.get(normalized_class)
        
        if analyzer_class is None:
            valid_classes = ", ".join(cls._ANALYZERS.keys())
            raise ValueError(
                f"Unknown asset class: '{asset_class}'. "
                f"Valid asset classes are: {valid_classes}"
            )
        
        # Instantiate and return analyzer
        return analyzer_class()
```

### Using the Factory

```python
def calculate_score(asset_class: str, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """Calculate score using appropriate analyzer."""
    try:
        # Get analyzer from factory
        analyzer = AnalyzerFactory.get_analyzer(asset_class)
        
        # Delegate to strategy
        return analyzer.calculate_fundamental_score(data)
        
    except ValueError as e:
        # Handle unknown asset class
        logger.warning(f"Unknown asset class: {asset_class} - {e}")
        return 0.5, {"error": str(e)}
```

## Benefits of This Pattern

### Before (Conditional Logic)

```python
def calculate_score(asset_class: str, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """Monolithic function with conditional logic."""
    if asset_class == "stock":
        # 100 lines of stock logic
        roe = data.get("roe", 0.0)
        if roe >= 0.20:
            roe_score = 1.0
        # ... more stock logic
        return stock_score, stock_details
        
    elif asset_class == "etf":
        # 100 lines of ETF logic
        expense_ratio = data.get("expense_ratio", 1.0)
        if expense_ratio <= 0.001:
            expense_score = 1.0
        # ... more ETF logic
        return etf_score, etf_details
        
    elif asset_class == "crypto":
        # 100 lines of crypto logic
        market_cap = data.get("market_cap", 0.0)
        if market_cap >= 100e9:
            cap_score = 1.0
        # ... more crypto logic
        return crypto_score, crypto_details
        
    else:
        return 0.5, {"error": "Unknown asset class"}
```

**Problems:**

- ❌ 300+ lines in one function
- ❌ High cognitive complexity
- ❌ Difficult to test individual strategies
- ❌ Hard to add new asset classes
- ❌ Violates Single Responsibility Principle

### After (Strategy Pattern)

```python
# Orchestrator (simple delegation)
def calculate_score(asset_class: str, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """Delegate to appropriate strategy."""
    analyzer = AnalyzerFactory.get_analyzer(asset_class)
    return analyzer.calculate_fundamental_score(data)

# Each strategy in its own file (50-150 lines each)
class StockAnalyzer(AssetAnalyzer):
    def calculate_fundamental_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        # Only stock logic here
        pass

class ETFAnalyzer(AssetAnalyzer):
    def calculate_fundamental_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        # Only ETF logic here
        pass

class CryptoAnalyzer(AssetAnalyzer):
    def calculate_fundamental_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        # Only crypto logic here
        pass
```

**Benefits:**

- ✅ Each strategy is 50-150 lines (focused)
- ✅ Low cognitive complexity
- ✅ Easy to test each strategy independently
- ✅ Easy to add new asset classes (just add new analyzer)
- ✅ Follows Single Responsibility Principle
- ✅ Follows Open/Closed Principle

## Testing Strategy Pattern

### Test Each Strategy Independently

```python
class TestStockAnalyzer:
    """Test suite for StockAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create StockAnalyzer instance."""
        return StockAnalyzer()
    
    def test_calculate_fundamental_score_excellent_stock(self, analyzer):
        """Test scoring for excellent stock."""
        data = {
            "roe": 0.25,
            "debt_to_equity": 0.2,
            "revenue_growth": 0.30,
            "profit_margin": 0.25,
        }
        
        score, details = analyzer.calculate_fundamental_score(data)
        
        assert score >= 0.9
        assert details["roe_score"] == 1.0
```

### Test Factory

```python
class TestAnalyzerFactory:
    """Test suite for AnalyzerFactory."""
    
    def test_get_analyzer_stock(self):
        """Test getting stock analyzer."""
        analyzer = AnalyzerFactory.get_analyzer("stock")
        assert isinstance(analyzer, StockAnalyzer)
    
    def test_get_analyzer_unknown_asset_class(self):
        """Test error handling for unknown asset class."""
        with pytest.raises(ValueError) as exc_info:
            AnalyzerFactory.get_analyzer("bond")
        
        assert "Unknown asset class" in str(exc_info.value)
```

## Adding New Strategies

To add a new asset class (e.g., "bond"):

1. **Create new analyzer class:**

```python
# src/finwiz/scoring/asset_analyzers/bond_analyzer.py
class BondAnalyzer(AssetAnalyzer):
    """Bond-specific analysis strategy."""
    
    def calculate_fundamental_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        # Bond-specific logic
        pass
    
    def extract_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        # Bond-specific metrics
        pass
    
    def validate_data(self, data: dict[str, Any]) -> bool:
        # Bond-specific validation
        pass
```

2. **Register in factory:**

```python
# src/finwiz/scoring/asset_analyzers/factory.py
from finwiz.scoring.asset_analyzers.bond_analyzer import BondAnalyzer

class AnalyzerFactory:
    _ANALYZERS = {
        "stock": StockAnalyzer,
        "etf": ETFAnalyzer,
        "crypto": CryptoAnalyzer,
        "bond": BondAnalyzer,  # Add new analyzer
    }
```

3. **Write tests:**

```python
# tests/unit/scoring/asset_analyzers/test_bond_analyzer.py
class TestBondAnalyzer:
    def test_calculate_fundamental_score(self):
        # Test bond-specific logic
        pass
```

**That's it!** No changes needed to existing code.

## Common Pitfalls

### ❌ Don't: Forget `@abstractmethod` decorator

```python
class AssetAnalyzer(ABC):
    def calculate_score(self, data: dict[str, Any]) -> float:
        """Missing @abstractmethod - can be instantiated without implementation!"""
        pass
```

### ✅ Do: Use `@abstractmethod` decorator

```python
class AssetAnalyzer(ABC):
    @abstractmethod
    def calculate_score(self, data: dict[str, Any]) -> float:
        """Enforces implementation in subclasses."""
        pass
```

### ❌ Don't: Implement logic in abstract base class

```python
class AssetAnalyzer(ABC):
    @abstractmethod
    def calculate_score(self, data: dict[str, Any]) -> float:
        # Don't put implementation here!
        roe = data.get("roe", 0.0)
        return roe * 0.5
```

### ✅ Do: Keep abstract base class abstract

```python
class AssetAnalyzer(ABC):
    @abstractmethod
    def calculate_score(self, data: dict[str, Any]) -> float:
        """Define interface only - no implementation."""
        pass
```

### ❌ Don't: Forget to implement all abstract methods

```python
class StockAnalyzer(AssetAnalyzer):
    def calculate_score(self, data: dict[str, Any]) -> float:
        return 0.8
    
    # Missing extract_metrics() and validate_data()!
    # Will raise TypeError when instantiated
```

### ✅ Do: Implement all abstract methods

```python
class StockAnalyzer(AssetAnalyzer):
    def calculate_score(self, data: dict[str, Any]) -> float:
        return 0.8
    
    def extract_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        return {}
    
    def validate_data(self, data: dict[str, Any]) -> bool:
        return True
```

## References

- **Python ABC Documentation**: https://docs.python.org/3/library/abc.html
- **Strategy Pattern**: Gang of Four Design Patterns
- **FinWiz Implementation**: `src/finwiz/scoring/asset_analyzers/`

## Example: FinWiz Asset Analyzers

See the complete implementation in:

- `src/finwiz/scoring/asset_analyzers/base.py` - Abstract base class
- `src/finwiz/scoring/asset_analyzers/stock_analyzer.py` - Stock strategy
- `src/finwiz/scoring/asset_analyzers/etf_analyzer.py` - ETF strategy
- `src/finwiz/scoring/asset_analyzers/crypto_analyzer.py` - Crypto strategy
- `src/finwiz/scoring/asset_analyzers/factory.py` - Factory pattern
- `tests/unit/scoring/asset_analyzers/` - Comprehensive test suite

---

**Version**: 1.0  
**Created**: 2025-11-14  
**Purpose**: Standardize Strategy Pattern implementation using Python's ABC module
