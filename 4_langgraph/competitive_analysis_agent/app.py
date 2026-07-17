# app.py
# Entry point for the Competitor Analysis Agent
# Includes: scheduler, optional Gradio UI, and LangSmith tracing

# Imports
import asyncio
import json
from datetime import datetime
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from langsmith import traceable

from competitor_agent import CompetitorAgent, load_config

# Load Environment Variables
load_dotenv(override=True)

# Global Agent Instance
agent_instance: CompetitorAgent = None

# Setup
async def setup() -> CompetitorAgent:
    """Initialize the CompetitorAgent on app startup."""
    global agent_instance
    try:
        print("Initializing Competitor Agent...")
        agent_instance = CompetitorAgent()
        await agent_instance.setup()
        print(f"Competitor Agent ready — graph: {agent_instance.graph is not None}")
        return agent_instance
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        raise

# Scheduled Run
@traceable(name="Scheduled Weekly Run")
async def scheduled_run():
    """
    Called automatically by the scheduler every week.
    Runs the full competitor analysis and sends push notification.
    """
    global agent_instance

    print(f"\n{'='*50}")
    print(f"Scheduled run triggered — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    if agent_instance is None:
        print("Agent not initialized. Running setup first...")
        await setup()

    try:
        result = await agent_instance.run()
        print("Scheduled run completed successfully.")
        return result
    except Exception as e:
        print(f"Scheduled run failed: {e}")
        raise

# Manual Run (triggered from UI)
async def manual_run(agent, history):
    """
    Triggered when user clicks 'Run Now' in the Gradio UI.
    Runs the full competitor analysis immediately.
    """
    global agent_instance
    active_agent = agent or agent_instance

    # Check graph is built before running
    if active_agent is None or active_agent.graph is None:
        return history + [{
            "role": "assistant",
            "content": "Agent is still initializing. Please wait a few seconds and click Run Now again."
        }], agent

    history = history + [{
        "role": "assistant",
        "content": f"Starting competitor analysis — {datetime.now().strftime('%Y-%m-%d %H:%M')}..."
    }]

    try:
        result       = await active_agent.run()
        final_report = result.get("final_report", "No report generated.")
        history      = history + [{
            "role": "assistant",
            "content": f"Analysis complete!\n\n{final_report}"
        }]
    except Exception as e:
        history = history + [{
            "role": "assistant",
            "content": f"Run failed: {str(e)}"
        }]

    return history, active_agent


# Load Report (triggered from UI)
async def load_latest_report(agent, history):
    """Load and display the most recently saved report in the UI."""
    reports_dir = Path("sandbox/competitors/reports")

    if not reports_dir.exists():
        return history + [{
            "role": "assistant",
            "content": "No reports directory found. Run an analysis first."
        }], agent

    reports = sorted(reports_dir.glob("report_*.txt"))

    if not reports:
        return history + [{
            "role": "assistant",
            "content": "No reports found yet. Run an analysis first."
        }], agent

    latest = reports[-1]
    with open(latest, "r") as f:
        content = f.read()

    history = history + [{
        "role": "assistant",
        "content": f"Latest report ({latest.name}):\n\n{content}"
    }]

    return history, agent


# Load Config (triggered from UI)
async def show_config(agent, history):
    """Display the current competitors.json config in the UI."""
    try:
        config = load_config()
        competitors = config["competitors"]

        summary = "Current Configuration:\n\n"
        for c in competitors:
            summary += f"{c['name'].upper()}\n"
            summary += f"   URL: {c['url']}\n"
            for area, url in c["check_areas"].items():
                summary += f"   {area}: {url}\n"
            summary += "\n"

        summary += f"Check areas: {', '.join(config['check_areas'])}\n"
        summary += f"Schedule: {config['schedule']}\n"
        summary += f"Notification threshold: {config['notification_threshold']}"

        history = history + [{"role": "assistant", "content": summary}]

    except Exception as e:
        history = history + [{
            "role": "assistant",
            "content": f"Failed to load config: {str(e)}"
        }]

    return history, agent


# Reset
async def reset(agent):
    """Clean up and reinitialize the agent."""
    global agent_instance

    if agent:
        await agent.cleanup()

    agent_instance = CompetitorAgent()
    await agent_instance.setup()

    return [], agent_instance


# Cleanup on shutdown
async def free_resources(agent):
    """Called by Gradio when session ends — cleans up browser."""
    print("Cleaning up agent resources...")
    try:
        if agent:
            await agent.cleanup()
    except Exception as e:
        print(f"Cleanup error: {e}")


# Scheduler Setup
def setup_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()              

    scheduler.add_job(
        lambda: asyncio.run(scheduled_run()),       
        trigger="cron",
        day_of_week="mon",
        hour=8,
        minute=0,
        id="weekly_competitor_analysis",
        name="Weekly Competitor Analysis",
        replace_existing=True,
    )
    return scheduler


# Gradio UI
def build_ui() -> gr.Blocks:
    """Build and return the Gradio UI."""

    with gr.Blocks(title="Competitor Analysis Agent") as ui:

        gr.Markdown("""
# Competitor Analysis Agent
Monitors competitor websites weekly for pricing changes, new products, and blog posts.
Sends push notifications when changes are detected.
        """)

        agent = gr.State(delete_callback=free_resources)

        with gr.Row():
            chatbot = gr.Chatbot(
                label="Agent Activity",
                height=500,
                show_label=True,
            )

        with gr.Row():
            with gr.Column(scale=1):
                run_button = gr.Button(
                    "Run Now",
                    variant="primary",
                    size="lg"
                )
            with gr.Column(scale=1):
                report_button = gr.Button(
                    "Load Latest Report",
                    variant="secondary",
                    size="lg"
                )
            with gr.Column(scale=1):
                config_button = gr.Button(
                    "Show Config",
                    variant="secondary",
                    size="lg"
                )
            with gr.Column(scale=1):
                reset_button = gr.Button(
                    "Reset Agent",
                    variant="stop",
                    size="lg"
                )

        with gr.Accordion("Schedule Info", open=False):
            gr.Markdown("""
**Automatic Schedule:** Every Monday at 8:00 AM

To change the schedule, edit `setup_scheduler()` in `app.py`:
```python
scheduler.add_job(
    scheduled_run,
    trigger="cron",
    day_of_week="mon",   # mon, tue, wed, thu, fri, sat, sun
    hour=8,              # 0-23
    minute=0,
)
```

To add competitors, edit `competitors.json` — no code changes needed.
            """)

        with gr.Accordion("Sandbox Directory", open=False):
            gr.Markdown("""
All data is saved to:
```
sandbox/
└── competitors/
    ├── apple_latest.json       ← latest scraped data
    ├── apple_2026_07_04.json   ← timestamped backup
    ├── samsung_latest.json
    └── reports/
        └── report_2026_07_04.txt
```
            """)

        # Wire up events
        ui.load(setup, [], [agent])

        run_button.click(
            manual_run,
            inputs=[agent, chatbot],
            outputs=[chatbot, agent]
        )

        report_button.click(
            load_latest_report,
            inputs=[agent, chatbot],
            outputs=[chatbot, agent]
        )

        config_button.click(
            show_config,
            inputs=[agent, chatbot],
            outputs=[chatbot, agent]
        )

        reset_button.click(
            reset,
            inputs=[agent],
            outputs=[chatbot, agent]
        )

    return ui


# Main Entry Point
if __name__ == "__main__":

    scheduler = setup_scheduler()
    scheduler.start()

    next_run = scheduler.get_job("weekly_competitor_analysis").next_run_time
    print(f"\n Scheduler started. Next run: {next_run}\n")

    ui = build_ui()
    ui.launch(
        server_name="0.0.0.0",
        server_port=7860,
        inbrowser=True,
        theme=gr.themes.Default(primary_hue="blue")
    )