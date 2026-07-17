# The Competitor Analysis Agent - class, state, nodes and graph

# Imports
import os
import json
import uuid
from typing import Annotated, List, Dict, Any, Optional, TypedDict
from datetime import datetime
from pathlib import Path

import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from openai import RateLimitError

from dotenv import load_dotenv
from langsmith import traceable
from langchain_community.callbacks import get_openai_callback
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage, RemoveMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages, REMOVE_ALL_MESSAGES
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from competitor_tools import playwright_tools, other_tools

# Load Environment Variables
load_dotenv(override=True)

# Config Loader
CONFIG_PATH = Path("competitors.json")

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"competitors.json not found. "
            f"Please create it at {CONFIG_PATH.absolute()}"
        )
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


# Structured Output Schema
class EvaluatorOutput(BaseModel):
    feedback: str = Field(
        description="Feedback on the quality and completeness of the scraped data"
    )
    success_criteria_met: bool = Field(
        description="True if all required data was successfully scraped and compared"
    )
    user_input_needed: bool = Field(
        description="True if the agent is stuck or needs clarification to proceed"
    )

# State
class CompetitorState(TypedDict):
    messages:               Annotated[List[Any], add_messages]

    # Config
    competitors:            List[Dict[str, Any]]
    check_areas:            List[str]

    # Progress tracking
    current_competitor:     Optional[Dict[str, Any]]
    completed_competitors:  List[str]
    changes_found:          Dict[str, Any]

    # Evaluation
    success_criteria:       str
    feedback_on_work:       Optional[str]
    success_criteria_met:   bool
    user_input_needed:      bool
    retry_count:            int

    # Output
    final_report:           Optional[str]
    report_sent:            bool


