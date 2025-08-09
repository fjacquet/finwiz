# FinWiz Milestone TODO

Last updated: 2025-08-08T22:52:58+02:00
This document tracks planned enhancements that do not require immediate implementation.

## Milestone: Add 10-K and Sentiment via YAML (No New Python)

- [x] Stock Crew: Add 10-K extraction step in task prompts
  - Locate latest 10-K on sec.gov for each ticker
  - Extract short, cited excerpts for: Business Overview, MD&A, Risk Factors, Liquidity, Segment Info
  - Include SEC URL, section references, and filing date; summarize material Y/Y changes
- [x] Stock Crew: Add OpenAI sentiment classification in prompts
  - Classify headlines/snippets as Positive/Neutral/Negative with confidence (0–1)
  - Return aggregate mean sentiment, counts per label, and top 3 pos/neg headlines with citations and dates
- [x] Report Crew: Update reporter prompt to include “10-K Insights” and “Market Sentiment” sections
  - Reporter remains tool-less and only consumes upstream context per project rules

## Milestone: SEC Filing Search Tool Refactor

- [x] Refactor `src/finwiz/tools/sec_tool.py` into CrewAI `BaseTool` with Pydantic args
- [x] Return structured output (ticker, form_type, filing_url, filed_at, question, excerpts[] with citations)
- [x] Add pytest tests with full mocking (SEC API, requests, unstructured, FAISS, embeddings)
- [x] Add module docstring and robust error handling (lazy imports, clear errors)

## Linting and Tests

- [x] Add missing module/class/dunder docstrings
  - src/finwiz/rag_config.py
  - src/finwiz/tools/file_conversion_tools.py (class HtmlToPdfTool)
  - src/finwiz/tools/save_to_rag_tool.py (__init__)
- [x] Compress one-line docstrings (D200) in Yahoo finance tools
  - src/finwiz/tools/yahoo_finance_company_info_tool.py
  - src/finwiz/tools/yahoo_finance_etf_holdings_tool.py
  - src/finwiz/tools/yahoo_finance_history_tool.py
  - src/finwiz/tools/yahoo_finance_news_tool.py
  - src/finwiz/tools/yahoo_finance_ticker_info_tool.py
- [x] Tests: add module docstrings and `-> None` annotations
  - tests/test_pdf_conversion.py
  - tests/test_rag_tools.py
  - tests/test_stock_crew.py

## Optional (Later): RAG Scoping and Guardrails

- [ ] Keep RAG for curated, slower-changing excerpts (10-K sections, fact sheets)
- [ ] Add retrieval filters (recency window, top_k=3–5), strong metadata (source_url, collected_at, ticker)
- [ ] Avoid storing live prices/news in RAG; prefer live tools instead

## Notes

- All reports must follow docs/output_formatting_guide.md (HTML5, section structure, emojis)
- Final reporting agent must remain tool-less and last task synchronous
