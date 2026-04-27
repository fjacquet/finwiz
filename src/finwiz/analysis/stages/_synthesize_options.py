"""Black-Scholes options-implied scenario probability helpers for the synthesize stage."""

from __future__ import annotations

import os
from typing import Any

from finwiz.schemas.hybrid_analysis.qualitative import ScenarioProbabilities


def _bs_nd2(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes N(d₂): risk-neutral probability that S_T > K."""
    import math

    from scipy.stats import norm  # type: ignore[import-untyped]

    if T <= 0 or sigma <= 0 or S <= 0:
        return 0.5
    d2 = (math.log(S / K) + (r - 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    return float(norm.cdf(d2))


def _compute_options_probabilities(raw_data: dict[str, Any]) -> ScenarioProbabilities | None:
    """Compute options-implied scenario probabilities via Black-Scholes N(d₂).

    Returns None when options IV data is unavailable (crypto, niche ETFs, etc.).
    Priority: options-implied > Python formula > AI guess.
    """
    bull_iv_raw = raw_data.get("options_bull_iv")
    bear_iv_raw = raw_data.get("options_bear_iv")
    t_raw = raw_data.get("options_T")
    s_raw = raw_data.get("current_price")
    if bull_iv_raw is None or bear_iv_raw is None or t_raw is None or s_raw is None:
        return None

    s_val = float(s_raw)
    t_val = float(t_raw)
    bull_val = float(bull_iv_raw)
    bear_val = float(bear_iv_raw)
    r = float(os.getenv("RISK_FREE_RATE", "0.045"))
    p_bull = _bs_nd2(s_val, s_val * 1.20, t_val, r, bull_val)
    p_bear = 1.0 - _bs_nd2(s_val, s_val * 0.85, t_val, r, bear_val)
    p_base = max(0.0, 1.0 - p_bull - p_bear)
    total = p_bull + p_base + p_bear
    return ScenarioProbabilities(
        bull=round(p_bull / total, 2),
        base=round(p_base / total, 2),
        bear=round(p_bear / total, 2),
    )
