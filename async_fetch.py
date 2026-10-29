import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def clean_html(html_text: str) -> str:
    """Strip markup and non-essential DOM tags to minimize prompt token overhead."""
    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ").split())

async def fetch_page_async(client: httpx.AsyncClient, url: str, max_chars: int = 5000) -> Dict[str, Any]:
    """Fetch and strip a single page with a strict 6-second timeout."""
    try:
        response = await client.get(url, headers=HEADERS, timeout=6.0, follow_redirects=True)
        response.raise_for_status()
        text = clean_html(response.text)
        return {"url": url, "text": text[:max_chars], "status": "ok"}
    except Exception as e:
        return {"url": url, "error": f"{type(e).__name__}: {str(e)}", "status": "failed"}

async def fetch_pages_batch(urls: List[str], max_chars: int = 5000) -> List[Dict[str, Any]]:
    """Concurrently scrape multiple URLs in parallel using an HTTP connection pool."""
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [fetch_page_async(client, url, max_chars) for url in urls]
        return await asyncio.gather(*tasks)