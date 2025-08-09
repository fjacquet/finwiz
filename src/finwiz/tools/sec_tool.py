"""
CrewAI tool for querying and retrieving excerpts from SEC 10-K/10-Q filings.

Provides `SECFilingSearchTool`, a BaseTool with typed inputs and structured
outputs including filing URL, filed date, and cited excerpts.
"""

import os
from typing import Any, Literal

import requests
from crewai.tools import BaseTool
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pydantic import BaseModel, Field

try:  # defer optional dependency
    from unstructured.partition.html import partition_html  # type: ignore
except Exception:  # pragma: no cover - provide a minimal fallback

    def partition_html(text: str) -> list[Any]:  # type: ignore
        """Fallback partitioner: return the raw HTML as a single chunk."""
        return [text]


# Defer importing QueryApi to runtime to keep module import lightweight and testable
QueryApi = None  # will be assigned to sec_api.QueryApi on first use


class SECFilingSearchInput(BaseModel):
    """Input schema for SECFilingSearchTool."""

    ticker: str = Field(..., description="The stock ticker symbol, e.g., AAPL")
    form_type: Literal["10-K", "10-Q"] = Field(..., description="SEC form type to search (10-K or 10-Q)")
    question: str = Field(..., description="What you want to find in the filing (natural language)")
    top_k: int = Field(4, ge=1, le=10, description="Number of excerpts to return")


class SECFilingSearchTool(BaseTool):
    """
    Search the latest SEC filing and extract cited excerpts.

    Extract the most relevant sections from the latest 10-K/10-Q for a ticker.
    Returns a structured dict with ticker, form_type, filing_url, filed_at, and
    a list of excerpts [{rank, text, source_url}].
    """

    name: str = "SEC Filing Search Tool"
    description: str = "Find the latest SEC 10-K or 10-Q for a ticker and return relevant, cited excerpts."
    args_schema: type[BaseModel] = SECFilingSearchInput

    def _run(self, ticker: str, form_type: str, question: str, top_k: int = 4) -> dict[str, Any]:
        """Execute the SEC filing search and retrieval pipeline."""
        try:
            filing = self._fetch_latest_filing(ticker=ticker, form_type=form_type)
            if filing is None:
                return {
                    "error": f"No {form_type} filing found for ticker {ticker}",
                    "ticker": ticker,
                    "form_type": form_type,
                }

            html = self._download_html(filing["filing_url"])  # type: ignore[index]
            docs = self._split_into_documents(html)
            excerpts = self._retrieve_excerpts(docs, question, top_k)

            return {
                "ticker": ticker,
                "form_type": form_type,
                "filing_url": filing["filing_url"],
                "filed_at": filing["filed_at"],
                "question": question,
                "excerpts": [
                    {
                        "rank": i + 1,
                        "text": txt,
                        "source_url": filing["filing_url"],
                    }
                    for i, txt in enumerate(excerpts)
                ],
            }
        except KeyError as e:
            return {"error": f"Missing environment/config: {e}"}
        except Exception as e:  # pragma: no cover - safety net
            return {"error": f"SEC filing search failed: {e}"}

    # ---- Helper methods (isolated for testability) ----
    def _fetch_latest_filing(self, ticker: str, form_type: str) -> dict[str, str] | None:
        api_key = os.environ.get("SEC_API_API_KEY")
        if not api_key:
            raise KeyError("SEC_API_API_KEY")

        # Lazy import to allow tests to patch QueryApi and to avoid hard dependency at import time
        global QueryApi  # type: ignore[global-variable-not-assigned]
        if QueryApi is None:
            try:
                from sec_api import QueryApi as _QueryApi  # type: ignore
            except Exception as e:  # pragma: no cover - surfaced to _run
                raise e
            QueryApi = _QueryApi  # type: ignore

        query_api = QueryApi(api_key=api_key)  # type: ignore[operator]
        query = {
            "query": {"query_string": {"query": f'ticker:{ticker} AND formType:"{form_type}"'}},
            "from": "0",
            "size": "1",
            "sort": [{"filedAt": {"order": "desc"}}],
        }
        filings = query_api.get_filings(query).get("filings", [])
        if not filings:
            return None
        f = filings[0]
        return {
            "filing_url": f.get("linkToFilingDetails", ""),
            "filed_at": f.get("filedAt", ""),
        }

    def _download_html(self, url: str) -> str:
        headers = {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8,"
                "application/signed-exchange;v=b3;q=0.7"
            ),
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.text

    def _split_into_documents(self, html_text: str) -> list[Any]:
        elements = partition_html(text=html_text)
        content = "\n".join([str(el) for el in elements])
        splitter = CharacterTextSplitter(
            separator="\n", chunk_size=2000, chunk_overlap=200, length_function=len
        )
        return splitter.create_documents([content])

    def _retrieve_excerpts(self, docs: list[Any], question: str, top_k: int) -> list[str]:
        retriever = FAISS.from_documents(docs, OpenAIEmbeddings()).as_retriever()
        results = retriever.get_relevant_documents(question, top_k=top_k)
        return [r.page_content for r in results]
