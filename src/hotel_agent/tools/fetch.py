import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

def _plain_fetch(url):
    r = requests.get(url, timeout=5, headers=HEADERS)  # was 15s
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ").split())

def _reader_fetch(url):
    r = requests.get("https://r.jina.ai/" + url, timeout=10, headers=HEADERS)  # was 45s
    r.raise_for_status()
    return r.text

def fetch_page(url, max_chars=6000):
    """Download a web page and return its readable text."""
    text, source = "", "plain"
    try:
        text = _plain_fetch(url)
    except Exception:
        pass
    if len(text) < 800:  # too little text: probably a JavaScript page
        try:
            text = _reader_fetch(url)
            source = "reader"
        except Exception as e:
            if not text:
                return {"error": f"Could not fetch page: {type(e).__name__}"}
    return {"url": url, "source": source, "text": text[:max_chars]}

if __name__ == "__main__":
    out = fetch_page("https://www.elivaas.com/pool-villas/villas-with-pool-in-karjat")
    print("Fetched via:", out.get("source"))
    print(out.get("error") or out["text"][:1500])