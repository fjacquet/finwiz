# Portfolio Optimization Theory

Mathematical foundations and theoretical concepts underlying FinWiz's portfolio optimization capabilities.

## Modern Portfolio Theory (MPT)

### Core Principles

Modern Portfolio Theory, developed by Harry Markowitz, forms the foundation of quantitative portfolio management:

1. **Risk-Return Trade-off**: Higher expected returns require accepting higher risk
2. **Diversification Benefits**: Combining uncorrelated assets reduces portfolio risk
3. **Efficient Frontier**: Optimal portfolios maximize return for given risk level
4. **Mean-Variance Optimization**: Optimize expected return and variance

### Mathematical Framework

**Expected Portfolio Return**

```
E(Rp) = Σ wi × E(Ri)
```

Where:

- E(Rp) = Expected portfolio return
- wi = Weight of asset i
- E(Ri) = Expected return of asset i

**Portfolio Variance**

```
σp² = Σ Σ wi × wj × σij
```

Where:

- σp² = Portfolio variance
- σij = Covariance between assets i and j

**Sharpe Ratio**

```
Sharpe = (E(Rp) - Rf) / σp
```

Where:

- Rf = Risk-free rate
- σp = Portfolio standard deviation

## Optimization Objectives

### 1. Mean-Variance Optimization

**Objective Function**

```
Maximize: E(Rp) - (λ/2) × σp²
```

Where λ is the risk aversion parameter.

**Constraints**

- Σ wi = 1 (weights sum to 1)
- wi ≥ 0 (no short selling)
- wi ≤ wmax (position limits)

### 2. Risk Parity

**Equal Risk Contribution**

```
RCi = wi × (∂σp/∂wi) = σp/n
```

Where RCi is the risk contribution of asset i.

**Objective**
Minimize the sum of squared deviations from equal risk contribution:

```
Minimize: Σ (RCi - σp/n)²
```

### 3. Black-Litterman Model

**Enhanced Expected Returns**

```
μBL = [(τΣ)⁻¹ + P'Ω⁻¹P]⁻¹ × [(τΣ)⁻¹μ + P'Ω⁻¹Q]
```

Where:

- μBL = Black-Litterman expected returns
- τ = Scaling factor
- Σ = Covariance matrix
- P = Picking matrix (views)
- Ω = Uncertainty matrix
- Q = View returns

## Advanced Optimization Techniques

### 1. Robust Optimization

**Uncertainty Sets**
Account for parameter uncertainty in optimization:

```
Minimize: max{μ∈U} w'μ + λw'Σw
```

Where U represents the uncertainty set for expected returns.

### 2. Factor Models

**Multi-Factor Risk Model**

```
Ri = αi + Σ βik × Fk + εi
```

Where:

- Fk = Factor k return
- βik = Asset i's exposure to factor k
- εi = Idiosyncratic return

**Factor-Based Optimization**

```
σp² = w'BFB'w + w'Dw
```

Where:

- B = Factor exposure matrix
- F = Factor covariance matrix
- D = Specific risk matrix

### 3. Regime-Switching Models

**Markov Regime Switching**

```
P(St = j | St-1 = i) = pij
```

Where St represents the market regime at time t.

**Regime-Dependent Optimization**
Optimize for different market regimes:

- Bull market parameters
- Bear market parameters
- Transition probabilities

## Practical Implementation

### 1. Covariance Matrix Estimation

**Sample Covariance**

```python
import numpy as np

def calculate_sample_covariance(returns):
    """Calculate sample covariance matrix."""
    return np.cov(returns.T)
```

**Shrinkage Estimators**

```python
def ledoit_wolf_shrinkage(returns):
    """Ledoit-Wolf shrinkage estimator."""
    sample_cov = np.cov(returns.T)
    n, p = returns.shape

    # Shrinkage target (identity matrix)
    target = np.trace(sample_cov) / p * np.eye(p)

    # Optimal shrinkage intensity
    shrinkage = calculate_shrinkage_intensity(returns, sample_cov, target)

    return shrinkage * target + (1 - shrinkage) * sample_cov
```

### 2. Expected Return Estimation

**Historical Mean**

```python
def historical_mean_returns(returns, window=252):
    """Calculate historical mean returns."""
    return returns.rolling(window).mean().iloc[-1]
```

**CAPM Expected Returns**

```python
def capm_expected_returns(returns, market_returns, risk_free_rate):
    """Calculate CAPM expected returns."""
    betas = calculate_betas(returns, market_returns)
    market_premium = market_returns.mean() - risk_free_rate

    return risk_free_rate + betas * market_premium
```

### 3. Optimization Solvers

**Quadratic Programming**

