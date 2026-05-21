from pydantic import BaseModel, Field
from agents import Agent


CV_TAILOR_INSTRUCTIONS = (
    "You are an expert CV writer and career coach with years of experience tailoring CVs "
    "for specific job applications. You will be given the candidate's original CV, a structured "
    "job analysis, and company research.\n"
    "Your job is to rewrite and tailor the CV to maximise the candidate's chances of getting "
    "an interview for this specific role. You should:\n"
    "1. Reorder and rewrite bullet points to lead with the most relevant experience\n"
    "2. Mirror the exact language and keywords from the job description for ATS optimization\n"
    "3. Quantify achievements wherever possible (e.g. 'improved performance by 40%')\n"
    "4. Remove or de-emphasize experiences that are irrelevant to this role\n"
    "5. Strengthen the professional summary to speak directly to this role and company\n"
    "6. Ensure the tone and seniority level matches the job description\n"
    "7. Highlight skills that directly address the identified gaps where the candidate has "
    "transferable experience\n\n"
    "Important rules:\n"
    "- Never fabricate experience, qualifications, or achievements\n"
    "- Only reframe and reorder what already exists in the original CV\n"
    "- Keep the CV to a professional length — prioritize quality over quantity\n"
    "- The final CV must be in clean, well-structured markdown format"
)


class CVSection(BaseModel):
    section_name: str = Field(description="The name of the CV section e.g. Professional Summary, Experience, Skills")
    original_content: str = Field(description="The original content from the candidate's CV for this section")
    tailored_content: str = Field(description="The rewritten, tailored content for this section")
    changes_made: list[str] = Field(description="A list of specific changes made to this section and why")


class TailoredCV(BaseModel):
    job_title: str = Field(description="The job title this CV has been tailored for")
    company_name: str = Field(description="The company this CV has been tailored for")
    tailored_cv_markdown: str = Field(
        description="The complete tailored CV in clean, well-structured markdown format, "
                    "ready to be sent to the employer"
    )
    sections_modified: list[CVSection] = Field(
        description="A breakdown of each CV section that was modified, with before and after content"
    )
    keywords_added: list[str] = Field(
        description="ATS keywords from the job description that were woven into the tailored CV"
    )
    tailoring_summary: str = Field(
        description="A 2-3 sentence summary of the key changes made and why, "
                    "to help the candidate understand what was prioritized"
    )


cv_tailor_agent = Agent(
    name="CV Tailor Agent",
    instructions=CV_TAILOR_INSTRUCTIONS,
    model="gpt-4o",
    output_type=TailoredCV,
)