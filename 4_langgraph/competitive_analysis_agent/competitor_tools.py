# Tools for the Competitor Analysis Agent
# Let's import necessary liraries
import os
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from langchain_core.tools import Tool
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_experimental.tools import PythonREPLTool

# Load the environment variables from the .env file
load_dotenv(override=True)

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"

serper = GoogleSerperAPIWrapper()

# Sandbox directory setup
SANDBOX_DIR = Path("sandbox/competitors")
REPORTS_DIR = SANDBOX_DIR / "reports"

def ensure_directories():
    """Create sandbox directories if they don't exist."""
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

ensure_directories()


# Push notification tool
def push(text: str) -> str:
    """Send a push notification using Pushover."""
    if not pushover_token or not pushover_user:
        return "Pushover not configured - skipping notification."
    
    try:
        response = requests.post(
            pushover_url,
            data={
                "token": pushover_token,
                "user": pushover_user,
                "message": text
            }
        )
        if response.status_code == 200:
            return "Successfully sent push notification: " + text
        else:
            return f"Failed to send notification: {response.status_code}"
        
    except Exception as e:
        return f"Error sending notification: {str(e)}"

# Playwright browser tool
async def playwright_tools():
    """
    Launch a headless chromium browser and return:
    - list of Langchain browser tools
    - the browser instance ( for lifecycle management )
    - the playwright instance ( for lifecycle management )
    """

    try:
        playwright = await async_playwright().start()
        browser    = await playwright.chromium.launch(headless=True)

        # Set default timeout to 15 seconds per action/navigation
        context = await browser.new_context()
        context.set_default_timeout(15000)
        context.set_default_navigation_timeout(15000)

        toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
        return toolkit.get_tools(), browser, playwright
    except Exception as e:
        print(f"Failed to launch browser: {e}")
        raise

# File management tool
def get_file_tools():
    """
    Return file management tools scoped to the sandbox/competitors directory.
    The agent can read, write, list, and delete files - but only inside the folder.
    """

    ensure_directories()
    toolkit = FileManagementToolkit(root_dir=str(SANDBOX_DIR))
    return toolkit.get_tools()

# JSON data tool
def save_competitor_data(competitor_name: str, data: str) -> str:
    """
    Save scraped competitor data as a JSON file.
    Filename format: {competitor_name}_latest.json
    Also saves a timestamped backup copy.
    """

    try:
        # Validate it's real JSON
        parsed = json.loads(data)

        # Save latest (always overwritten)
        latest_path = SANDBOX_DIR / f"{competitor_name}_latest.json"
        with open(latest_path, "w") as f:
            json.dump(parsed, f, indent=2)

        # Save timestamped backup
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        backup_path = SANDBOX_DIR / f"{competitor_name}_{timestamp}.json"
        with open(backup_path, "w") as f:
            json.dump(parsed, f, indent=2)

        return f"Saved competitor data for {competitor_name} to {latest_path}"
    
    except json.JSONDecodeError:
        return f"Error: data is not valid JSON. Please provide a valid JSON string."
    except Exception as e:
        return f"Error saving competitor data: {str(e)}"
    
def load_competitor_data(competitor_name: str) -> str:
    """
    Load the most recent saved data for a competitor.
    Returns the JSON string, or a message if no prior data exists.
    
    Args:
        competitor_name: e.g. 'apple', 'samsung'
    """

    try: 
        latest_path = SANDBOX_DIR / f"{competitor_name}_latest.json"
        if not latest_path.exists():
            return f"No previous data found for {competitor_name}. This is the first run."
        with open(latest_path, "r") as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error loading competitor data: {str(e)}"

def save_report(report: str) -> str:
    """
    Save the weekly competitor analysis report to the reports directory.
    Filename format: report_{YYYY_MM_DD}.txt
    
    Args:
        report: the full text of the weekly report
    """

    try:
        timestamp = datetime.now().strftime("%Y_%m_%d")
        report_path = REPORTS_DIR / f"report_{timestamp}.txt"
        with open(report_path, "w") as f:
            f.write(report)
        return f"Saved weekly report to {report_path}"
    except Exception as e:
        return f"Error saving report: {str(e)}"
    
def load_latest_report() -> str:
    """
    Load the most recently saved weekly report.
    Useful for comparing trends week over week.
    """
    try:
        reports = sorted(REPORTS_DIR.glob("report_*.txt"))
        if not reports:
            return "No previous reports found."
        latest = reports[-1]
        with open(latest, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error loading report: {str(e)}"

# All other tools
def other_tools():
    """
    Assemble and return all non-PlayWright tools:
    - Push notification
    - Google Search
    - Python REPL
    - JSON save/load tools
    - Report save/load tools
    - File management tools
    """

    push_tool = Tool(
        name="send_push_notification",
        func=push,
        description=(
            "Use this tool to send a notification to the user's phone. "
            "Use it when a weekly report is ready or when an important competitor "
            "change is detected that the user should know about immediately. "
        )
    )

    search_tool = Tool(
        name="search",
        func=serper.run,
        description=(
            "Use this tool to search the web for information about a competitor"
            "before browsing their website. Useful for finding the right URLs," \
            "recent news, or product announcements."
        )
    )

    python_repl = PythonREPLTool()

    save_data_tool = Tool(
        name="save_competitor_data",
        func=lambda x: save_competitor_data(*x.split("|", 1)),
        description=(
            "Use this tool to save scraped competitor data as JSON."
            "Input format: 'competitor_name|json_string'"
            "Example: 'apple|{\"pricing\": {\"iphone\": 999}}'"
        )
    )

    load_data_tool = Tool(
        name="load_competitor_data",
        func=load_competitor_data,
        description=(
            "Use this tool to load previously saved data for a competitor."
            "Input: competitor name e.g. 'apple'."
            "Returns the last week's scraped data for comparison."
        )
    )

    save_report_tool = Tool(
        name="save_report",
        func=save_report,
        description=(
            "Use this tool to save the final weekly competitor analysis report."
            "Input: the full report text as a string."
        )
    )

    load_report_tool = Tool(
        name="load_latest_report",
        func=lambda _: load_latest_report(),
        description=(
            "Use this tool to load the most recent weekly report."
            "Useful for understanding what was reported last week."
        )
    )

    file_tools = get_file_tools()

    return [push_tool, search_tool, python_repl, save_data_tool, load_data_tool,
              save_report_tool, load_report_tool] + file_tools