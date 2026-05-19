# 🔍 Deep Research Agent

An agentic AI system that autonomously researches any topic, synthesizes findings into a detailed report, and delivers it straight to your inbox — all from a clean web interface.

Built with the **OpenAI Agents SDK**, **Gradio**, and **SendGrid**.

---

## What It Does

You type a research query. The agent:

1. **Plans** what to search for — breaking your query into focused sub-questions
2. **Searches** the web in parallel across multiple queries
3. **Writes** a detailed 1000+ word structured markdown report
4. **Emails** the report as a formatted HTML email to your inbox

No manual searching. No copy-pasting. No summarizing. The agents handle everything.

---

## Architecture

```
User Query (Gradio UI)
        │
        ▼
  ResearchManager
        │
        ├──► PlannerAgent     → 3 targeted search queries (with reasoning)
        │
        ├──► SearchAgent × 3  → web summaries (run in parallel)
        │
        ├──► WriterAgent      → full markdown report + summary + follow-up questions
        │
        └──► EmailAgent       → formatted HTML email via SendGrid
```

---

## Agents

| Agent | Model | Role | Tools |
|---|---|---|---|
| `PlannerAgent` | gpt-4o-mini | Breaks query into 3 search terms | — |
| `SearchAgent` | gpt-4o-mini | Searches the web and summarizes results | `WebSearchTool` |
| `WriterAgent` | gpt-4o-mini | Synthesizes summaries into a full report | — |
| `EmailAgent` | gpt-4o-mini | Converts report to HTML and sends email | `send_email` |

---

## Project Structure

```
deep_research_agent/
├── planner_agent.py      # PlannerAgent + WebSearchPlan schema
├── search_agent.py       # SearchAgent with WebSearchTool
├── writer_agent.py       # WriterAgent + ReportData schema
├── email_agent.py        # EmailAgent + send_email function tool
├── research_manager.py   # ResearchManager class — orchestrates the full pipeline
├── app.py                # Gradio web UI — entry point
├── requirements.txt      # Dependencies
└── .env                  # API keys (not committed to version control)
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/deep-research-agent.git
cd deep-research-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=sk-...
SENDGRID_API_KEY=SG...
```

### 4. Run the app

```bash
python app.py
```

The Gradio interface will open automatically in your browser.

---

## Requirements

```
openai-agents>=0.0.12
openai>=1.75.0
gradio
sendgrid
pydantic
python-dotenv
```

---

## Key Technical Decisions

**Parallel search execution**
All searches run simultaneously using `asyncio.as_completed` — cutting total search time by up to 3×. Results are processed as each one finishes, with a live progress counter.

**Structured outputs with Pydantic**
Every agent returns a typed, validated Pydantic object — not raw text. This means no parsing, no guessing, and clean data flowing between agents:
- `PlannerAgent` → `WebSearchPlan`
- `WriterAgent` → `ReportData`

**Async generator for real-time streaming**
`ResearchManager.run_research()` uses `yield` to stream live status updates to the Gradio UI as each pipeline step completes — no loading spinners, no waiting in the dark.

**`tool_choice="required"` on SearchAgent**
Forces the search agent to always call `WebSearchTool` — it can never answer from training data. This ensures research results are always current and sourced from the live web.

**Hosted `WebSearchTool`**
Runs on OpenAI's infrastructure. No external search API keys, no scraping setup required.

**OpenAI Traces**
Every research run generates a unique trace ID and URL, giving full visibility into every agent call, tool use, and handoff in the OpenAI dashboard.

---

## How It Works — Step by Step

### Step 1 — Planning
The `PlannerAgent` receives your query and returns a `WebSearchPlan` — a structured list of 3 search items, each with a `query` string and a `reason` explaining why that search is relevant.

### Step 2 — Searching
The `ResearchManager` fires all 3 searches simultaneously as async tasks. The `SearchAgent` uses `WebSearchTool` to search the web for each query and returns a concise 2-3 paragraph summary. Failed searches are caught gracefully and skipped.

### Step 3 — Writing
The `WriterAgent` receives the original query + all search summaries. It first produces an outline, then writes a full 1000+ word markdown report. The output is a `ReportData` object with three fields:
- `short_summary` — a 2-3 sentence overview
- `markdown_report` — the full report in markdown
- `follow_up_questions` — suggested next research directions

### Step 4 — Emailing
The `EmailAgent` takes the markdown report, converts it to clean, well-presented HTML, writes an appropriate subject line, and sends it via SendGrid.

---

## Gradio UI

The web interface is built with Gradio and supports:
- A text input for your research query
- A primary **Run Research** button
- Pressing **Enter** in the textbox as an alternative trigger
- Live streaming of status updates and the final report as it's generated

---

## Observability

Every run generates a unique trace viewable on the OpenAI platform:

```
https://platform.openai.com/traces/trace?trace_id=<trace_id>
```

This shows every agent call, tool invocation, input, and output across the full pipeline — invaluable for debugging and monitoring in production.

---

## Acknowledgements

Special thanks to **Ed Donner** — whose exceptional teaching made agentic AI concepts finally click. This project would not exist without his guidance and clarity.

---

## License

MIT License — feel free to use, modify, and build on this project.