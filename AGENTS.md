# AGENTS.md: Hotel/Villa Research Agent

## Goal
Autonomous research agent that finds 10-20 private-pool villas/hotels and returns
price, contact, food, reviews and other details, each with a source URL and evidence.
Also a learning project: the owner is learning agent-building, so explain what you
change and why, and make one change at a time.

## Real use case
Group stay, 25-26 Dec. Karjat first, otherwise western/coastal Maharashtra within
200 km of Mumbai. 8 adults (children count to be confirmed). Whole-villa budget
about Rs 15,000-25,000 per night. Private pool preferred.

## Environment
Windows, PowerShell, Python 3.14, virtualenv in .venv (activate with
`.venv\Scripts\activate`; if blocked: `Set-ExecutionPolicy -Scope Process RemoteSigned`).
Package installed with `pip install -e .` (src/hotel_agent).
LLM: Gemini via OpenAI-compatible endpoint
(https://generativelanguage.googleapis.com/v1beta/openai/), model gemini-3.1-flash-lite,
key in the GEMINI_API_KEY environment variable. Free tier: low rate limits.
Search: ddgs (DuckDuckGo). Fetch: requests/httpx + BeautifulSoup, Jina Reader
(r.jina.ai) fallback for JavaScript pages.

## Rules
- Never print, log or commit API keys.
- Never guess. Use null or "unknown" when a page does not state something.
- Do not label results "verified" unless something actually verifies them.
- Prefer deterministic Python checks (filters, scoring) over trusting model output.
- Edit files by hand-sized, reviewable changes; do not rewrite files wholesale.
- After any change, run the import checks and tell the owner what to run.
- Update docs/STATE.md at the end of every session.