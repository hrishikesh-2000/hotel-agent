import pytest

from hotel_agent.tools.fetch_async import fetch_page_async


class FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


class FakeClient:
    def __init__(self):
        self.calls = []

    async def get(self, url, headers=None, timeout=None, follow_redirects=None):
        self.calls.append(url)
        if len(self.calls) == 1:
            return FakeResponse("Preparing your experience... please wait")
        return FakeResponse("Karjat Pool Villa 4 BHK near Khandala with private pool and breakfast included for 8 guests")


@pytest.mark.asyncio
async def test_fetch_page_async_retries_with_jina_when_page_is_placeholder():
    client = FakeClient()
    result = await fetch_page_async(client, "https://example.com/villa")

    assert result["status"] == "ok"
    assert "private pool" in result["text"].lower()
    assert client.calls[0].startswith("https://example.com/villa")
    assert client.calls[1].startswith("https://r.jina.ai/http")
