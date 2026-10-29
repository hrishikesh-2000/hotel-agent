# STATE (updated 2026-10-29)

## Layout
src/hotel_agent/{schemas,pipeline,agent_loop,agent_loop_async}.py
src/hotel_agent/tools/{search,fetch,fetch_async}.py
app/streamlit_app.py, scripts/learning/{hello,agent_step}.py, docs/

## Done
- Project scaffold, files moved into src/hotel_agent, package installed editable.
- Imports updated in agent_loop, agent_loop_async, pipeline, agent_step.
- app import path corrected and verified in the virtualenv.
- schema was hardened to replace bool-based private-pool logic with explicit `private_pool` values and evidence-based fields.
- deterministic `compute_match_score()` was added so ranking is computed in Python instead of trusting model-generated score fields.
- a regression test for schema contract and scoring was added and passed.

## Verification run
- `python -c "import hotel_agent.schemas, hotel_agent.pipeline, hotel_agent.agent_loop, hotel_agent.agent_loop_async; print('OK')"` in the project venv returned `OK`.
- `python -m pytest -q tests/test_schemas.py` -> `2 passed in 0.21s`.

## Remaining issues
- pipeline needs stricter geo filtering and a proper Karjat search script.
- app still needs a dedicated date/budget/children input model if the search plan is to be fully realistic.

## Done (latest)
- Added Jina fallback to async fetch for placeholder/JavaScript pages.
- Added and passed a regression test proving the fetcher retries when the page text is only a placeholder.

## Next steps
1. Tighten search plan and extraction logic with evidence-backed filtering.
2. Write a Karjat search runner and print an evidence table.
3. Add more fixture-based fetch tests for static and JS-heavy pages.

## Known problems (priority order)
1. schemas.py: has_private_pool is a bool (unknown becomes False); match_score is
   model-invented and used for sorting; no evidence/source fields; no contact,
   rating or meals fields; test block at the bottom must be removed.
   Planned: private_pool Literal["yes","no","unknown"], evidence list, contact,
   rating, meals; compute score in Python from facts (pool, capacity, price in budget).
2. fetch_async has no Jina fallback, so JavaScript pages (e.g. elivaas.com) return
   only "Preparing your experience...". The test counting Rs signs on that page
   (max_chars=60000) was never run.
3. pipeline fires 5 DuckDuckGo searches concurrently: likely rate limiting.
   Searches without a region return junk (e.g. "villa Karjat" gave a Helsinki museum);
   add a positive location filter on extracted city.
4. pipeline/app have no date, budget or child inputs; hardcoded Mumbai examples in
   SearchPlan descriptions can leak into a Karjat search (use strict_geo=False).
5. agent_loop.py lost earlier safeguards: system prompt rules, max_tokens,
   honest tool errors, forced final answer when MAX_STEPS is reached.
6. Add check that booking_url values come from pages actually scraped.
7. No tests yet; save sample pages in tests/fixtures.

## Next steps
1. Run the checks above, fix the app import, commit.
2. Fix schemas.py (problem 1), update pipeline.py and the app to match.
3. Add Jina fallback to fetch_async (problem 2).
4. Write scripts/run_pipeline.py for Karjat, 8 adults, Rs 25,000 cap; print a table
   with evidence.