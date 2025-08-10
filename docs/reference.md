# FinWiz Technical Reference

This document provides a technical reference for the FinWiz project, covering its architecture, components, and advanced features.

## Project Architecture

FinWiz is built on the [CrewAI](https://github.com/joaomdmoura/crewai) framework and follows a modular architecture designed for extensibility and maintainability.

- **Crews**: The core of the application. Each crew is a specialized team of AI agents designed to perform a specific type of financial analysis (e.g., Crypto, Stocks, ETFs).
- **Agents**: The individual AI workers within a crew. Each agent has a specific role, goal, and set of tools. Agent configurations are defined in `agents.yaml` files.
- **Tasks**: The specific assignments for agents. Tasks define the work to be done, the expected output, and which agent should perform it. Task configurations are defined in `tasks.yaml` files.
- **Tools**: The functions and APIs that agents can use to perform their tasks. This includes web search tools, data scraping tools, and financial data APIs.
- **Flow**: The `crewai.flow` orchestrates the execution of the different crews in a predefined sequence.

## Crews

FinWiz includes the following pre-configured crews:

### 1. Crypto Crew

- **Objective**: To analyze the cryptocurrency market.
- **Tasks**: Performs technical analysis, risk assessment, and develops investment strategies for specified cryptocurrencies.
- **Output**: A detailed report in HTML and PDF formats on the analyzed digital asset.

### 2. Stock Crew

- **Objective**: To research and analyze publicly traded stocks.
- **Tasks**: Conducts market analysis, screens stocks based on predefined criteria, performs technical analysis, and assesses risk.
- **Output**: A report in HTML and PDF formats on promising stock investment opportunities.

### 3. ETF Crew

- **Objective**: To analyze Exchange-Traded Funds (ETFs).
- **Tasks**: Analyzes market trends, screens for suitable ETFs, and assesses risk factors.
- **Output**: A report in HTML and PDF formats with investment strategies for ETFs.

## Customization

You can easily customize FinWiz by modifying the YAML configuration files located in each crew's directory (`src/finwiz/crews/<crew_name>/config/`).

- **To modify an agent**: Edit the `agents.yaml` file. You can change an agent's `role`, `goal`, `backstory`, or assigned `tools`.
- **To modify a task**: Edit the `tasks.yaml` file. You can change a task's `description`, `expected_output`, or the `agent` assigned to it.

## Asynchronous Task Execution

To enhance performance, FinWiz utilizes asynchronous execution for I/O-bound tasks, such as calling external APIs or scraping websites.

### How it Works

Tasks that can run concurrently without waiting for each other are marked with `async_execution=True` in their respective crew definition files (e.g., `src/finwiz/crews/stock_crew/stock_crew.py`). This allows CrewAI to run these tasks in parallel, significantly reducing the total execution time.

### Important Constraint

When using a `Process.sequential` workflow in CrewAI, there is a key limitation:

> **The final task in a sequential crew must be synchronous.**

This means the last task in the sequence cannot have `async_execution=True`. All preceding tasks can be asynchronous. FinWiz's crews are configured to adhere to this rule to ensure the workflow runs correctly. If you modify the task sequence or add new tasks, ensure the final task remains synchronous.

### Final Reporter Tooling Policy

To avoid unintended external calls or research at the reporting stage, the final reporting agent must be configured with an empty tools list. It should only consume upstream context and format the final HTML report according to `docs/output_formatting_guide.md`.

## Available Tools

The agents in FinWiz are equipped with a variety of tools to perform their research, including:

- `SerperDevTool`: For general web searches.
- `FirecrawlScrapeWebsiteTool`: For scraping content from websites.
- `FirecrawlSearchTool`: For searching within a website's content.
- `YoutubeVideoSearchTool`: For finding relevant videos on YouTube.
- `YahooFinanceNewsTool`: For fetching financial news.
- `AlphaVantageNewsSentimentTool`: For structured news and sentiment via Alpha Vantage's NEWS_SENTIMENT endpoint.
- `TwelveDataIndicatorTool`: For technical indicators (RSI, MACD, Bollinger Bands) via Twelve Data.
- `ChartImgTool`: For generating PNG chart images as base64 data URLs via Chart-img. Requires `CHART_IMG_API_KEY`.
- And other specialized financial data tools.

## Environment Variables

These tools require API keys. Create a `.env` file (see `.env.example`) with the following variables:

- `ALPHA_VANTAGE_API_KEY`: API key for Alpha Vantage (used by `AlphaVantageNewsSentimentTool`).
- `TWELVE_DATA_API_KEY`: API key for Twelve Data (used by `TwelveDataIndicatorTool`).
- `CHART_IMG_API_KEY`: API key for Chart-img (used by `ChartImgTool`).
- `CHART_IMG_BASE_URL` (optional): Override base URL for Chart-img; defaults to `https://api.chart-img.com/v1/stock`.

Notes:
- Ensure variable names match exactly. If you previously used `CHARTIMG_API_KEY`, rename it to `CHART_IMG_API_KEY`.

## Testing

- Framework: `pytest`; mocking: `pytest-mock`.
- Structure: place tests under a top-level `tests/` directory using `test_*.py` files.
- Run commands:

```bash
uv run pytest
```

- Use markers to manage scope/speed (e.g., integration tests):

```bash
uv run pytest -m "not integration"
```

- Guidelines:
  - Mock external APIs/tools and filesystem for determinism.
  - Prefer small unit tests, add integration tests for crew flows.
  - Ensure CI runs `uv run pytest` as default.
