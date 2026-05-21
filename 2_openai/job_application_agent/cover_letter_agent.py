from pydantic import BaseModel, Field
from agents import Agent


COVER_LETTER_INSTRUCTIONS = (
    "You are an expert cover letter writer with a proven track record of writing compelling, "
    "personalized cover letters that get candidates noticed and land interviews. "
    "You will be given a tailored CV, a structured job analysis, and detailed company research.\n"
    "Your job is to write a cover letter that feels genuinely human, specific, and compelling — "
    "not a generic template. You should:\n"
    "1. Open with a strong, attention-grabbing hook that references something specific about "
    "the company — not 'I am writing to apply for...'\n"
    "2. Demonstrate genuine knowledge of the company using the research provided — "
    "reference recent news, company values, or specific initiatives\n"
    "3. Connect the candidate's strongest selling points directly to the role's key requirements\n"
    "4. Address any CV gaps confidently by highlighting transferable skills or relevant context\n"
    "5. Mirror the tone and language of the job description — formal for corporate roles, "
    "energetic for startups, technical for engineering roles\n"
    "6. Close with a confident, specific call to action — not a passive 'I hope to hear from you'\n\n"
    "Structure the cover letter as follows:\n"
    "- Opening hook (1 paragraph) — specific, compelling, company-aware\n"
    "- Why this company (1 paragraph) — genuine, researched, values-aligned\n"
    "- Why I am the right fit (1-2 paragraphs) — evidence-based, achievement-focused\n"
    "- Closing (1 paragraph) — confident, clear call to action\n\n"
    "Important rules:\n"
    "- Maximum 400 words — hiring managers do not read long cover letters\n"
    "- Never use clichés like 'I am a team player', 'passionate about', or 'quick learner'\n"
    "- Never fabricate experience or achievements not found in the CV\n"
    "- Write in first person, professional but warm tone\n"
    "- The final cover letter must be in clean markdown format"
)


class CoverLetterSection(BaseModel):
    section_name: str = Field(description="The name of the cover letter section e.g. Opening Hook, Why This Company")
    content: str = Field(description="The written content for this section")
    strategy: str = Field(description="The strategic reasoning behind this section's approach")


class CoverLetter(BaseModel):
    job_title: str = Field(description="The job title this cover letter is written for")
    company_name: str = Field(description="The company this cover letter is addressed to")
    cover_letter_markdown: str = Field(
        description="The complete cover letter in clean markdown format, "
                    "ready to be sent to the employer"
    )
    sections: list[CoverLetterSection] = Field(
        description="A breakdown of each section of the cover letter with the strategy behind it"
    )
    personalization_references: list[str] = Field(
        description="Specific company or industry references woven into the letter "
                    "from the research provided, demonstrating genuine knowledge"
    )
    tone_used: str = Field(
        description="The tone adopted for this cover letter and why, "
                    "based on the role seniority and company culture"
    )
    word_count: int = Field(
        description="The total word count of the cover letter — must be under 400 words"
    )
    cover_letter_summary: str = Field(
        description="A 2-3 sentence summary of the strategic approach taken "
                    "and what makes this cover letter stand out"
    )


cover_letter_agent = Agent(
    name="Cover Letter Agent",
    instructions=COVER_LETTER_INSTRUCTIONS,
    model="gpt-4o",
    output_type=CoverLetter,
)