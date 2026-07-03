# Import the necessary libraries
from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
from langchain_core.tools import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper

# Load environment variables
load_dotenv(override=True)

# Set up Pushover API credentials, for push notification system
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
    
# Initialize the Google Serper API Wrapper
serper = GoogleSerperAPIWrapper()

# This is an async factory function that spins up a fresh Playwright browser instance and returns the tools, browser, and playwright objects
async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright

# This function sends a notification to the user via Pushover
def push(text: str) -> str:
    """Send a notification to the user via Pushover."""
    requests.post(pushover_url, data={
        "token": pushover_token,
        "user": pushover_user,
        "message": text})
    return "Successfully sent notification to user: " + str

# Returns a set of file management tools that let the agent read, write, and manage files, but restricted to a specific folder
def get_file_tools():
    """Get the file management tools."""
    os.makedirs("sandbox", exist_ok=True)
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()

# This function returns a set of tools that can be used by the agent, including the push notification tool, file management tools, and a web search tool
# It assembles all the non-Playwright tools into one collection
def other_tools():
    push_tool = Tool(
        name="send_push_notification",
        func=push,
        description="Use this tool when you want to send a push notification"
    )
    file_tools = get_file_tools()

    tool_search = Tool(
        name="search",
        func=serper.run,
        description="Use this tool when you want to search the web for information"
    )

    # wikipedia = WikipediaAPIWrapper()
    # wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)
    
    python_repl = PythonREPLTool()
    
    return [push_tool, tool_search, python_repl] + file_tools



