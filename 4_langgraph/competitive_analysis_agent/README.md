# Competitor Analysis Agent

An autonomous LangGraph agent that runs on a weekly schedule, visits your competitors' websites, scrapes pricing/product/blog pages, compares this week's data against last week's, writes a report on what changed, and sends you a push notification summary.

---

## What it does

Each run, for every competitor in `competitors.json`, the agent:

1. **Plans** the analysis for that competitor (`coordinator`)
2. **Scrapes** their pricing, products, and blog pages via a headless browser (`scraper`)
3. **Compares** this week's scrape against last week's saved data (`comparator`)
4. **Evaluates** whether the scrape/comparison was actually good enough, retrying if not (`evaluator`)
5. Moves to the **next competitor** and repeats
6. Once all competitors are done, **writes and saves a report**, then **sends a push notification** summary (`reporter`)

---

## Architecture

The agent is a [LangGraph](https://langchain-ai.github.io/langgraph/) state machine — a graph of nodes (steps) and edges (transitions), rather than one linear script. State flows through every node as a single `CompetitorState` dictionary.

```
START
  |
  v
coordinator ------> scraper <----+
                       |         |
                       v         |
                  scraper_tools--+   (loops until scraper is done)
                       |
                       v
                  comparator <----+
                       |          |
                       v          |
                 comparator_tools-+  (loops until comparator is done)
                       |
                       v
                   evaluator
                    /   |   \
        retry -----+    |    \----- stuck/done ------+
     (back to scraper)  |                             |
                         v                             v
                  next_competitor -------------> reporter <----+
                    |        |                        |        |
        more--------+        +---all done       reporter_tools-+
     (back to                                          |   (loops until reporter is done)
      coordinator)                                     v
                                                        END
```

### Nodes

| Node | Purpose | Uses tools? |
|---|---|---|
| `coordinator` | Picks the next unprocessed competitor, plans the approach | No |
| `scraper` | Visits competitor URLs via Playwright, extracts pricing/products/blog data, saves it | Yes |
| `comparator` | Loads last week's saved data, diffs it against this week's scrape (via `python_repl`) | Yes |
| `evaluator` | An independent LLM call judging whether the work was actually complete; decides retry / move on / give up | No |
| `next_competitor` | Marks the current competitor done, clears working memory for the next one | No |
| `reporter` | Writes the final report, saves it, sends a push notification | Yes |

### Why three separate "tools" nodes?

`scraper`, `comparator`, and `reporter` each call tools, but each needs its own dedicated `ToolNode` (`scraper_tools`, `comparator_tools`, `reporter_tools`) rather than sharing one. If two different nodes shared a single tools node, a tool call from one node could route back to the wrong caller — this was one of the harder bugs to track down during development (see [Design decisions & lessons learned](#design-decisions--lessons-learned) below).

---

## Project structure

```
competitive_analysis_agent/
├── app.py                  # Gradio UI + APScheduler entry point
├── competitor_agent.py     # CompetitorAgent class: state, nodes, graph, run loop
├── competitor_tools.py     # Tool definitions: Playwright, push notifications, JSON storage
├── competitors.json        # Config: which competitors/URLs to track
├── checkpoints.db          # SQLite checkpoint DB (auto-created, gitignore this)
├── sandbox/
│   └── competitors/
│       ├── {name}_latest.json           # Most recent scrape per competitor
│       ├── {name}_{timestamp}.json      # Timestamped historical backups
│       └── reports/
│           └── report_{date}.txt        # Saved weekly reports
└── .env                     # API keys (gitignore this)
```

---

## Setup

### 1. Install dependencies

```bash
pip install langgraph langgraph-checkpoint-sqlite langchain-openai langchain-community \
    langchain-experimental langsmith tenacity playwright python-dotenv gradio \
    apscheduler pydantic --break-system-packages

playwright install chromium
```

### 2. Environment variables

Create a `.env` file:

```
OPENAI_API_KEY=sk-...
SERPER_API_KEY=...
PUSHOVER_TOKEN=...
PUSHOVER_USER=...
LANGCHAIN_API_KEY=...        # optional, for LangSmith tracing
LANGCHAIN_TRACING_V2=true    # optional
```

- **OPENAI_API_KEY** — required, powers all LLM calls
- **SERPER_API_KEY** — powers the `search` tool (Google Serper)
- **PUSHOVER_TOKEN / PUSHOVER_USER** — for weekly push notifications ([pushover.net](https://pushover.net))
- **LANGCHAIN_API_KEY** — optional; enables LangSmith tracing via the `@traceable` decorator

### 3. Configure competitors

Edit `competitors.json`:

```json
{
    "competitors": [
        {
            "name": "apple",
            "url": "https://www.apple.com",
            "check_areas": {
                "pricing": "https://www.apple.com/shop/buy-iphone",
                "products": "https://www.apple.com/newsroom",
                "blog": "https://www.apple.com/newsroom"
            }
        }
    ],
    "check_areas": ["pricing", "products", "blog"],
    "schedule": "weekly",
    "notification_threshold": "any_change"
}
```

> **Note:** `notification_threshold` is defined but not yet wired into the code — see [Known limitations](#known-limitations--future-work).

### 4. Run it

```bash
python app.py
```

This starts a Gradio UI on `http://0.0.0.0:7860` with **Run Now**, **Load Latest Report**, and **Show Config** buttons, plus a background scheduler for the weekly automated run.

---

## How memory works

The agent has **two separate, independent memory systems**:

### 1. LangGraph checkpointing (`AsyncSqliteSaver`)

Every state update is persisted to `checkpoints.db`, keyed by a `thread_id` scoped to the current ISO week (`competitor-analysis-{year}-w{week_number}`). This means:

- If the process crashes mid-run, restarting `python app.py` and running again will **resume from the last checkpoint** rather than starting over — already-completed competitors won't be re-scraped.
- If a checkpoint is detected as **bloated** (more than 50 accumulated messages, a sign of a runaway loop from an earlier bug), the agent automatically discards it and starts that thread fresh instead of resuming broken state.

### 2. Per-competitor scrape history (JSON files)

Independent of LangGraph's checkpointer, `sandbox/competitors/` holds:
- `{name}_latest.json` — always overwritten, the current snapshot used for next week's comparison
- `{name}_{timestamp}.json` — a permanent, growing archive of every scrape ever saved

This is what `comparator` reads from to compute week-over-week differences.

### Message history is reset per competitor

Within a single run, `messages` accumulates as `scraper`/`comparator` call tools and see results — this lets each node "remember" what it already tried. But once a competitor is marked complete, `next_competitor` **clears `messages` entirely** before moving to the next one, so one competitor's tool calls/results can never leak into (or corrupt) the next competitor's context.

---

## Design decisions & lessons learned

This project went through substantial iteration. A few decisions are worth understanding if you're extending it:

- **Tool-calling nodes must preserve message history, not rebuild it fresh each call.** Early versions rebuilt `messages = [SystemMessage(...)]` from scratch every time a node ran, which meant the LLM never saw its own prior tool results and would call the same tool over and over indefinitely. The fix: a shared `_refresh_system_message()` helper that preserves prior messages (including tool results) and only swaps in a fresh system prompt.

- **"Is the work done?" should be checked from actual message history, not inferred from the LLM's behavior.** Trusting the LLM to naturally stop calling tools once it's "done" is unreliable — `reporter` once sent 100 duplicate push notifications because the model kept re-reading its own instructions as a standing order. The fix: explicitly scan message history for `ToolMessage`s confirming each required tool actually ran, and hard-stop (no further LLM call) once confirmed — never leave "are we finished" up to model judgment alone.

- **Never let a router skip past a pending tool call.** OpenAI's API enforces that every tool-call message must be immediately followed by its result message, or the request is rejected outright (a 400 "orphaned tool call" error). Any logic that can "force move on" to the next node must check whether the last message still has an unresolved tool call first — resolving it always takes priority over any retry/round cap.

- **Tool-call round limits belong inside the node, not the router.** A node can force itself to stop calling tools by invoking a `tool_choice="none"`-bound LLM variant, guaranteeing a plain-text response. A router can only choose where to go *based on* what already happened — it can't force the LLM to stop mid-decision, and trying to make it do so is what causes orphaned tool calls.

- **`retry_count` must actually be incremented somewhere.** A retry cap that's checked but never incremented is dead code — worth double-checking any "give up after N attempts" logic actually updates its own counter.

---

## Known limitations & future work

- **Some competitor sites actively block automated browsers.** Samsung's site in particular has returned `net::ERR_ABORTED` during scraping — likely bot detection on headless/cloud traffic rather than a bug in this code. `handle_tool_errors=True` on all `ToolNode`s means this now surfaces as a message the LLM can react to instead of crashing the whole run, but it may still result in incomplete data for that competitor some weeks.
- **`notification_threshold` from `competitors.json` isn't wired up yet.** Currently every run sends a notification regardless of whether anything meaningful changed; filtering by threshold (e.g. only notify on price changes, not cosmetic wording) is a good next step.
- **Diffing is LLM + `python_repl`-driven, not deterministic.** `comparator` asks the LLM to write comparison code fresh each time, which is flexible but token-heavy and occasionally inconsistent. A plain deterministic Python diff function exposed as a tool (with the LLM only used to summarize the result) would be cheaper and more reliable.
- **First run for any competitor will show "no changes."** Until a competitor has at least one prior saved scrape, there's nothing to compare against.

---

## Troubleshooting

**"An assistant message with 'tool_calls' must be followed by tool messages..." (400 error)**
An orphaned tool call — a `checkpoints.db` file with corrupted state from an earlier crash. Stop the app, delete `checkpoints.db*`, and restart.

**Run hangs or times out with no visible progress**
Check the terminal for `[scraper]` / `[comparator]` / `[evaluator routing]` log lines — these show exactly which node is active and how many tool-call rounds have happened. If a node is stuck repeating the same tool call, that's the loop to investigate.

**Editing the code but nothing changes when you re-run**
`python app.py` doesn't hot-reload. Fully stop the process (`Ctrl+C`) and restart it after any code change.

**Verify the file is valid before a full run**
```bash
python3 -m py_compile competitor_agent.py && echo "SYNTAX OK"
```
This catches syntax errors in under a second, instead of discovering them after a 10-minute run times out.

---

## Cost & rate limits

Every run tracks token usage and cost via `get_openai_callback()`, printed at the end of each run. `_invoke_with_retry` wraps graph execution with exponential-backoff retry (`tenacity`) specifically for `RateLimitError`, up to 5 attempts.