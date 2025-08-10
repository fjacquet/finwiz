"""Tests for Alpha Vantage News Sentiment Tool."""

from unittest.mock import Mock, patch

from finwiz.tools.alpha_vantage_news_tool import AlphaVantageNewsSentimentTool


class TestAlphaVantageNewsSentimentTool:
    def setup_method(self):
        self.tool = AlphaVantageNewsSentimentTool()

    def test_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
        out = self.tool._run(tickers="AAPL,MSFT")
        assert out.startswith("Error: ALPHA_VANTAGE_API_KEY")

    @patch("requests.get")
    def test_success_with_params(self, mock_get, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "key")
        resp = Mock()
        resp.raise_for_status = Mock()
        resp.text = '{"feed": []}'
        mock_get.return_value = resp

        out = self.tool._run(
            tickers="AAPL,MSFT",
            sort="RELEVANCE",
            time_from="20240101T0000",
            time_to="20240131T2359",
            limit=25,
            topics="technology,financial_markets",
        )
        assert "feed" in out

        called_url = mock_get.call_args[0][0]
        called_params = mock_get.call_args[1]["params"]
        assert "query" in called_url
        assert called_params["function"] == "NEWS_SENTIMENT"
        assert called_params["tickers"] == "AAPL,MSFT"
        assert called_params["sort"] == "RELEVANCE"
        assert called_params["time_from"] == "20240101T0000"
        assert called_params["time_to"] == "20240131T2359"
        assert called_params["limit"] == 25
        assert called_params["topics"] == "technology,financial_markets"
        assert called_params["apikey"] == "key"

    @patch("requests.get")
    def test_request_error(self, mock_get, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "key")
        mock_get.side_effect = Exception("timeout")
        out = self.tool._run(tickers="AAPL")
        assert out.startswith("Error fetching Alpha Vantage news sentiment: ")
