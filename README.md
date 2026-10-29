# Hotel & Villa Research Agent

A Streamlit-based research agent for finding private-pool villas and hotels for group trips and travel planning.

## Goal

This project helps identify suitable properties using:

- search across property portals and travel sources
- concurrent page fetching
- structured extraction of listing facts
- deterministic ranking based on location, guest count, budget, and pool preference
- evidence-backed output for each result

The app is designed for trip planning scenarios where a group wants a property that matches a destination, capacity, budget, and amenity preference.

## Current app

The main UI is in:

- app/streamlit_app.py

It runs a Medallion-style pipeline:

1. Search planning
2. Bronze page ingestion
3. Silver structured extraction
4. Gold comparison table and property cards

The app can be used for different destinations, not only Karjat, and is designed to support a destination + guest count + amenity workflow.

## Tech stack

- Python 3.10+
- Streamlit
- Pydantic
- Asyncio + httpx
- BeautifulSoup
- DuckDuckGo search
- Gemini via OpenAI-compatible endpoint

## Project structure

- app/streamlit_app.py — main Streamlit app
- src/hotel_agent/ — project package
- src/hotel_agent/tools/ — fetch/search tooling
- src/hotel_agent/pipeline.py — research pipeline
- src/hotel_agent/schemas.py — structured output model
- tests/ — focused regression tests
- docs/STATE.md — current project status and known issues
- AGENTS.md — project rules and usage guidance
- ai_travel_agent_engineering_log.md — design history and architecture notes

## Local setup

From the project root:

```powershell
cd "c:\Users\Hrishikesh\projects\hotel-agent"
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

If the venv is not available yet, create it:

```powershell
cd "c:\Users\Hrishikesh\projects\hotel-agent"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .
```

## Environment variables

The app expects a Gemini API key in the environment:

```powershell
$env:GEMINI_API_KEY="your_key_here"
```

Or set it in your shell/profile as needed.

## Run the app locally

```powershell
cd "c:\Users\Hrishikesh\projects\hotel-agent"
.\.venv\Scripts\Activate.ps1
streamlit run app/streamlit_app.py
```

Then open:

- http://localhost:8502

## Run targeted checks

```powershell
cd "c:\Users\Hrishikesh\projects\hotel-agent"
.\.venv\Scripts\python.exe -m pytest -q tests/test_schemas.py tests/test_fetch_async.py
```

## Deployment to Streamlit Cloud

1. Push this repository to GitHub.
2. Open Streamlit Cloud.
3. Create a new app.
4. Select the repo and set the app file to:

```text
app/streamlit_app.py
```

5. Add the secret:

```toml
GEMINI_API_KEY = "your_key_here"
```

6. Deploy.

## Important cautions

This is a research assistant, not a booking engine. Some property sites are JavaScript-heavy and may require fallback fetching. Search and extraction quality can vary by source, so the app should be treated as a decision-support tool rather than a final verified booking source.

Always prefer evidence-backed results over raw model output. Avoid assuming a page is valid unless the listing text actually supports the fact.

## Current status

This repo is in active development. The important working checks are currently:

- package imports pass
- schema tests pass
- async fetch fallback handles placeholder JavaScript pages

See docs/STATE.md for the latest project status and known issues.

## License

This project is for local learning and research use unless a separate license is added.
