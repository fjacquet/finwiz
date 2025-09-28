"""Tests for Perplexity Sonar Search Tool."""

from __future__ import annotations

import json

import pytest

from finwiz.tools.perplexity_search_tool import PerplexitySearchTool


class TestPerplexitySearchTool:
    def setup_method(self) -> None:
        self.tool = PerplexitySearchTool()

    def test_missing_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PPLX_API_KEY", raising=False)

        result = self.tool._run(query="Tell me about AAPL")

        assert result.startswith("Error: PPLX_API_KEY")

    def test_successful_search(self, mocker: pytest.MockFixture, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PPLX_API_KEY", "secret")
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.raise_for_status = mocker.Mock()
        mock_payload = {"output": {"answer": "Apple Inc. overview", "citations": []}}
        mock_response.json.return_value = mock_payload
        mock_post.return_value = mock_response

        result = self.tool._run(
            query="What is happening with Apple stock?",
            model="sonar-small-chat",
            top_k=3,
            search_recency="week",
            search_domain_filter=["sec.gov", "ir.apple.com"],
        )

        assert json.loads(result) == mock_payload

        called_headers = mock_post.call_args.kwargs["headers"]
        called_data = json.loads(mock_post.call_args.kwargs["data"])

        assert called_headers["Authorization"] == "Bearer secret"
        assert called_data["model"] == "sonar-small-chat"
        assert called_data["top_k"] == 3
        assert called_data["search_recency"] == "week"
        assert called_data["search_domain_filter"] == ["sec.gov", "ir.apple.com"]
        assert called_data["messages"][1]["content"] == "What is happening with Apple stock?"

    def test_non_json_response(self, mocker: pytest.MockFixture, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PPLX_API_KEY", "secret")
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.raise_for_status = mocker.Mock()
        mock_response.json.side_effect = ValueError()
        mock_response.text = "plain text"
        mock_post.return_value = mock_response

        result = self.tool._run(query="Explain market trends")

        assert result == "plain text"

    def test_http_error(self, mocker: pytest.MockFixture, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PPLX_API_KEY", "secret")
        mock_post = mocker.patch("requests.post")
        mock_post.side_effect = Exception("network error")

        with pytest.raises(Exception, match="network error"):
            self.tool._run(query="Should I buy TSLA?")