# Agent Class
class CompetitorAgent:

    def __init__(self):
        self.worker_llm_with_tools      = None
        self.coordinator_llm            = None
        self.evaluator_llm_with_output  = None
        self.tools                      = None
        self.graph                      = None
        self.agent_id                   = str(uuid.uuid4())
        self.memory                     = None  # set up in setup(), needs async init
        self._memory_cm                 = None  # holds the context manager so we can close it in cleanup()
        self.browser                    = None
        self.playwright                 = None
        self.config                     = load_config()

    # Setup
    async def setup(self):
        """Initialize browser, tools, LLMs and graph."""

        # Persistent checkpointer
        self._memory_cm = AsyncSqliteSaver.from_conn_string("checkpoints.db")
        self.memory = await self._memory_cm.__aenter__()

        # Browser + tools
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += other_tools()

        # Worker LLM - acts, browses, scrapes, compares
        worker_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        self.worker_llm_no_more_tools = worker_llm.bind_tools(self.tools, tool_choice="none")

        self.coordinator_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

        # Evaluator LLM - judges completeness
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)

        await self.build_graph()
        print(f"CompetitorAgent ready — ID: {self.agent_id}")

    # --- helper: preserve prior messages, but refresh/insert the system message ---
    @staticmethod
    def _refresh_system_message(messages: List[Any], new_system_content: str, match_hint: str) -> List[Any]:
        """
        Preserve prior messages (including ToolMessages, so the LLM remembers what it
        already did), but swap in a fresh system message. `match_hint` is a substring
        used to identify "this node's" prior system message specifically, so we don't
        accidentally overwrite a system message belonging to a different node.
        """
        found = False
        updated = []
        for message in messages:
            if isinstance(message, SystemMessage) and match_hint in message.content and not found:
                updated.append(SystemMessage(content=new_system_content))
                found = True
            else:
                updated.append(message)

        if not found:
            updated = [SystemMessage(content=new_system_content)] + updated

        return updated

    # Node 1: Coordinator
    def coordinator(self, state: CompetitorState) -> Dict[str, Any]:
        """Plans the analysis run and selects the next competitor."""
        competitors = state["competitors"]
        completed   = state.get("completed_competitors", [])

        # Find next unprocessed competitor
        remaining = [c for c in competitors if c["name"] not in completed]

        if not remaining:
            # All done - move to reporting
            return {
                "messages":           [HumanMessage(content="All competitors processed. Generating report.")],
                "current_competitor": None,
            }

        current = remaining[0]

        system_message = f"""You are a competitive intelligence coordinator.
Today's date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Current competitor to analyze: {current["name"]}
Website: {current["url"]}

Areas to check:
{json.dumps(current["check_areas"], indent=2)}

What to look for:
- pricing: product names, prices, discounts, bundles
- products: new launches, discontinued items, spec changes
- blog: latest post titles, dates, topics covered

Provide a clear analysis plan for this competitor."""

        # Fresh messages
        messages = [SystemMessage(content=system_message)]
        response = self.coordinator_llm.invoke(messages)

        return {
            "messages":           [response],
            "current_competitor": current,
            "success_criteria": (
                f"Successfully scraped pricing, products, and blog data "
                f"from {current['name']}'s website and compared with previous data."
            ),
            "feedback_on_work":     None,
            "success_criteria_met": False,
            "user_input_needed":    False,
            "retry_count":          0,
        }

    # Node 2: Scraper
    def scraper(self, state: CompetitorState) -> Dict[str, Any]:
        """Visits competitor website and extracts pricing, products, and blog data."""
        current     = state["current_competitor"]
        check_areas = current.get("check_areas", {})
        feedback    = state.get("feedback_on_work")

        print(f"[scraper] competitor={current['name']} incoming_message_count={len(state['messages'])}")

        system_message = f"""You are a web scraping agent specialized in competitive intelligence.
Today's date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Your current task: Scrape data from {current["name"]}'s website.

URLs to visit for each area:
{json.dumps(check_areas, indent=2)}

For PRICING pages, extract:
- Product names, current prices, discounts

For PRODUCTS pages, extract:
- Recently launched products (last 30 days)
- Discontinued products, major spec updates

For BLOG pages, extract:
- Latest 5 post titles, publication dates, main topics

Steps:
1. Load previous data: use load_competitor_data tool with "{current["name"]}"
2. Visit each URL and extract relevant data
3. Save current data: use save_competitor_data tool with "{current["name"]}|{{json_data}}"
4. Return a summary of what you found

Structure all extracted data as valid JSON before saving."""

        if feedback:
            system_message += f"\n\nPrevious attempt feedback:\n{feedback}\nPlease address these issues."

        tool_call_rounds = sum(
            1 for m in state["messages"]
            if hasattr(m, "tool_calls") and m.tool_calls
        )

        if tool_call_rounds >= 8:
            # Force a final plain-text answer, never allow another tool call once
            # capped. This guarantees the router can never see a pending tool call
            # it's tempted to skip past.
            print(f"[scraper] hit {tool_call_rounds} tool-call rounds — forcing a final answer, no more tools")
            stop_instruction = (
                "\n\nYou have used your tool budget for this attempt. Do NOT call any "
                "more tools. Respond now in plain text summarizing what you found so far "
                "(or what you were unable to find), so this can move forward."
            )
            updated_messages = self._refresh_system_message(
                state["messages"], system_message + stop_instruction, match_hint="web scraping agent"
            )
            response = self.worker_llm_no_more_tools.invoke(updated_messages)
        else:
            updated_messages = self._refresh_system_message(
                state["messages"], system_message, match_hint="web scraping agent"
            )
            response = self.worker_llm_with_tools.invoke(updated_messages)

        if hasattr(response, "tool_calls") and response.tool_calls:
            call_names = [tc["name"] for tc in response.tool_calls]
            print(f"[scraper] LLM requested tool calls: {call_names}")
        else:
            print(f"[scraper] LLM finished — no more tool calls, routing to comparator")

        return {"messages": [response]}

    # Router: After Scraper
    def scraper_router(self, state: CompetitorState) -> str:
        """Route to tools if scraper called one, otherwise to comparator."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "comparator"

    # Node 3: Comparator
    def comparator(self, state: CompetitorState) -> Dict[str, Any]:
        """Compares this week's scraped data with last week's saved data."""
        current = state["current_competitor"]

        print(f"[comparator] competitor={current['name']} incoming_message_count={len(state['messages'])}")

        system_message = f"""You are a data analyst specialized in competitive intelligence.
