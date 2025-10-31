"""
Perplexity Sonar Search Tool.

Provides a CrewAI-compatible tool that queries the Perplexity Sonar Search API
and returns grounded results (answer text plus cited sources).
Requires the environment variable `PPLX_API_KEY` to be set with a valid Perplexity API key.
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel

# Import schema from centralized location
from finwiz.schemas.tools import PerplexitySearchInput
from finwiz.utils.api_decorators import api_tool
from finwiz.utils.rate_limiter import APIProvider


class PerplexitySearchTool(BaseTool):
    """Tool that performs a grounded web search using Perplexity Sonar."""

    name: str = "Perplexity Sonar Search"
    description: str = "Queries Perplexity Sonar to obtain grounded answers with citations. Requires the PPLX_API_KEY environment variable."
    args_schema: type[BaseModel] = PerplexitySearchInput

    base_url: str = "https://api.perplexity.ai/chat/completions"

    @api_tool(
        provider=APIProvider.PERPLEXITY,
        endpoint="chat_completions",
        timeout=45.0,
        default_return="Error: Unable to complete Perplexity search",
    )
    def _run(
        self,
        query: str,
        model: str = "sonar-pro",
        top_k: int | None = 5,
        search_recency: str | None = None,
        search_domain_filter: list[str] | None = None,
    ) -> str:
        api_key = os.getenv("PPLX_API_KEY")
        if not api_key:
            return "Error: PPLX_API_KEY environment variable not set."

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": ("You are a financial research assistant. Provide concise, cited answers that include the key facts, figures, and trends relevant to the query."),
                },
                {"role": "user", "content": query},
            ],
            "return_citations": True,
        }

        if top_k is not None:
            payload["top_k"] = top_k
        if search_recency:
            payload["search_recency"] = search_recency
        if search_domain_filter:
            payload["search_domain_filter"] = search_domain_filter

        response = requests.post(self.base_url, headers=headers, data=json.dumps(payload), timeout=30)
        response.raise_for_status()

        try:
            json_payload = response.json()
        except ValueError:
            return response.text

        return json.dumps(json_payload, indent=2, ensure_ascii=False)
