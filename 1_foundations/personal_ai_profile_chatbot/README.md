# Career Conversation — Personal AI Profile Chatbot

An AI-powered chatbot that represents **Ojo Gbenga Charles** in professional conversations. Built with OpenAI GPT-4o-mini and Gradio, this agent answers career-related questions on your behalf — acting as a smart, always-available representative for potential clients, recruiters, and future employers.

---

## Live Demo

👉 [huggingface.co/spaces/charliehuggingfac3/career_conversation](https://huggingface.co/spaces/charliehuggingfac3/career_conversation)

---

## What It Does

- Answers questions about career history, skills, and professional background
- Reads from a personal LinkedIn profile PDF and a written summary
- Redirects and records off-topic or unanswerable questions via Pushover notifications
- Captures interested users' email addresses for follow-up
- Steers conversations toward meaningful professional engagement

---

## Tech Stack

| Layer | Tool |
|---|---|
| LLM | OpenAI GPT-4o-mini |
| UI | Gradio ChatInterface |
| PDF Parsing | pypdf |
| Notifications | Pushover API |
| Deployment | Hugging Face Spaces |
| Environment | python-dotenv |

---

## Project Structure

```
personal_ai_profile_chatbot/
├── app.py                  # Main chatbot application
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── me/
│   ├── Profile.pdf         # LinkedIn profile exported as PDF
│   └── summary.txt         # Personal career summary
└── personal_ai_profile_chatbot.ipynb   # Original notebook
```

---

## How It Works

The agent uses two custom tools:

- **`record_user_details`** — captures a visitor's name, email, and conversation notes via Pushover notification when they express interest in getting in touch
- **`record_unknown_question`** — logs any off-topic or unanswerable question so it can be reviewed and addressed later

The system prompt constrains the agent strictly to career and professional topics, ensuring it stays on-brand and on-message at all times.

---

## Running Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/Charlie-Charlie01/ai-agents-lab.git
   cd 1_foundations/personal_ai_profile_chatbot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your credentials:
   ```
   OPENAI_API_KEY=your_openai_key
   PUSHOVER_TOKEN=your_pushover_token
   PUSHOVER_USER=your_pushover_user_key
   ```

5. Add your profile files:
   - Export your LinkedIn profile as a PDF → save as `me/Profile.pdf`
   - Write a short career summary → save as `me/summary.txt`

6. Run the app:
   ```bash
   python app.py
   ```

---

## Deploying to Hugging Face Spaces

```bash
gradio deploy
```

Make sure to add your secrets (`OPENAI_API_KEY`, `PUSHOVER_TOKEN`, `PUSHOVER_USER`) in your Space's **Settings → Repository Secrets**.

---

## Author

**Ojo Gbenga Charles**
[Hugging Face](https://huggingface.co/charliehuggingfac3)
