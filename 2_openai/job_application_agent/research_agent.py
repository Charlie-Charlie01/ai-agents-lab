from pydantic import BaseModel, Field
from agents import Agent, WebSearchTool
from agents.model_settings import ModelSettings


RESEARCH_INSTRUCTIONS = (
    "You are an expert company and industry researcher. You will be given a company name, job title, "
    "and a structured job analysis. Your job is to search the web and gather rich, relevant information "
    "that will help personalize a cover letter and tailor a CV.\n"
    "You should search for:\n"
    "1. The company's mission, vision, and core values\n"
    "2. Recent company news, product launches, or milestones (last 6-12 months)\n"
    "3. The company's culture, work environment, and what they look for in employees\n"
    "4. The industry landscape and key trends relevant to this role\n"
    "5. Any notable achievements, awards, or recognitions the company has received\n"
    "Search at least 4-5 times with different queries to gather comprehensive information. "
    "Be specific and factual. Avoid generic statements. "
    "Everything you find will be used to write a highly personalized cover letter, "
    "so prioritize insights that show genuine knowledge of the company."
)


class CompanyInsights(BaseModel):
    mission_and_values: str = Field(description="The company's mission, vision, and core values")
    recent_news: list[str] = Field(description="Recent news, product launches, or milestones from the last 6-12 months")
    culture_and_environment: str = Field(description="Insights about the company's culture, work environment, and team")
    notable_achievements: list[str] = Field(description="Awards, recognitions, or notable achievements of the company")


class IndustryInsights(BaseModel):
    key_trends: list[str] = Field(description="Current trends in the industry relevant to this role")
    challenges: list[str] = Field(description="Key challenges or problems the industry is currently facing")
    opportunities: list[str] = Field(description="Emerging opportunities in the industry relevant to this role")


class CompanyResearch(BaseModel):
    company_name: str = Field(description="The name of the company researched")
    job_title: str = Field(description="The job title being applied for")
    company_insights: CompanyInsights = Field(description="Detailed insights about the company")
    industry_insights: IndustryInsights = Field(description="Insights about the industry and market landscape")
    personalization_hooks: list[str] = Field(
        description="3-5 specific, compelling talking points the candidate can reference in their cover letter "
                    "to demonstrate genuine interest and knowledge of the company"
    )
    research_summary: str = Field(
        description="A 2-3 sentence summary of the most important findings that should influence "
                    "the tone and content of the cover letter"
    )


research_agent = Agent(
    name="Research Agent",
    instructions=RESEARCH_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="medium")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
    output_type=CompanyResearch,
)