```python
import cvxpy as cp

def mean_variance_optimization(mu, Sigma, risk_aversion):
    """Solve mean-variance optimization problem."""
    n = len(mu)
    w = cp.Variable(n)

    # Objective: maximize return - risk penalty
    objective = cp.Maximize(mu.T @ w - 0.5 * risk_aversion * cp.quad_form(w, Sigma))

    # Constraints
    constraints = [
        cp.sum(w) == 1,  # Weights sum to 1
        w >= 0           # Long-only
    ]

    # Solve
    problem = cp.Problem(objective, constraints)
    problem.solve()

    return w.value
```

## Risk Models

### 1. Factor Risk Models

**Fama-French Three-Factor Model**

```
Ri - Rf = αi + βi(Rm - Rf) + siSMB + hiHML + εi
```

Where:

- SMB = Small Minus Big (size factor)
- HML = High Minus Low (value factor)

**Carhart Four-Factor Model**
Adds momentum factor:

```
Ri - Rf = αi + βi(Rm - Rf) + siSMB + hiHML + piPR1YR + εi
```

### 2. Risk Budgeting

**Risk Contribution Calculation**

```python
def calculate_risk_contributions(weights, cov_matrix):
    """Calculate risk contributions for each asset."""
    portfolio_vol = np.sqrt(weights.T @ cov_matrix @ weights)
    marginal_contrib = cov_matrix @ weights / portfolio_vol
    risk_contrib = weights * marginal_contrib

    return risk_contrib / risk_contrib.sum()
```

**Equal Risk Contribution Optimization**

```python
def equal_risk_contribution(cov_matrix):
    """Optimize for equal risk contribution."""
    n = cov_matrix.shape[0]

    def objective(weights):
        risk_contrib = calculate_risk_contributions(weights, cov_matrix)
        target_contrib = 1.0 / n
        return np.sum((risk_contrib - target_contrib) ** 2)

    # Constraints
    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # Sum to 1
        {'type': 'ineq', 'fun': lambda w: w}             # Non-negative
    ]

    # Initial guess
    x0 = np.ones(n) / n

    # Optimize
    result = minimize(objective, x0, constraints=constraints)
    return result.x
```

## Performance Attribution

### 1. Brinson Attribution

**Total Return Decomposition**

```
Rp - Rb = Σ (wi - wbi) × Rbi + Σ wbi × (Ri - Rbi) + Σ (wi - wbi) × (Ri - Rbi)
```

Where:

- Asset Allocation Effect: (wi - wbi) × Rbi
- Security Selection Effect: wbi × (Ri - Rbi)
- Interaction Effect: (wi - wbi) × (Ri - Rbi)

### 2. Factor Attribution

**Factor-Based Performance Attribution**

```python
def factor_attribution(portfolio_returns, factor_returns, factor_loadings):
    """Attribute portfolio performance to factors."""

    # Factor contributions
    factor_contrib = factor_loadings @ factor_returns

    # Specific return (alpha)
    specific_return = portfolio_returns - factor_contrib

    return {
        'factor_contributions': factor_contrib,
        'specific_return': specific_return,
        'total_return': portfolio_returns
    }
```

## Backtesting Framework

### 1. Walk-Forward Analysis

```python
def walk_forward_backtest(returns, optimization_func, window=252, rebalance_freq=21):
    """Perform walk-forward backtesting."""

    results = []

    for t in range(window, len(returns), rebalance_freq):
        # Training data
        train_data = returns.iloc[t-window:t]

        # Optimize portfolio
        weights = optimization_func(train_data)

        # Out-of-sample performance
        oos_returns = returns.iloc[t:t+rebalance_freq]
        portfolio_returns = (oos_returns * weights).sum(axis=1)

        results.append({
            'date': returns.index[t],
            'weights': weights,
            'returns': portfolio_returns
        })

    return results
```

### 2. Performance Metrics

```python
def calculate_performance_metrics(returns):
    """Calculate comprehensive performance metrics."""

    total_return = (1 + returns).prod() - 1
    annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
    volatility = returns.std() * np.sqrt(252)
    sharpe_ratio = annualized_return / volatility

    # Drawdown analysis
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()

    return {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'calmar_ratio': annualized_return / abs(max_drawdown)
    }
```

## Limitations and Considerations

### 1. Model Limitations

**Mean-Variance Optimization Issues**

- Sensitive to input parameters
- Assumes normal return distributions
- Static optimization (single period)
- No transaction costs consideration

**Practical Challenges**

- Parameter estimation error
- Non-stationarity of returns
- Regime changes
- Behavioral factors

### 2. Robust Solutions

**Regularization Techniques**

- L1 regularization (Lasso) for sparsity
- L2 regularization (Ridge) for stability
- Elastic net combining both

**Alternative Approaches**

- Minimum variance portfolios
- Equal-weight portfolios
- Momentum-based strategies
- Fundamental indexing

## Related Documentation

- [Performance Attribution](optimization_theory.md)
- [Investment Methodology](investment_methodology.md)
