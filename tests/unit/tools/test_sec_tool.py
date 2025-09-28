from finwiz.tools.sec_tool import SECFilingSearchTool


def test_missing_api_key(monkeypatch):
    """Returns a clear error when SEC_API_API_KEY is missing."""
    monkeypatch.delenv("SEC_API_API_KEY", raising=False)
    tool = SECFilingSearchTool()
    out = tool._run(ticker="AAPL", form_type="10-K", question="risk", top_k=2)
    assert isinstance(out, dict)
    assert "error" in out
    assert "SEC_API_API_KEY" in out["error"]


def test_successful_search_with_mocks(monkeypatch):
    """Happy path with mocked external dependencies and retrieval."""
    monkeypatch.setenv("SEC_API_API_KEY", "dummy")

    # Mock SEC Query API
    class DummyQueryApi:
        def __init__(self, api_key: str):
            self.api_key = api_key

        def get_filings(self, query):
            return {
                "filings": [
                    {
                        "linkToFilingDetails": "http://example.com/filing",
                        "filedAt": "2025-01-01",
                    }
                ]
            }

    monkeypatch.setattr("finwiz.tools.sec_tool.QueryApi", DummyQueryApi)

    # Mock requests.get
    class DummyResp:
        def __init__(self, text: str):
            self.text = text

        def raise_for_status(self):
            return None

    def fake_get(url, headers=None, timeout=None):
        return DummyResp("<html><body><h1>Risk Factors</h1><p>Example risk.</p></body></html>")

    monkeypatch.setattr("finwiz.tools.sec_tool.requests.get", fake_get)

    # Mock partition_html to avoid heavy parsing
    def fake_partition_html(text: str):
        return ["Risk Factors section", "Other section"]

    monkeypatch.setattr("finwiz.tools.sec_tool.partition_html", fake_partition_html)

    # Mock FAISS and OpenAIEmbeddings retrieval pipeline
    class DummyRetriever:
        def get_relevant_documents(self, question, top_k=2):
            class Obj:
                def __init__(self, pc):
                    self.page_content = pc

            return [Obj("Excerpt 1"), Obj("Excerpt 2")][:top_k]

    class DummyFAISS:
        @staticmethod
        def from_documents(docs, embeddings):
            class Container:
                def as_retriever(self_inner):
                    return DummyRetriever()

            return Container()

    monkeypatch.setattr("finwiz.tools.sec_tool.FAISS", DummyFAISS)

    class DummyEmbeddings:
        pass

    monkeypatch.setattr("finwiz.tools.sec_tool.OpenAIEmbeddings", lambda: DummyEmbeddings())

    tool = SECFilingSearchTool()
    out = tool._run(ticker="AAPL", form_type="10-K", question="What are the risks?", top_k=2)

    assert out["ticker"] == "AAPL"
    assert out["form_type"] == "10-K"
    assert out["filing_url"] == "http://example.com/filing"
    assert out["filed_at"] == "2025-01-01"
    assert out["question"] == "What are the risks?"
    assert isinstance(out["excerpts"], list)
    assert len(out["excerpts"]) == 2
    assert out["excerpts"][0]["rank"] == 1
    assert "text" in out["excerpts"][0]
    assert out["excerpts"][0]["source_url"] == "http://example.com/filing"
