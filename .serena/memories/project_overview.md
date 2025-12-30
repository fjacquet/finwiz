# FinWiz Project Overview

## Purpose
FinWiz is an AI-powered financial analysis platform built with CrewAI. It uses autonomous AI agents to perform comprehensive analysis of stocks, ETFs, cryptocurrencies, and portfolios.

## Key Capabilities
- Multi-asset financial analysis (stocks, ETFs, crypto)
- Portfolio review with keep/sell recommendations
- Portfolio rebalancing with optimization
- A+ investment discovery across markets
- Quantitative analysis with Backtrader, TA-Lib, QuantLib
- Batch processing for high-performance portfolio analysis

## Tech Stack
- **Language**: Python 3.12+
- **AI Framework**: CrewAI (agents, crews, flows)
- **Data Validation**: Pydantic v2
- **Package Manager**: uv
- **Testing**: pytest with pytest-mock
- **Type Checking**: mypy
- **Linting/Formatting**: ruff
- **Quantitative Libraries**: Backtrader, TA-Lib, QuantLib, PyPortfolioOpt
- **Data Sources**: Yahoo Finance, Alpha Vantage

## Core Principle: AI Minimalism
Use Python for deterministic tasks, AI only where reasoning is required:
- ✅ AI: Analysis requiring reasoning, synthesis, insights from unstructured data
- ❌ Python: HTML generation, calculations, data validation, templates
