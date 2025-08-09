# FinWiz: AI-Powered Financial Research Crews

**FinWiz** is a sophisticated financial analysis platform powered by autonomous AI agents built with the [CrewAI](https://github.com/joaomdmoura/crewai) framework. It leverages specialized crews of AI agents to perform in-depth research and generate comprehensive reports on various financial instruments, including cryptocurrencies, stocks, and ETFs.

## ✨ Features

- **Specialized Research Crews**: Dedicated crews for Crypto, Stocks, and ETFs, each with tailored agents and tasks.
- **Dynamic Configuration**: Agents and tasks are configured via YAML files, allowing for easy customization and extension.
- **Asynchronous Task Execution**: Leverages async operations to significantly speed up I/O-bound tasks like web scraping and API calls, improving overall performance.
- **Real-Time Data Retrieval**: Employs a suite of tools to fetch live data from the web, ensuring analyses are based on the most current information.
- **Structured Output**: Generates detailed reports in HTML and PDF formats, ready for review.
- **Modular and Extendable**: The project is structured to be easily extendable with new crews, agents, or tools.

## 📂 Project Structure

The project follows a modular structure to keep the codebase organized and maintainable:

```text
finwiz/
├── src/finwiz/
│   ├── crews/                # Contains the definitions for each financial crew
│   │   ├── crypto_crew/
│   │   ├── etf_crew/
│   │   └── stock_crew/
│   ├── tools/                # Custom tools for financial analysis and data handling
│   └── utils/                # Utility functions (e.g., config loaders)
├── docs/                     # Project documentation
├── output/                   # Generated reports from the crews
├── .env                      # Environment variables (API keys, etc.)
├── pyproject.toml            # Project dependencies and metadata
└── README.md                 # This file
```

## 🚀 Getting Started

Follow these instructions to set up and run FinWiz on your local machine.

### Prerequisites

- Python 3.10+
- A Python package manager like `pip` with `uv`.
- API keys for any services you wish to use (e.g., Serper, Firecrawl).

### Installation

1. **Clone the repository:**

   ```bash
   git clone <your-repo-url>
   cd finwiz
   ```

2. **Set up environment variables:**

   - If an `.env.example` file exists, copy it to `.env`:

     ```bash
     cp .env.example .env
     ```

   - Open the `.env` file and add your API keys.

3. **Install dependencies:**

   The project uses `uv` for dependency management, and dependencies are defined in `pyproject.toml`.

   ```bash
   uv pip install . # Install the project and its dependencies
   ```

4. **Install WeasyPrint System Dependencies:**

   FinWiz uses WeasyPrint to generate PDF reports from HTML. WeasyPrint requires certain system-level libraries to be installed.

   - **macOS (using Homebrew):**

     ```bash
     brew install pango cairo libffi gdk-pixbuf
     ```

   - **Debian/Ubuntu Linux:**

     ```bash
     sudo apt-get update
     sudo apt-get install python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
     ```

   - **Windows:** Please refer to the [WeasyPrint documentation](https://doc.weasyprint.org/stable/first_steps.html#windows) for installation instructions, typically involving installing GTK+.

### Running the Flow

To kick off the entire financial analysis workflow, run the main flow:

```bash
crewai flow kickoff
```

This command will execute the predefined sequence of crews (Crypto, Stock, ETF) and generate the final reports in both HTML and PDF formats in the `output/` directory.

## 🤖 Crews Overview

FinWiz is composed of several specialized crews:

- **Crypto Crew**: Analyzes the cryptocurrency market, focusing on technical analysis, risk assessment, and investment strategies for specific digital assets.
- **Stock Crew**: Conducts research on publicly traded stocks, performing technical analysis, screening, and risk assessment to identify promising investment opportunities.
- **ETF Crew**: Specializes in Exchange-Traded Funds (ETFs), analyzing market trends, screening for suitable funds, and assessing risk to provide investment strategies.

## ⚡ Performance Enhancements

### Asynchronous Execution

To improve performance, FinWiz leverages asynchronous task execution for I/O-bound operations. Tasks that involve fetching data from the web or calling external APIs are marked with `async_execution=True`.

**Important Note:** When using a `Process.sequential` workflow in CrewAI, the final task in the sequence **must be synchronous**. All other tasks can be asynchronous. This is a current limitation of the framework that FinWiz adheres to.

---

Happy analyzing!


export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH
