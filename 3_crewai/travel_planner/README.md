# Travel Planner — Autonomous AI Travel Planning Agent

An autonomous multi-agent travel planning system built with CrewAI. Give it a destination, dates, budget, and interests — a crew of AI agents researches flights, hotels, and activities, then compiles everything into a complete travel plan and delivers it to your inbox.

---

## How It Works

The system runs four specialist agents coordinated by a manager agent using CrewAI's hierarchical process:

```
User provides destination, dates, budget, interests
            ↓
      Manager kicks off
            ↓
Flight Researcher   →  finds best flight options       →  FlightList (Pydantic)
Hotel Researcher    →  finds best hotel options        →  HotelList (Pydantic)
Itinerary Planner   →  builds day-by-day activities   →  ItineraryPlan (Pydantic)
Travel Coordinator  →  compiles full plan + sends email →  travel_plan.md
```

No human input is needed after the initial kickoff. The crew handles everything autonomously.

---

## Agents

| Agent | Role | Tools |
|---|---|---|
| `flight_researcher` | Finds flight options from departure city to destination | SerperDevTool |
| `hotel_researcher` | Researches hotels matching budget and interests | SerperDevTool |
| `itinerary_planner` | Creates day-by-day activity plan | SerperDevTool |
| `travel_coordinator` | Compiles full plan and delivers via email | EmailTool |
| `manager` | Delegates tasks and oversees the crew | — |

---

## Tasks

| Task | Output |
|---|---|
| `find_flights` | Structured list of flight options |
| `find_hotels` | Structured list of hotel options |
| `plan_itinerary` | Full day-by-day itinerary |
| `compile_travel_plan` | Complete markdown travel plan + email delivery |

---

## Project Structure

```
travel_planner/
├── src/travel_planner/
│   ├── config/
│   │   ├── agents.yaml          # Agent roles, goals, backstories
│   │   └── tasks.yaml           # Task descriptions and expected outputs
│   ├── tools/
│   │   ├── __init__.py
│   │   └── email_tool.py        # Custom tool to send plan via email
│   ├── __init__.py
│   ├── crew.py                  # Agents, tasks, crew definition
│   └── main.py                  # Entry point and input configuration
├── output/
│   ├── flights.json
│   ├── hotels.json
│   ├── itinerary.json
│   └── travel_plan.md           # Final compiled travel plan
├── .env                         # API keys (not committed)
├── pyproject.toml
└── README.md
```

---

## Setup

### 1. Prerequisites

- Python 3.10–3.13
- CrewAI installed (`pip install crewai crewai-tools`)
- A Gmail account with an App Password generated

### 2. Clone and navigate

```bash
git clone https://github.com/your-username/travel-planner.git
cd travel_planner
```

### 3. Install dependencies

```bash
crewai install
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
# LLM
OPENAI_API_KEY=sk-...

# Web search
SERPER_API_KEY=your-serper-key

# Memory embeddings
GOOGLE_API_KEY=your-gemini-api-key

# Email delivery
EMAIL_ADDRESS=yourname@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
RECIPIENT_EMAIL=traveler@gmail.com
```

#### Getting your API keys

| Key | Where to get it |
|---|---|
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) |
| `SERPER_API_KEY` | [serper.dev](https://serper.dev) |
| `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com) |
| `EMAIL_PASSWORD` | Google Account → Security → 2-Step Verification → App Passwords |

### 5. Create the output folder

```bash
mkdir -p output
```

---

## Running the Project

### Configure your trip

Open `src/travel_planner/main.py` and update the inputs:

```python
inputs = {
    'destination': 'Paris, France',
    'departure_city': 'Lagos, Nigeria',
    'check_in': '2025-08-01',
    'check_out': '2025-08-07',
    'budget': 'mid-range',
    'travelers': '2 adults',
    'interests': 'art, food, history, local culture',
}
```

### Run the crew

```bash
crewai run
```

### Output

The final travel plan is saved to `output/travel_plan.md` and emailed to the address set in `RECIPIENT_EMAIL`.

---

## Custom Tool — EmailTool

The `EmailTool` is a custom CrewAI tool built using `BaseTool`. It is called autonomously by the `travel_coordinator` agent when the plan is ready.

```python
class EmailTool(BaseTool):
    name: str = "Send Travel Plan Email"
    description: str = "Sends the completed travel plan to the traveler via email."
```

It uses Gmail's SMTP server to deliver the plan. To use a different email provider, update the SMTP settings in `tools/email_tool.py`.

---

## Key Concepts Demonstrated

| Concept | Implementation |
|---|---|
| Multi-agent collaboration | 4 specialist agents + 1 manager |
| Hierarchical process | Manager delegates to agents dynamically |
| Structured outputs | Pydantic models enforce data shape between tasks |
| Context chaining | Each task feeds into the next via `context:` in tasks.yaml |
| Custom tool | `EmailTool` built from scratch using `BaseTool` |
| Memory | Unified memory with Google embeddings for cross-session recall |
| Real-world delivery | Email sent via Gmail SMTP on task completion |

---

## Dependencies

```toml
[project]
dependencies = [
    "crewai[tools]>=1.0.0",
    "pydantic>=2.0.0",
]
```

---

## redits

Project built as part of the AI Agents curriculum by **Ed Donner**. The structured approach to multi-agent systems, tool building, and hierarchical orchestration taught in the course made this project possible.

---

## License

MIT License — free to use, fork, and build on.