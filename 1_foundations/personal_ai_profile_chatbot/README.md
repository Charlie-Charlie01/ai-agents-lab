# 🤖 Personal AI Profile Chatbot

> A conversational AI chatbot that represents a personal profile, answering questions about background, skills, experience, and more. Built with OpenAI's GPT-4o-mini and an automated evaluation system to ensure response quality.

---

## 📌 Overview

The **Personal AI Profile Chatbot** is an AI-powered conversational agent that uses my LinkedIn profile and personal summary as context to answer questions about me. Instead of reading through a resume or LinkedIn page, users can simply **chat** with this bot to learn about my experience, skills, and background. This includes an evaluation pipeline that automatically assesses whether responses are accurate and appropriate.

This is the first project in my **AI Agents Lab** — a growing collection of intelligent agent experiments.


## How It Works

User Question
     ↓
GPT-4o-mini (Personal AI Agent)
     ↓
AI Response
     ↓
Evaluator (GPT-4o-mini)
     ↓
Evaluation Result (is_acceptable + feedback)

---

## ✨ Features

- 📄 **PDF Profile Ingestion** — Automatically reads and extracts text from a LinkedIn PDF export
- 🧠 **OpenAI-Powered** — Uses GPT to understand and respond to questions about my profile
- 💬 **Conversational UI** — Clean, interactive chat interface built with Gradio
- 🔐 **Secure API Key Handling** — Uses `.env` file to keep credentials safe
- 🌐 **Public Sharing** — Easily shareable via Gradio's built-in public link feature
- 📊 **Structured Feedback** — returns is_acceptable (bool) and feedback (str) for every reply
- 🔗 **OpenAI Integration** — powered by GPT-4o-mini for both the agent and evaluator

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core programming language |
| OpenAI API | Language model for chat responses |
| Gradio | Chat user interface |
| PyPDF2 | PDF text extraction |
| python-dotenv | Secure environment variable management |
| Jupyter Notebook | Development environment |

---

## 📁 Project Structure

```
ai-agents-lab/
│
├── me/
│   ├── Profile.pdf        # LinkedIn profile export (PDF)
│   └── summary.txt        # Short professional summary
│
├── chatbot.ipynb          # Main Jupyter Notebook
├── .env                   # API keys (not committed to Git)
├── .gitignore             # Excludes .env and venv
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
```

---

## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Charlie-Charlie01/ai-agents-lab.git
cd ai-agents-lab
```

### 2. Create & Activate a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Your `.env` File
Create a `.env` file in the root directory:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Add Your Profile Files
Place the following in the `me/` folder:
- `Profile.pdf` — your LinkedIn profile exported as PDF
- `summary.txt` — a short written summary about yourself

### 6. Register the Jupyter Kernel
```bash
pip install ipykernel
python -m ipykernel install --user --name=venv --display-name "Python (venv)"
```

### 7. Launch the Notebook
```bash
jupyter notebook chatbot.ipynb
```

---

## 🚀 Usage

1. Open `chatbot.ipynb` in Jupyter or GitHub Codespaces
2. Run all cells in order
3. The Gradio interface will launch at `http://127.0.0.1:7860`
4. Start chatting! Example questions:
   - *"What is Gbenga's current role?"*
   - *"What programming languages does he know?"*
   - *"Tell me about his educational background."*
   - *"Is he experienced in AI and machine learning?"*

To generate a public shareable link:
```python
gr.ChatInterface(chat, type="messages").launch(share=True)
```

---

## 🔒 Security Notes

- **Never commit your `.env` file** to GitHub
- Add `.env` to your `.gitignore`:
```
.env
venv/
__pycache__/
```

---

## 📦 Requirements

Generate or update with:
```bash
pip freeze > requirements.txt
```

Key dependencies:
```
openai
gradio
PyPDF2
python-dotenv
ipykernel
```

---

## 🙋🏽‍♂️ About Me

**Gbenga Ojo** — AI/ML | WordPress Developer | Web Automation Specialist

- 🌍 Lagos, Nigeria
- 💼 IT Specialist at Gidi Real Estate Investment Limited
- 🐙 GitHub: [Charlie-Charlie01](https://github.com/Charlie-Charlie01)
- 🔗 LinkedIn: [gbenga-ojo](https://www.linkedin.com/in/gbenga-ojo-21767430a)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

> *Part of the [AI Agents Lab](https://github.com/Charlie-Charlie01/ai-agents-lab) — a personal collection of AI agent projects by Gbenga Ojo.*