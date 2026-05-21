---
title: Job_Application_Agent
app_file: app.py
sdk: gradio
sdk_version: 6.14.0
---
# Job Application Agent

An agentic AI system that takes a job description and your CV, then autonomously analyses the role, researches the company, tailors your CV, writes a personalized cover letter, and sends your complete application, all from a clean web interface.

Built with the **OpenAI Agents SDK**, **Gradio**, and **SendGrid**.

---

## What It Does

You paste a job description and your CV. The agent:

1. **Analyses** the role — extracts skills, keywords, gaps, and match score
2. **Researches** the company — finds recent news, culture, values, and industry trends
3. **Tailors your CV** — rewrites it with ATS keywords specific to this role
4. **Writes a cover letter** — personalized using real company insights, under 400 words
5. **Sends your application** — formatted HTML email delivered via SendGrid

No copy-pasting. No generic templates. No fabricated experience. The agents do the work.

---

## Architecture

```
Job Description + CV (Gradio UI)
           │
           ▼
  JobApplicationManager
           │
           ├──► AnalystAgent       → skills, gaps, match score, ATS keywords
           │
           ├──► ResearchAgent      → company insights, culture, personalization hooks
           │         └── WebSearchTool (4-5 searches)
           │
           ├──► CVTailorAgent      → tailored CV in markdown, before/after sections
           │
           ├──► CoverLetterAgent   → personalized cover letter, under 400 words
           │
           └──► EmailAgent         → HTML email sent via SendGrid
```

---

## Agents

| Agent | Model | Role | Tools |
|---|---|---|---|
| `AnalystAgent` | gpt-4o-mini | Analyses job description vs CV, scores match | — |
| `ResearchAgent` | gpt-4o-mini | Searches company, culture, industry trends | `WebSearchTool` |
| `CVTailorAgent` | gpt-4o | Rewrites CV with ATS keywords for this role | — |
| `CoverLetterAgent` | gpt-4o | Writes personalized cover letter under 400 words | — |
| `EmailAgent` | gpt-4o-mini | Formats and sends the application via SendGrid | `send_email` |

---

## Project Structure

```
job_application_agent/
├── analyst_agent.py       # AnalystAgent + JobAnalysis schema
├── research_agent.py      # ResearchAgent + CompanyResearch schema
├── cv_tailor_agent.py     # CVTailorAgent + TailoredCV schema
├── cover_letter_agent.py  # CoverLetterAgent + CoverLetter schema
├── email_agent.py         # EmailAgent + send_email function tool
├── manager.py             # JobApplicationManager — orchestrates the pipeline
├── app.py                 # Gradio web UI — entry point
├── requirements.txt       # Dependencies
└── .env                   # API keys (not committed to version control)
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/job-application-agent.git
cd job-application-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=sk-...
SENDGRID_API_KEY=SG-...
SENDER_EMAIL=applications@yourdomain.com
RECIPIENT_EMAIL=your@email.com
```

