---
title: engineering_team
app_file: app.py
sdk: gradio
sdk_version: 6.14.0
---
# Engineering Team — Powered by CrewAI

A multi-agent AI system that takes your software requirements and automatically generates:
- 📐 **Design Document** — Architecture and class/method breakdown
- 🐍 **Backend Module** — Clean, self-contained Python code
- 🎨 **Gradio UI** — A simple frontend to demo the backend
- 🧪 **Unit Tests** — Ready-to-run test suite

---

## 🤖 How It Works

This project uses **CrewAI** to orchestrate a team of 4 AI agents working sequentially:
Engineering Lead → Backend Engineer → Frontend Engineer
→ Test Engineer


| Agent                 | Role                                          |
|---                    |---                                            |
| 🧠 Engineering Lead | Designs the architecture and module structure |
| 💻 Backend Engineer | Implements the Python module |
| 🎨 Frontend Engineer | Builds a Gradio UI to demo the backend |
| 🧪 Test Engineer | Writes unit tests for the backend |

---

## 🚀 How To Use

1. Enter your **software requirements** in plain English
2. Provide a **module name** (e.g. `accounts.py`)
3. Provide a **class name** (e.g. `Account`)
4. Click **Run Engineering Team**
5. View the generated files across the tabs

---

## 🛠️ Built With

- [CrewAI](https://crewai.com) — Multi-agent orchestration
- [Gradio](https://gradio.app) — UI framework
- [OpenAI GPT-4o](https://openai.com) — LLM powering all agents

---

## ⚠️ Notes

- Generation can take **2–5 minutes** depending on complexity
- All agents use `gpt-4o` — ensure your `OPENAI_API_KEY` is set in Space Secrets
- Generated files are saved to the `output/` directory

---

## 📁 Example Output

Given requirements for a trading account system, the crew generates:
output/
├── accounts_design.md     # Design document
├── accounts.py            # Backend module
├── app.py                 # Gradio demo UI
└── test_accounts.py       # Unit tests


engineering-team/
├── app.py                  # Gradio entry point
├── requirements.txt
├── README.md               # Space metadata
└── engineering_team/
    ├── crew.py
    └── config/
        ├── agents.yaml
        └── tasks.yaml
        
---

## 🔑 Environment Variables

Set these in your Space **Settings → Secrets**:

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key |

---

## 📄 License

MIT
