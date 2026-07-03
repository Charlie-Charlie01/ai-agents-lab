# Sidekick — Personal AI Co-Worker

An autonomous AI agent that browses the internet, completes tasks, evaluates its own work, and loops until the job is done — or asks you for help when it's stuck.

---

## What It Does

You give Sidekick a task and define what "done" looks like. It handles the rest.

- **Browses the web** autonomously using a real Chromium browser via Playwright
- **Searches Google** intelligently before deciding which pages to visit
- **Reads and writes files** to a sandboxed local directory
- **Runs Python code** for calculations and data processing
- **Evaluates its own work** using a second AI judge
- **Retries with feedback** if the work doesn't meet your criteria
- **Asks for help** if it gets stuck or needs clarification
- **Notifies your phone** via Pushover when tasks complete
- **Stops** only when the success criteria is fully met

---

## Architecture

```
START → worker → tools → worker (loop)
               → evaluator → END
                           → worker (retry)
```

### The Three Nodes

| Node | Role |
|---|---|
| **Worker** | Browses the web, runs tools, attempts the task |
| **Tools** | Executes browser actions, searches, file ops, code |
| **Evaluator** | Judges if the work meets the success criteria |

### The Actor-Critic Pattern

Two separate GPT-4o instances with different responsibilities:

```
worker_llm   →  acts  (uses tools to complete the task)
evaluator_llm →  judges (determines if the task is done)
```

The evaluator returns structured feedback via Pydantic:
- `feedback` — what was good or missing
- `success_criteria_met` — stop or retry signal
- `user_input_needed` — pause and ask the user

---

## Project Structure

```
sidekick/
├── app.py              # Gradio UI and entry point
├── sidekick.py         # Sidekick class, graph, nodes, state
├── sidekick_tools.py   # All tool definitions
├── .env                # API keys (never commit this)
├── requirements.txt    # Python dependencies
└── sandbox/            # Agent's read/write directory (auto-created)
```

---

## Tech Stack

| Technology | Purpose |
|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | Graph orchestration and state management |
| [LangChain](https://github.com/langchain-ai/langchain) | LLM wrappers and tool abstractions |
| [OpenAI GPT-4o](https://platform.openai.com) | Worker and evaluator LLMs |
| [Playwright](https://playwright.dev/python/) | Real browser automation |
| [Google Serper](https://serper.dev) | Web search API |
| [Gradio](https://gradio.app) | Chat UI |
| [Pushover](https://pushover.net) | Push notifications |
| [Pydantic](https://docs.pydantic.dev) | Structured evaluator output |
| [MemorySaver](https://langchain-ai.github.io/langgraph/) | In-memory conversation persistence |

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/sidekick.git
cd sidekick
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Playwright browser

```bash
playwright install chromium
```

### 4. Set up environment variables

Copy the `.env` template and fill in your API keys:

```bash
cp .env.example .env
```

```env
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here
PUSHOVER_TOKEN=your_pushover_app_token_here
PUSHOVER_USER=your_pushover_user_key_here
```

| Key | Where to get it |
|---|---|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `SERPER_API_KEY` | [serper.dev](https://serper.dev) — has a free tier |
| `PUSHOVER_TOKEN` | [pushover.net](https://pushover.net) — create an app |
| `PUSHOVER_USER` | Same Pushover account — your user key |

### 5. Run the app

```bash
python app.py
```

Open your browser at `http://127.0.0.1:7860`

---

## How to Use

1. **Type your task** in the first text box
   > e.g. *"Find the top 5 AI news stories from this week"*

2. **Define your success criteria** in the second text box
   > e.g. *"A bullet point summary of each story with a source link"*

3. **Click Go!** and watch Sidekick work

4. **Wait for the response** — Sidekick will browse, evaluate, and retry until done

5. **Click Reset** to start a fresh conversation

---

## Tool Capabilities

| Tool | What the agent can do |
|---|---|
| **Playwright Browser** | Navigate pages, click, fill forms, extract text |
| **Google Search** | Search the web before deciding which pages to visit |
| **Python REPL** | Run calculations and data processing code |
| **File Management** | Read and write files inside the `sandbox/` directory |
| **Push Notifications** | Send alerts to your phone via Pushover |

> ⚠️ **Security note:** The Python REPL executes arbitrary code. Keep this app private or in a sandboxed environment. Do not expose it publicly without proper isolation.

---

## Example Use Cases

- **Research** — *"Summarize the latest developments in quantum computing"*
- **Price tracking** — *"Find the cheapest iPhone 16 Pro across major retailers"*
- **Data gathering** — *"Collect the LinkedIn URLs of the top 10 AI companies"*
- **Monitoring** — *"Check if our website at example.com is loading correctly"*
- **Calculations** — *"Calculate compound interest on $10,000 at 7% over 20 years"*
- **File creation** — *"Research and write a report on renewable energy, save it as a file"*

---

## Known Limitations

- Runs **headless** in containerized environments (Codespaces, Docker) — no visible browser window
- `MemorySaver` is **in-memory only** — conversations reset when the app restarts. Swap for `PostgresSaver` or `RedisSaver` for persistence across restarts
- Wikipedia tool may **fail in restricted networks** — disable it in `sidekick_tools.py` if needed
- No **execution timeout** on the Python REPL — use with caution

---

## Deployment

### Hugging Face Spaces

1. Create a new Space with **Gradio SDK**
2. Add your API keys as **Secrets** in Space Settings
3. Upload `app.py`, `sidekick.py`, `sidekick_tools.py`, and `requirements.txt`
4. Add `packages.txt`:
   ```
   chromium
   ```
5. Add this at the top of `app.py`:
   ```python
   import subprocess
   subprocess.run(["playwright", "install", "chromium"], check=True)
   ```
6. Update `launch()`:
   ```python
   ui.launch(server_name="0.0.0.0", server_port=7860)
   ```

---

## Requirements

```
langchain
langchain-openai
langchain-community
langchain-experimental
langgraph
playwright
gradio
google-search-results
python-dotenv
requests
nest-asyncio
pydantic
```

---

## License

MIT License — feel free to use, modify, and build on this project.

---

## Acknowledgements

Built with guidance from [Ed Donner](https://www.linkedin.com/in/eddonner/)'s work on AI agents and agentic systems.