> **SendGrid note:** Your `SENDER_EMAIL` must be a verified sender in your SendGrid account. Visit [sendgrid.com](https://sendgrid.com) to verify.

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

## How It Works — Step by Step

### Stage 1 — Analysis
The `AnalystAgent` reads both the job description and your CV simultaneously. It returns a `JobAnalysis` object containing:
- Required and preferred skills extracted from the job description
- ATS keywords for optimization
- Your strongest matching skills and experiences
- Gaps between your CV and the role
- A match score out of 10
- Suggested CV sections to focus on

### Stage 2 — Company Research
The `ResearchAgent` uses `WebSearchTool` to run 4-5 targeted searches about the company and industry. It returns a `CompanyResearch` object containing:
- Company mission, values, and culture
- Recent news, product launches, or milestones
- Industry trends and challenges
- 3-5 personalization hooks — specific talking points for the cover letter

### Stage 3 — CV Tailoring
The `CVTailorAgent` rewrites your CV using the analyst output and company research. It returns a `TailoredCV` object containing:
- The complete tailored CV in markdown format
- A before/after breakdown of every section modified
- All ATS keywords woven in
- A summary of changes made and why

> **Ethics guardrail:** The agent never fabricates experience or qualifications. It only reframes and reorders what already exists in your original CV.

### Stage 4 — Cover Letter
The `CoverLetterAgent` writes a personalized cover letter using the company research, analyst output, and tailored CV. It returns a `CoverLetter` object containing:
- The complete cover letter in markdown, under 400 words
- A section-by-section breakdown with the strategy behind each paragraph
- The specific company references used
- The tone adopted and why

> **Anti-cliché guardrails:** The agent never uses "I am a team player", "passionate about", "quick learner", or opens with "I am writing to apply for...".

### Stage 5 — Email Delivery
The `EmailAgent` writes a short professional email body, appends the cover letter and tailored CV below it, formats everything as clean HTML, and sends it via SendGrid. The subject line is always specific to the role and company — never generic.

---

## Pydantic Output Schemas

Every agent returns a typed, validated Pydantic object — not raw text:

| Agent | Output Schema | Key Fields |
|---|---|---|
| `AnalystAgent` | `JobAnalysis` | `overall_match_score`, `ats_keywords`, `gaps`, `strongest_selling_points` |
| `ResearchAgent` | `CompanyResearch` | `personalization_hooks`, `company_insights`, `industry_insights` |
| `CVTailorAgent` | `TailoredCV` | `tailored_cv_markdown`, `sections_modified`, `keywords_added` |
| `CoverLetterAgent` | `CoverLetter` | `cover_letter_markdown`, `word_count`, `tone_used`, `personalization_references` |

---

## Gradio UI

The web interface features:
- **Side-by-side inputs** — job description on the left, CV on the right
- **Input validation** — prevents empty runs before the pipeline starts
- **Live streaming output** — status updates appear in real time as each stage completes
- **Accumulated output** — the full log and final report build up in one scrollable view
- **Clear button** — resets all fields for the next application in one click

---

## What Lands in Your Inbox

```
Subject: Application for [Job Title] at [Company] — [Your Name]
──────────────────────────────────────────────────────────────
[Short professional email body — 5-8 sentences]
──────────────────────────────────────────────────────────────
COVER LETTER
[Personalized cover letter — under 400 words]
──────────────────────────────────────────────────────────────
TAILORED CV
[ATS-optimized CV tailored to this specific role]
```

---

## Key Technical Decisions

**Sequential pipeline — not parallel**
Unlike a research agent where searches can run simultaneously, each stage here depends on the previous stage's output. Analysis feeds research, research feeds the CV tailor, and so on. Sequential execution is the correct pattern for dependent pipelines.

**gpt-4o for CV and cover letter, gpt-4o-mini everywhere else**
CV tailoring and cover letter writing are the most cognitively demanding tasks — they require holding multiple contexts simultaneously while producing high-quality, nuanced prose. The full `gpt-4o` is used for these two agents. All other agents use `gpt-4o-mini` for cost efficiency.

**Nested Pydantic schemas**
Complex agents like `AnalystAgent` use nested models (`JobRequirements` inside `JobAnalysis`, `CompanyInsights` inside `CompanyResearch`) so downstream agents can access exactly the fields they need cleanly.

**Rich structured input strings**
Each stage method in `JobApplicationManager` carefully assembles only the relevant fields from upstream outputs — not entire objects. This keeps token usage efficient and agent prompts focused.

**Environment variables for email addresses**
Both sender and recipient emails are loaded from `.env` — no hardcoded addresses in code, making the agent portable across environments.

**OpenAI Traces**
Every run generates a unique trace viewable on the OpenAI platform:
```
https://platform.openai.com/traces/trace?trace_id=<trace_id>
```

---

## Acknowledgements

Special thanks to **Ed Donner** — whose teaching made agentic AI architecture finally click. The modular, single-responsibility approach to agent design came directly from his influence.

---

## License

MIT License — feel free to use, modify, and build on this project.