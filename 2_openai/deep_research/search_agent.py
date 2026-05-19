from agents import Agent, WebSearchTool
from agents.model_settings import ModelSettings

search_agent_instructions = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a cohesive summary of the results. The summary must be 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succinctly, no need to have a complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so it's vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself"
)

search_agent = Agent(
    name="Search Agent",
    instructions=search_agent_instructions,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required")
)