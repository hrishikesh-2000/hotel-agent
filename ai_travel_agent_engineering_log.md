# Hotel & Villa Search Agent: Engineering Journey & Concept Log

An engineering log documenting the development of an autonomous travel search agent—from basic tool-augmented LLM calls to concurrent, structured, and production-grade architectures.

## 1. Project Overview & Motivation

* **Goal:** Build an autonomous agent capable of finding, vetting, and structuring private pool villas/hotels based on nuanced human constraints (location, guest count, private pool availability, pricing).

* **Core Technology Stack:**

  * Python 3.10+

  * Google Gemini API (`gemini-3.1-flash-lite` via OpenAI-compatible SDK endpoint)

  * Pydantic v2 (Schema validation & structured outputs)

  * `httpx` & `asyncio` (Concurrent I/O)

  * `BeautifulSoup4` & DuckDuckGo Search (`ddgs`)

  * Streamlit (Gold Layer Analytics UI)

## 2. Architectural Evolution

```
Phase 1: Single Step          Phase 2: ReAct Loop           Phase 3: Structured Extraction      Phase 4: Concurrent Engine        Phase 5: Medallion ETL & UI
┌──────────────┐              ┌──────────────┐              ┌────────────────────────┐          ┌────────────────────────┐        ┌───────────────────────────────┐
│  agent_step  │              │  agent_loop  │              │ agent_loop + Pydantic  │          │   agent_loop_async     │        │ Medallion Pattern             │
│              │              │              │              │                        │          │                        │        │ Planner -> Bronze -> Silver   │
│ 1 tool call  │ ───►         │ Multi-turn   │ ───►         │ 2-phase: discovery     │ ───►     │ AsyncIO + HTTPX Pool   │ ───►   │ + Gold Analytics Dashboard    │
│ & hard exit  │              │ ReAct loop   │              │ then schema parse      │          │ Parallel tool calls    │        │ (Strict Geo-Guards & Split $) │
└──────────────┘              └──────────────┘              └────────────────────────┘          └────────────────────────┘        └───────────────────────────────┘
```

## 3. Key Milestones & Files

### Phase 1: Basic Tool Augmentation (`agent_step.py`)
* **Concept:** Function calling basics.
* **Limitation:** Can only perform one round of tool execution without self-correction.

### Phase 2: The Multi-Step ReAct Loop (`agent_loop.py`)
* **Concept:** The **ReAct (Reason + Act)** pattern bounded by `MAX_STEPS`.
* **Limitation:** Outputs unstructured text/markdown, impossible to integrate cleanly downstream.

### Phase 3: Enforcing Strict Schemas (`schemas.py`)
* **Concept:** Schema-driven output synthesis via Pydantic v2 and `client.beta.chat.completions.parse`. Eliminates markdown hallucinations.

### Phase 4: Concurrency & Latency Optimization (`async_fetch.py`, `agent_loop_async.py`)
* **Concept:** Switched from blocking `requests` to asynchronous `httpx.AsyncClient` with `asyncio.gather()` to fetch multiple property web pages concurrently.

### Phase 5: Medallion ETL Architecture & Analytics UI (`pipeline.py`, `app.py`)
* **Concept:** Transitioned from a naive chatbot loop to a structured data pipeline:
  1. *Stage 1 (Planner):* Generates micro-localities and strict geographic exclusion boundaries (e.g., dropping Alibaug when searching Mumbai).
  2. *Stage 2 (Bronze Ingestion):* Fan-out multi-portal search queries and concurrent URL scraping.
  3. *Stage 3 (Silver Extraction & Filter):* Entity resolution, pricing normalization, and deterministic post-filtering.
  4. *Gold Layer UI:* Telemetry metrics, per-person split calculator (`₹/person/night`), interactive comparison grid, and CSV export.

## 4. Core Concepts & Takeaways

### A. ReAct Pattern vs. Agentic ETL Pipelines
* Naive LLM agents loop open-endedly and often get distracted by SEO listicles.
* Production systems require deterministic DAGs (Planner $\to$ Bronze $\to$ Silver $\to$ Gold) where LLMs handle unstructured extraction/planning, while deterministic Python code handles filtering, deduplication, and schema validation.

### B. Multi-LLM Handoff & Context-Driven Development (CDD)
* When switching between Claude, ChatGPT, and Gemini, relying on chat memory fails.
* **Solution:** Adopt repository-level canonical instructions (`AGENTS.md`, `docs/STATE.md`, `docs/decisions/`) so any incoming LLM instantly inherits architectural guardrails, design decisions, and active task states.

### C. Concurrency in Agent Workflows
* LLM agents are heavily **I/O bound**. Running tools sequentially scales linearly ($O(N \times \text{timeout})$), whereas `asyncio.gather()` flattens execution time to the slowest individual request.

## 5. Next Engineering Objectives
* \[ \] **Price Extraction Robustness:** Handle JS-rendered React state blobs and JSON-LD schema markup for platforms like StayVista and Airbnb.
* \[ \] **Test Fixtures:** Implement offline HTML mock fixtures to ensure deterministic unit testing without hitting live rate limits.
* \[ \] **Async Messaging Gateway:** Wrap the pipeline into a FastAPI webhook for WhatsApp deployment via Twilio.