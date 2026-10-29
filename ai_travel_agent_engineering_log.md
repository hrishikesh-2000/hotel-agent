# Hotel & Villa Search Agent: Engineering Journey & Concept Log

An engineering log documenting the development of an autonomous travel search agent—from basic tool-augmented LLM calls to concurrent, structured, and production-grade architectures.

---

## 1. Project Overview & Motivation
- **Goal:** Build an autonomous agent capable of finding, vetting, and structuring private pool villas/hotels based on nuanced human constraints (location, guest count, private pool availability, pricing).
- **Core Technology Stack:** 
  - Python 3.10+
  - Google Gemini API (`gemini-3.1-flash-lite` via OpenAI-compatible SDK endpoint)
  - Pydantic v2 (Schema validation & structured outputs)
  - `httpx` & `asyncio` (Concurrent I/O)
  - `BeautifulSoup4` & DuckDuckGo Search (`ddgs`)

---

## 2. Architectural Evolution

```
Phase 1: Single Step          Phase 2: ReAct Loop           Phase 3: Structured Extraction      Phase 4: Concurrent Engine
┌──────────────┐              ┌──────────────┐              ┌────────────────────────┐          ┌────────────────────────┐
│  agent_step  │              │  agent_loop  │              │ agent_loop + Pydantic  │          │   agent_loop_async     │
│              │              │              │              │                        │          │                        │
│ 1 tool call  │ ───►         │ Multi-turn   │ ───►         │ 2-phase: discovery     │ ───►     │ AsyncIO + HTTPX Pool   │
│ & hard exit  │              │ ReAct loop   │              │ then schema parse      │          │ Parallel tool calls    │
└──────────────┘              └──────────────┘              └────────────────────────┘          └────────────────────────┘
```

---

## 3. Key Milestones & Files

### Phase 1: Basic Tool Augmentation (`agent_step.py`)
- **Concept:** Function calling basics.
- **Workflow:** 
  1. Register a JSON schema describing `web_search`.
  2. Send query to LLM.
  3. If `tool_calls` are requested, parse arguments, run function, and feed the result back for a final answer.
- **Limitation:** Can only perform one round of tool execution. If the initial search yields low-quality links, the agent has no self-correction mechanism.

### Phase 2: The Multi-Step ReAct Loop (`agent_loop.py`)
- **Concept:** The **ReAct (Reason + Act)** pattern.
- **Mechanism:**
  - Standard loop bounded by a safety counter (`MAX_STEPS = 6`).
  - Model reasons $\rightarrow$ chooses tool $\rightarrow$ receives observation $\rightarrow$ evaluates if more information is needed.
  - Terminates automatically when `finish_reason == "stop"` (no further tool calls).
- **Limitation:** Outputs loose Markdown/freeform text. Difficult to feed into downstream databases, apps, or messaging systems.

### Phase 3: Enforcing Strict Schemas (`schemas.py`)
- **Concept:** Schema-driven output synthesis.
- **Why Pydantic?**
  - Enforces strict data types (`int` capacities, `bool` flags, sanitized URLs).
  - Eliminates prompt hallucination of missing fields via `Optional[T]` defaults.
- **Two-Phase Architecture:**
  1. *Exploratory Phase:* Model freely searches (`search_tool.py`) and scrapes web pages (`fetch_tool.py`) accumulating raw conversational context.
  2. *Synthesis Phase:* Once data is gathered, prompt the model with `client.beta.chat.completions.parse(response_format=VillaSearchResponse)` to enforce a typed JSON contract.

### Phase 4: Concurrency & Latency Optimization (`async_fetch.py`, `agent_loop_async.py`)
- **The Bottleneck:** Sequential scraping (`requests.get`) caused 30–60 second latency spikes due to slow external web servers and timeouts.
- **The Solution:**
  - Shifted from `requests` to asynchronous `httpx.AsyncClient`.
  - Upgraded client to `AsyncOpenAI`.
  - Wrapped tool execution in `asyncio.gather()`, resolving multiple external web pages concurrently in parallel tasks.
  - Offloaded synchronous CPU/blocking tasks (like DuckDuckGo) via `asyncio.to_thread()`.

---

## 4. Core Concepts & Takeaways

### A. ReAct Pattern (Reasoning + Acting)
Instead of hardcoding deterministic search logic:
1. Provide the LLM with tool contracts (names, descriptions, parameter schemas).
2. Allow the model to decide *when* to search, *what* query to run, and *when* it has collected sufficient facts to conclude.

### B. Structured Outputs vs. Markdown Extraction
| Approach | Fragility | Parsing Reliability | Downstream Usability |
| :--- | :--- | :--- | :--- |
| Regex / String Splitting | High | Low (breaks on layout changes) | Poor |
| Freeform Markdown | Medium | Medium (unpredictable headings) | Hard to automate |
| **Pydantic Schema Parsing** | **Zero** | **Guaranteed valid JSON** | **Instant DB / API ingest** |

### C. Concurrency in Agent Workflows
- LLM agents are heavily **I/O bound** (waiting on network queries, scraping responses, and API inference).
- Running tools sequentially leads to compounding latency:
  $$\text{Total Latency} = \sum_{i=1}^{n} (\text{Inference}_i + \text{ToolLatency}_i)$$
- Running parallel tool calls via `asyncio.gather` collapses tool wait time to the duration of the single slowest call:
  $$\text{Tool Latency} \approx \max(\text{ToolLatency}_1, \text{ToolLatency}_2, \dots)$$

### D. Web Scraping Defensiveness
- Raw HTML is noisy and expensive in LLM token context.
- Stripping elements (`<script>`, `<style>`, `<nav>`, `<footer>`) drastically reduces token usage and prevents attention dilution.
- Aggressive timeouts ($5\text{–}6\text{s}$) prevent dead links from stalling the entire agent loop.

---

## 5. Next Steps for Production & Portfolio

- [ ] **Streamlit UI:** Build a front-end form (City, Budget, Guests) displaying results in structured property cards.
- [ ] **Real-time Pricing Strategy:** Bridge dynamic pricing gaps using specialized hotel/travel APIs (e.g., SerpApi Google Hotels) instead of static HTML scraping.
- [ ] **Async Messaging Gateway:** Wrap the runner in a FastAPI webhook to power an asynchronous WhatsApp bot via Twilio.