Today's date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Your task: Compare this week's data for {current["name"]} with last week's data.

Steps:
1. Load current data using load_competitor_data("{current["name"]}")
2. Use python_repl to compare old vs new data and find:
   - Price changes (which products, by how much)
   - New products (in current but not previous)
   - Removed products (in previous but not current)
   - New blog posts (titles not seen last week)
3. Structure your findings as a clear summary

Python comparison example:
```python
import json
old_data = {{...}}  # last week
new_data = {{...}}  # this week

price_changes = []
for product in new_data.get("pricing", []):
    old_price = next((p["price"] for p in old_data.get("pricing", [])
                     if p["name"] == product["name"]), None)
    if old_price and old_price != product["price"]:
        price_changes.append({{
            "product": product["name"],
            "old_price": old_price,
            "new_price": product["price"],
            "change": product["price"] - old_price
        }})
print(json.dumps(price_changes))
```

Once you have your summary, respond with plain text only (no further tool calls)."""

        tool_call_rounds = sum(
            1 for m in state["messages"]
            if hasattr(m, "tool_calls") and m.tool_calls
        )

        if tool_call_rounds >= 8:
            print(f"[comparator] hit {tool_call_rounds} tool-call rounds — forcing a final answer, no more tools")
            stop_instruction = (
                "\n\nYou have used your tool budget. Do NOT call any more tools. "
                "Respond now in plain text with your best summary of the comparison "
                "based on whatever you've already found."
            )
            updated_messages = self._refresh_system_message(
                state["messages"], system_message + stop_instruction, match_hint="data analyst specialized"
            )
            response = self.worker_llm_no_more_tools.invoke(updated_messages)
        else:
            updated_messages = self._refresh_system_message(
                state["messages"], system_message, match_hint="data analyst specialized"
            )
            response = self.worker_llm_with_tools.invoke(updated_messages)

        if hasattr(response, "tool_calls") and response.tool_calls:
            call_names = [tc["name"] for tc in response.tool_calls]
            print(f"[comparator] LLM requested tool calls: {call_names}")
        else:
            print(f"[comparator] LLM finished — no more tool calls, routing to evaluator")

        changes = state.get("changes_found", {})
        if not (hasattr(response, "tool_calls") and response.tool_calls):
            changes[current["name"]] = response.content

        return {
            "messages":      [response],
            "changes_found": changes,
        }
    
    # Router: After Comparator
    def comparator_router(self, state: CompetitorState) -> str:
        """Route to tools if comparator called one, otherwise to evaluator."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "evaluator"


    # Node 4: Evaluator
    def evaluator(self, state: CompetitorState) -> Dict[str, Any]:
        """Judges whether scraping and comparison was complete and accurate."""
        current       = state["current_competitor"]
        last_response = state["messages"][-1].content

        system_message = """You are an evaluator checking the quality of competitive intelligence data.
Assess whether the scraping and comparison was thorough and complete."""

        user_message = f"""Evaluate this competitive analysis for {current["name"]}.

Success criteria: {state["success_criteria"]}

Last response from the agent:
{last_response}

Check:
1. Was pricing data successfully scraped? (product names + prices)
2. Were new products identified?
3. Were blog posts extracted? (at least titles + dates)
4. Was comparison with previous data completed?
5. Were changes clearly identified?

If the agent says it saved data or found no changes, give it the benefit of the doubt.
Only reject if data is clearly missing or comparison was skipped entirely."""

        if state.get("feedback_on_work"):
            user_message += (
                f"\n\nPrevious feedback given: {state['feedback_on_work']}\n"
                "If the same issues persist, set user_input_needed=True."
            )

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)

        current_retry_count = state.get("retry_count", 0)
        new_retry_count = (
            current_retry_count if eval_result.success_criteria_met
            else current_retry_count + 1
        )

        return {
            "messages": [AIMessage(content=f"Evaluator: {eval_result.feedback}")],
            "feedback_on_work":     eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed":    eval_result.user_input_needed,
            "retry_count":          new_retry_count,
        }

    # Router: After Evaluator
    def route_based_on_evaluation(self, state: CompetitorState) -> str:
        """Routes to scraper (retry), next_competitor, or reporter."""
        retry_count = state.get("retry_count", 0)
        competitor_name = state.get("current_competitor", {}).get("name", "unknown")

        print(
            f"[evaluator routing] competitor={competitor_name} "
            f"retry_count={retry_count} "
            f"success_criteria_met={state['success_criteria_met']} "
            f"user_input_needed={state['user_input_needed']} "
            f"feedback={state.get('feedback_on_work')!r}"
        )

        if state["user_input_needed"]:
            print(f"[evaluator routing] -> reporter (user_input_needed=True, skipping remaining competitors)")
            return "reporter"

        if not state["success_criteria_met"]:
            if retry_count >= 3:
                print(f"Max retries reached for {competitor_name}")
                return "next_competitor"
            return "scraper"

        return "next_competitor"

    # Node 5: Next Competitor
    def next_competitor(self, state: CompetitorState) -> Dict[str, Any]:
        """
        Marks current competitor as complete and prepares for the next one.
        Also clears the message history — each competitor gets a clean working
        memory, so tool calls/results from a finished competitor can never leak
        into (or poison) the next competitor's LLM calls.
        """
        current   = state["current_competitor"]
        completed = state.get("completed_competitors", [])

        if current:
            completed = completed + [current["name"]]
            print(f"{current['name']} complete. Pausing before next competitor...")

        return {
            "completed_competitors": completed,
            "current_competitor":    None,
            "retry_count":           0,
            "success_criteria_met":  False,
            "feedback_on_work":      None,
            "messages":              [RemoveMessage(id=REMOVE_ALL_MESSAGES)],
        }

    # Router: After Next Competitor
    def next_competitor_router(self, state: CompetitorState) -> str:
        """Go back to coordinator if more competitors remain, else generate report."""
        competitors = state["competitors"]
        completed   = state.get("completed_competitors", [])
        remaining   = [c for c in competitors if c["name"] not in completed]

        if remaining:
            return "coordinator"
        return "reporter"

    # Node 6: Reporter
    def reporter(self, state: CompetitorState) -> Dict[str, Any]:
        """Builds the final weekly report, saves it, and sends push notification."""
        changes     = state.get("changes_found", {})
        competitors = state["competitors"]
        week_number = datetime.now().isocalendar()[1]

        # Short-circuit: if the report has already been sent this run, don't do it again.
        if state.get("report_sent"):
            return {"messages": [AIMessage(content="Report already sent — nothing more to do.")]}

        # Hard stop based on actual message history, not the LLM's judgment: if both
        # required tools have already executed successfully once, we're done, full
        # stop, regardless of what the LLM might otherwise be inclined to call again.
        existing_tool_names = {
            m.name for m in state["messages"]
            if isinstance(m, ToolMessage) and getattr(m, "name", None)
        }
        if {"save_report", "send_push_notification"}.issubset(existing_tool_names):
            print("Reporter: save_report and send_push_notification both already ran — stopping.")
            return {
                "messages":     [AIMessage(content="Report already saved and notification already sent.")],
                "final_report": state.get("final_report"),
                "report_sent":  True,
            }

        system_message = f"""You are a competitive intelligence reporter.
Today's date: {datetime.now().strftime("%Y-%m-%d")}
Week number: {week_number}

Generate a clear, actionable weekly competitor analysis report.

Format:

WEEKLY COMPETITOR REPORT
Week {week_number} — {datetime.now().strftime("%B %d, %Y")}

[COMPETITOR NAME]
Pricing Changes:
  • [list changes or "No changes detected"]
New Products:
  • [list new products or "No new products"]
Blog/News:
  • [list new posts or "No new posts"]
Key Insight:
  • [one sentence on most important finding]

SUMMARY
[2-3 sentences on most important competitive developments this week]

After generating:
1. Save using save_report tool
2. Send push notification: "Week {week_number} Competitor Report: [2-3 key highlights]"

Once both tools have been called, respond with plain text only (no further tool calls)."""

        existing_messages = state["messages"]
        has_reporter_system = any(
            isinstance(m, SystemMessage) and "competitive intelligence reporter" in m.content
            for m in existing_messages
        )

        if not has_reporter_system:
            user_message = f"""Generate the weekly report based on these findings:

{json.dumps(changes, indent=2) if changes else "No changes data available."}

Competitors analyzed: {[c["name"] for c in competitors]}
Completed: {state.get("completed_competitors", [])}

Save the report and send the push notification."""

            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message),
            ]
        else:
            messages = existing_messages

        response = self.worker_llm_with_tools.invoke(messages)

        has_pending_tool_call = hasattr(response, "tool_calls") and response.tool_calls

        return {
            "messages":     [response],
            "final_report": response.content if not has_pending_tool_call else state.get("final_report"),
            # Only flip report_sent once the LLM is done calling tools —
            # this combines with the short-circuit above to guarantee exactly one send.
            "report_sent":  not has_pending_tool_call,
        }

    # Router: After Reporter
    def reporter_router(self, state: CompetitorState) -> str:
        """Route to tools if reporter called one, otherwise END."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    # Build Graph
    async def build_graph(self):
        """Wire all nodes and edges into compiled LangGraph."""
        graph_builder = StateGraph(CompetitorState)

        # Add nodes
        graph_builder.add_node("coordinator",      self.coordinator)
        graph_builder.add_node("scraper",          self.scraper)
        graph_builder.add_node("scraper_tools",    ToolNode(tools=self.tools, handle_tool_errors=True))
        graph_builder.add_node("comparator",       self.comparator)
        graph_builder.add_node("comparator_tools", ToolNode(tools=self.tools, handle_tool_errors=True))
        graph_builder.add_node("evaluator",        self.evaluator)
        graph_builder.add_node("next_competitor",  self.next_competitor)
        graph_builder.add_node("reporter",         self.reporter)
        graph_builder.add_node("reporter_tools",   ToolNode(tools=self.tools, handle_tool_errors=True))

        # Edges
        graph_builder.add_edge(START, "coordinator")
        graph_builder.add_edge("coordinator", "scraper")
        graph_builder.add_edge("scraper_tools", "scraper")
        graph_builder.add_edge("comparator_tools", "comparator")
        graph_builder.add_edge("reporter_tools", "reporter")

        graph_builder.add_conditional_edges(
            "scraper",
            self.scraper_router,
            {"tools": "scraper_tools", "comparator": "comparator"}
        )

        graph_builder.add_conditional_edges(
            "comparator",
            self.comparator_router,
            {"tools": "comparator_tools", "evaluator": "evaluator"}
        )

        graph_builder.add_conditional_edges(
            "evaluator",
            self.route_based_on_evaluation,
            {
                "scraper":         "scraper",
                "next_competitor": "next_competitor",
                "reporter":        "reporter",
            }
        )

        graph_builder.add_conditional_edges(
            "next_competitor",
            self.next_competitor_router,
            {
                "coordinator": "coordinator",
                "reporter":    "reporter",
            }
        )

        graph_builder.add_conditional_edges(
            "reporter",
            self.reporter_router,
            {"tools": "reporter_tools", END: END}
        )

        self.graph = graph_builder.compile(checkpointer=self.memory)
        print("Graph compiled successfully.")

    # Run
    @retry(
        retry=retry_if_exception_type(RateLimitError),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5)
    )
    async def _invoke_with_retry(self, state, config):
        """Invoke the graph, retrying with backoff if OpenAI rate-limits us."""
        return await self.graph.ainvoke(state, config=config)

    @traceable(name="Weekly Competitor Analysis Run")
    async def run(self):
        """Main entry point for a weekly analysis run."""
        if self.graph is None:
            raise RuntimeError(
                "Agent not ready. Call await agent.setup() before running."
            )

        config      = load_config()
        competitors = config["competitors"]
        check_areas = config["check_areas"]

        print(f"\n{'='*50}")
        print(f"Starting competitor analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"Competitors: {[c['name'] for c in competitors]}")
        print(f"{'='*50}\n")

        initial_state: CompetitorState = {
            "messages":              [HumanMessage(content="Start weekly competitor analysis.")],
            "competitors":           competitors,
            "check_areas":           check_areas,
            "current_competitor":    None,
            "completed_competitors": [],
            "changes_found":         {},
            "success_criteria":      "All competitors scraped and compared successfully.",
            "feedback_on_work":      None,
            "success_criteria_met":  False,
            "user_input_needed":     False,
            "retry_count":           0,
            "final_report":          None,
            "report_sent":           False,
        }

        # Scope the thread to this ISO week, so a crashed run can be retried and
        # resume from its last checkpoint instead of starting over from scratch.
        week_number  = datetime.now().isocalendar()[1]
        year         = datetime.now().year
        thread_id    = f"competitor-analysis-{year}-w{week_number}"

        graph_config = {
            "configurable": {"thread_id": thread_id, "recursion_limit": 60},
            "metadata": {
                "run_type":          "weekly_analysis",
                "competitors_count": len(competitors),
                "run_date":          datetime.now().strftime("%Y-%m-%d"),
                "week_number":       week_number,
            },
            "tags": ["competitor-agent", "weekly", "production"]
        }

        try:
            async with asyncio.timeout(600):
                with get_openai_callback() as cb:
                    # Check whether this week's thread already has in-progress state
                    # (e.g. from a run that crashed mid-tool-call). If so, resume it
                    # in place by passing None as input — passing a fresh initial_state
                    # here would re-enter at START and append a new HumanMessage on top
                    # of any unresolved tool calls left behind, which corrupts the
                    # message history. If the thread is new or already finished, run
                    # normally with the fresh initial_state.
                    existing_state = await self.graph.aget_state(graph_config)

                    if existing_state.values and existing_state.next:
                        existing_msg_count = len(existing_state.values.get("messages", []))
                        if existing_msg_count > 50:
                            # This thread's checkpoint is bloated from an earlier runaway loop —
                            # don't resume it, reset it and start clean instead.
                            print(
                                f"Found an incomplete run with {existing_msg_count} accumulated "
                                f"messages — treating as corrupted, resetting instead of resuming."
                            )
                            graph_input = {
                                **initial_state,
                                "messages": [
                                    RemoveMessage(id=REMOVE_ALL_MESSAGES),
                                    HumanMessage(content="Start weekly competitor analysis."),
                                ],
                            }
                        else:
                            print("Found an incomplete run for this week — resuming in place...")
                            graph_input = None
                    else:
                        graph_input = initial_state

                    result = await self._invoke_with_retry(graph_input, graph_config)

                    print(f"\n{'='*50}")
                    print(f"Run complete!")
                    print(f"Total tokens:      {cb.total_tokens:,}")
                    print(f"Prompt tokens:     {cb.prompt_tokens:,}")
                    print(f"Completion tokens: {cb.completion_tokens:,}")
                    print(f"Total cost:        ${cb.total_cost:.4f}")
                    print(f"{'='*50}\n")

        except asyncio.TimeoutError:
            print("Run timed out after 10 minutes")
            return {
                "final_report": (
                    "Run timed out after 10 minutes. "
                    "Try reducing the number of competitors, or re-run — "
                    "progress on completed competitors is checkpointed."
                ),
                "report_sent": False
            }
        except Exception as e:
            print(f"Run failed with an unexpected error: {e}")
            return {
                "final_report": (
                    f"Run failed: {e}\n\n"
                    "Progress on already-completed competitors is checkpointed — "
                    "re-running should resume from where this left off."
                ),
                "report_sent": False
            }

        return result

    # Cleanup
    async def cleanup(self):
        """Cleanly shut down the Playwright browser, engine, and checkpoint DB connection."""
        if self.browser:
            try:
                await self.browser.close()
                print("Browser closed.")
            except Exception as e:
                print(f"Error closing browser: {e}")
        if self.playwright:
            try:
                await self.playwright.stop()
                print("Playwright stopped.")
            except Exception as e:
                print(f"Error stopping playwright: {e}")
        if self._memory_cm:
            try:
                await self._memory_cm.__aexit__(None, None, None)
                print("Checkpoint DB connection closed.")
            except Exception as e:
                print(f"Error closing checkpoint DB: {e}")