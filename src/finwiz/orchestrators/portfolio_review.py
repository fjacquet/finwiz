from __future__ import annotations

import csv
import os
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import (
    HoldingDecision,
    PortfolioReview,
)
from finwiz.tools.ticker_validation_tool import TickerExistenceValidationTool

AssetClass = Literal["stock", "etf"]


# --- Configuration helpers ---


def _get_env(name: str, default: str) -> str:
    return (os.getenv(name) or default).strip()


def get_csv_paths() -> tuple[Path, Path]:
    project_root = Path(__file__).resolve().parents[3]
    etf_csv = Path(_get_env("PORTFOLIO_ETF_CSV", str(project_root / "data/etf.csv")))
    stock_csv = Path(_get_env("PORTFOLIO_STOCK_CSV", str(project_root / "data/stock.csv")))
    return etf_csv, stock_csv


def get_thresholds() -> tuple[float, float, int]:
    def _f(name: str, default: float) -> float:
        try:
            return float(os.getenv(name, default))
        except Exception:
            return default

    def _i(name: str, default: int) -> int:
        try:
            return int(os.getenv(name, default))
        except Exception:
            return default

    return (
        _f("KEEP_THRESHOLD", 0.55),
        _f("DELTA_THRESHOLD", 0.10),
        _i("MAX_RISK_STEP", 1),
    )


# --- Ingestion & normalization ---


def normalize_ticker(raw: str) -> str:
    s = (raw or "").strip()
    if s.upper().startswith("YAHOO:"):
        return s.split(":", 1)[1]
    return s


@dataclass
class RawHolding:
    asset_class: AssetClass
    name: str
    ticker: str
    currency: str


def read_csv_holdings(path: Path, asset_class: AssetClass) -> list[RawHolding]:
    holdings: list[RawHolding] = []
    if not path.exists():
        return holdings
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Name") or "").strip()
            ticker = normalize_ticker(row.get("Ticker") or "")
            currency = (row.get("Currency") or "").strip()
            if not name or not ticker:
                continue
            holdings.append(RawHolding(asset_class=asset_class, name=name, ticker=ticker, currency=currency))
    return holdings


# --- Validation and basic scoring ---


def validate_symbol(symbol: str, asset_class: AssetClass) -> dict:
    tool = TickerExistenceValidationTool()
    return tool._run(symbol=symbol, asset_class=asset_class)  # use internal run for programmatic call


def basic_composite_score(valid: bool, asset_class: AssetClass) -> float:
    # Placeholder: prefer valid listings; ETFs get slight baseline boost for diversification
    base = 0.6 if valid else 0.0
    if asset_class == "etf" and valid:
        base += 0.05
    return min(base, 1.0)


def basic_risk(valid: bool) -> RiskAssessmentStandardized:
    if valid:
        return RiskAssessmentStandardized(score=2.0, level="Medium", risk_factors=["Baseline placeholder"])
    return RiskAssessmentStandardized(score=5.0, level="Very High", risk_factors=["Invalid or unknown exchange"])


# --- Builder ---


def build_portfolio_review(
    raw_holdings: Iterable[RawHolding],
    *,
    base_currency: str = "CHF",
) -> PortfolioReview:
    keep_threshold, _delta, _max_step = get_thresholds()

    decisions: list[HoldingDecision] = []
    for rh in raw_holdings:
        v = validate_symbol(rh.ticker, rh.asset_class)
        valid = bool(v.get("valid"))
        score = basic_composite_score(valid, rh.asset_class)
        decision = "KEEP" if score >= keep_threshold else "SELL"
        risk = basic_risk(valid)
        rationale: list[str] = []
        if valid:
            rationale.append("Ticker validated on Yahoo; baseline confidence")
        else:
            rationale.append(f"Validation failed: {v.get('reason')}")
        citations: list[str] = []
        src = v.get("meta", {}).get("source")
        if src == "yahoo":
            citations.append("Yahoo Finance")
        elif src == "coinbase":
            citations.append("Coinbase Products API")

        decisions.append(
            HoldingDecision(
                asset_class=rh.asset_class,
                name=rh.name,
                ticker=rh.ticker,
                currency=rh.currency or base_currency,
                decision=decision,  # type: ignore[arg-type]
                composite_score=score,
                risk=risk,
                rationale_bullets=rationale,
                citations=citations,
                alternatives=[],  # placeholder; to be filled by screeners
            )
        )

    return PortfolioReview(
        as_of=datetime.now(UTC),
        base_currency=base_currency,
        holdings=decisions,
    )


# --- I/O helpers ---


def save_review_json(review: PortfolioReview, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(review.model_dump_json(indent=2), encoding="utf-8")


def run() -> Path:
    etf_csv, stock_csv = get_csv_paths()
    etfs = read_csv_holdings(etf_csv, "etf")
    stocks = read_csv_holdings(stock_csv, "stock")
    review = build_portfolio_review([*etfs, *stocks])

    project_root = Path(__file__).resolve().parents[3]
    out = project_root / "output" / "portfolio" / "portfolio_review.json"
    save_review_json(review, out)
    return out


if __name__ == "__main__":
    path = run()
    print(f"Portfolio review saved to: {path}")
