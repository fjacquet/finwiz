# Getting Started

Get up and running with FinWiz in under 10 minutes.

## Prerequisites

- Python 3.12 or higher
- `uv` package manager (recommended) or `pip`
- API keys for external services

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/finwiz/finwiz.git
cd finwiz
```

### 2. Install Dependencies

Using `uv` (recommended):
```bash
uv sync
```

Using `pip`:
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Required API Keys
OPENAI_API_KEY=sk-proj-your-openai-key
SERPER_API_KEY=your-serper-key
FIRECRAWL_API_KEY=your-firecrawl-key
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key

# Optional API Keys (for enhanced features)
TWELVE_DATA_API_KEY=your-twelve-data-key
PPLX_API_KEY=your-perplexity-key
SEC_API_API_KEY=your-sec-api-key
CHART_IMG_API_KEY=your-chart-img-key
COINMARKETCAP_API_KEY=your-coinmarketcap-key
```

### 4. Verify Installation

```bash
uv run python src/finwiz/main.py --help
```

## Your First Analysis

### Analyze a Single Stock

```bash
uv run python src/finwiz/main.py --ticker AAPL --asset-class stock
```

### Analyze a Portfolio

1. Create a CSV file with your holdings:
```csv
ticker,name,asset_class
AAPL,Apple Inc.,stock
MSFT,Microsoft Corporation,stock
BTC-USD,Bitcoin,crypto
```

2. Run the analysis:
```bash
uv run python src/finwiz/main.py --portfolio holdings.csv
```

### Generate HTML Reports

FinWiz automatically generates professional HTML reports. Find them in the `output/` directory:

- `output/portfolio/portfolio_review.html` - Portfolio analysis
- `output/discovery/a_plus_stocks.html` - Investment opportunities
- `output/backtesting_results_default.html` - Performance analysis

## Next Steps

- **[Developer Guide](developer-guide.md)** - Learn the development workflow
- **[HTML Integration](html-integration.md)** - Customize report generation
- **[API Reference](api-reference.md)** - Explore the full API

## Common Issues

### Missing API Keys
If you see authentication errors, ensure all required API keys are set in your `.env` file.

### Slow Performance
For faster analysis, enable caching:
```bash
export ENABLE_CACHING=true
```

### Rate Limiting
If you hit rate limits, the system will automatically retry with exponential backoff.

## Getting Help

- Check the [Developer Guide](developer-guide.md) for detailed documentation
- Review [API Reference](api-reference.md) for specific function usage
- Open an issue on [GitHub](https://github.com/finwiz/finwiz/issues) for bugs or feature requests