# FinWiz Data Schemas (Pydantic v2)

This folder hosts JSON Schemas exported from Pydantic models in `src/finwiz/schemas/`.

- Reporter input: `ReporterInput`
- Stock contracts: `TenKInsight`, `MarketSentiment`
- Standardized risk: `RiskAssessmentStandardized`
- ETF contracts: `ETFFactsheet`, `ETFTopHolding`
- Crypto contracts: `CryptoThesis`
- Validation contracts: `ValidatedTicker`

Exporter:

```bash
uv run python -m finwiz.schemas.export
```

This writes `*.schema.json` files into this folder.

Examples live under `docs/schemas/examples/`.

These schemas implement change requests CR-2025-08-09-01, CR-2025-08-09-02, and CR-2025-08-09-03 and are enforced with strict Pydantic v2 models (`extra='forbid'`).
