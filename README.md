# FinWiz: AI-Powered Financial Research Crews

Welcome to FinWiz, a multi-agent AI system powered by [crewAI](https://crewai.com) designed to conduct comprehensive financial research. FinWiz deploys specialized crews of AI agents to analyze stocks, ETFs, and cryptocurrencies, culminating in an integrated financial report for a family-focused investment strategy.

## Features

- **Multi-Agent Collaboration:** Utilizes multiple specialized AI agents for in-depth analysis in different financial domains.
- **Specialized Research Crews:** Separate crews for Stocks, ETFs, and Cryptocurrencies, plus a Report crew to synthesize findings.
- **Real-Time Data Integration:** Leverages tools for Yahoo Finance and CoinMarketCap to ensure analyses are based on current market data.
- **Web Research Capabilities:** Equipped with tools like Serper for general web searches and Firecrawl for scraping.
- **Persistent Knowledge Base:** Uses a Retrieval-Augmented Generation (RAG) system for each crew to store and recall information across sessions.
- **Robust and Resilient:** Implements a retry mechanism for LLM calls to handle transient API errors gracefully.

## Project Structure

- **`.env`**: Configuration file for API keys and other secrets.
- **`src/finwiz/`**: Main source code directory.
  - **`crews/`**: Contains the definitions for each specialized crew (`stock_crew`, `etf_crew`, `crypto_crew`, `report_crew`). Each crew has its own `agents.yaml` and `tasks.yaml`.
  - **`tools/`**: Houses all the custom and third-party tools used by the agents.
  - **`main.py`**: The main entry point to orchestrate the FinWiz workflow.
- **`output/`**: Directory where all the final reports from the crews are saved.

## Installation

Ensure you have Python >=3.10 <3.13 installed. This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

1. **Install UV:**

   ```bash
   pip install uv
   ```

2. **Create a Virtual Environment and Install Dependencies:**

   ```bash
   uv venv
   uv pip install -r requirements.txt
   ```

3. **Set up API Keys:**
   - Rename the `.env.example` file to `.env`.
   - Add your API keys to the `.env` file. You will need keys for:
      - `OPENAI_API_KEY`
      - `SERPER_API_KEY`
      - `FIRECRAL_API_KEY`
      - `X-CMC_PRO_API_KEY` (for CoinMarketCap)

## Running the Project

To start the entire FinWiz financial analysis workflow, run the following command from the project's root directory:

```bash
crewai flow kickoff
```

This command will sequentially execute the Crypto, ETF, Stock, and Report crews. The final consolidated report will be saved in the `output/report/` directory.

## Customization

You can customize the behavior of each crew by modifying their configuration files:

- **Agents:** To change the roles, goals, or backstories of the agents, edit the `agents.yaml` file within the respective crew's directory (e.g., `src/finwiz/crews/stock_crew/config/agents.yaml`).
- **Tasks:** To modify the research tasks, edit the `tasks.yaml` file for the desired crew.

## Support

For support, questions, or feedback regarding crewAI:

- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
