import time
from ddgs import DDGS

def web_search(query, max_results=5):
    """Search the web and return a list of results."""
    for attempt in range(2):
        try:
            results = DDGS().text(query, max_results=max_results)
            if results:
                return [
                    {"title": r["title"], "url": r["href"], "snippet": r["body"]}
                    for r in results
                ]
        except Exception:
            pass
        time.sleep(2)
    return {"note": "No results found. Try a clearly different query."}

if __name__ == "__main__":
    for item in web_search("private villa with pool Karjat Maharashtra"):
        print(item["title"])
        print(item["url"])
        print(item["snippet"])
        print()