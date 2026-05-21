from pydantic import BaseModel, Field
from agents import Agent


ANALYST_INSTRUCTIONS = (
    "You are an expert job application analyst. You will be given a job description and a candidate's CV. "
    "Your job is to carefully analyze both and produce a structured analysis that will be used by other "
    "agents to tailor the CV and write a cover letter.\n"
    "You should:\n"
    "1. Extract the key skills, qualifications, and requirements from the job description\n"
    "2. Identify the candidate's strongest matching skills and experiences from their CV\n"
    "3. Identify gaps between the job requirements and the candidate's CV\n"
    "4. Extract important keywords from the job description for ATS optimization\n"
    "5. Assess the seniority level and tone of the role\n"
    "Be thorough and precise. Your analysis directly determines the quality of the tailored CV and cover letter."
)


class JobRequirements(BaseModel):
    required_skills: list[str] = Field(description="Hard skills explicitly required in the job description")
    preferred_skills: list[str] = Field(description="Nice-to-have or preferred skills mentioned in the job description")
    qualifications: list[str] = Field(description="Required qualifications, degrees, or certifications")
    responsibilities: list[str] = Field(description="Key responsibilities of the role")
    seniority_level: str = Field(description="The seniority level of the role e.g. junior, mid, senior, lead")
    company_values: list[str] = Field(description="Any company values or culture indicators mentioned in the job description")
    ats_keywords: list[str] = Field(description="Important keywords to include for ATS optimization")


class CandidateAnalysis(BaseModel):
    matching_skills: list[str] = Field(description="Skills and experiences from the CV that match the job requirements")
    gaps: list[str] = Field(description="Skills or qualifications required by the job that are missing or weak in the CV")
    strongest_selling_points: list[str] = Field(description="The candidate's top 3-5 strengths most relevant to this role")
    suggested_cv_focus: list[str] = Field(description="Sections or experiences in the CV that should be emphasized or rewritten")


class JobAnalysis(BaseModel):
    job_title: str = Field(description="The title of the job being applied for")
    company_name: str = Field(description="The name of the company")
    job_requirements: JobRequirements = Field(description="Structured breakdown of the job requirements")
    candidate_analysis: CandidateAnalysis = Field(description="Analysis of the candidate's CV against the job requirements")
    overall_match_score: int = Field(description="A score from 1 to 10 indicating how well the candidate matches the role")
    overall_match_summary: str = Field(description="A 2-3 sentence summary of how well the candidate fits the role and what to focus on")


analyst_agent = Agent(
    name="Analyst Agent",
    instructions=ANALYST_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=JobAnalysis,
)