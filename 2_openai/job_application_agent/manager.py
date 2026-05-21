import asyncio
from agents import Runner, trace, gen_trace_id

from analyst_agent import analyst_agent, JobAnalysis
from research_agent import research_agent, CompanyResearch
from cv_tailor_agent import cv_tailor_agent, TailoredCV
from cover_letter_agent import cover_letter_agent, CoverLetter
from email_agent import email_agent


class JobApplicationManager:

    async def run(self, job_description: str, candidate_cv: str):
        """
        Run the full job application pipeline, yielding live status updates
        and the final outputs as each stage completes.
        """
        trace_id = gen_trace_id()
        with trace("Job Application Agent", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n"

            # ── Stage 1: Analyse the job description and CV ──────────────────
            yield "Stage 1/5 — Analysing job description and CV..."
            analysis = await self.analyse(job_description, candidate_cv)
            yield (
                f"Analysis complete. Applying for **{analysis.job_title}** at "
                f"**{analysis.company_name}**. "
                f"Match score: **{analysis.overall_match_score}/10**\n"
            )
            yield f"_{analysis.overall_match_summary}_\n"

            # ── Stage 2: Research the company ────────────────────────────────
            yield "Stage 2/5 — Researching company and industry..."
            research = await self.research(analysis)
            yield f"Research complete. Found **{len(research.personalization_hooks)}** personalization hooks.\n"

            # ── Stage 3: Tailor the CV ───────────────────────────────────────
            yield "Stage 3/5 — Tailoring your CV for this role..."
            tailored_cv = await self.tailor_cv(candidate_cv, analysis, research)
            yield (
                f"CV tailored. **{len(tailored_cv.keywords_added)}** ATS keywords added. "
                f"**{len(tailored_cv.sections_modified)}** sections rewritten.\n"
            )

            # ── Stage 4: Write the cover letter ─────────────────────────────
            yield "Stage 4/5 — Writing your cover letter..."
            cover_letter = await self.write_cover_letter(tailored_cv, analysis, research)
            yield (
                f"Cover letter written. **{cover_letter.word_count} words**. "
                f"Tone: _{cover_letter.tone_used}_\n"
            )

            # ── Stage 5: Send the application email ─────────────────────────
            yield "Stage 5/5 — Sending your application email..."
            await self.send_email(analysis, tailored_cv, cover_letter)
            yield "Application email sent successfully!\n"

            # ── Final output ─────────────────────────────────────────────────
            yield "---"
            yield self._format_final_output(analysis, tailored_cv, cover_letter)

    # ── Stage methods ─────────────────────────────────────────────────────────

    async def analyse(self, job_description: str, candidate_cv: str) -> JobAnalysis:
        """Use the analyst agent to analyse the job description and CV."""
        print("Running analyst agent...")
        input_text = (
            f"Job Description:\n{job_description}\n\n"
            f"Candidate CV:\n{candidate_cv}"
        )
        result = await Runner.run(analyst_agent, input_text)
        print(f"Analysis complete — match score: {result.final_output_as(JobAnalysis).overall_match_score}/10")
        return result.final_output_as(JobAnalysis)

    async def research(self, analysis: JobAnalysis) -> CompanyResearch:
        """Use the research agent to research the company and industry."""
        print("Running research agent...")
        input_text = (
            f"Company: {analysis.company_name}\n"
            f"Job Title: {analysis.job_title}\n"
            f"Key Requirements: {', '.join(analysis.job_requirements.required_skills)}\n"
            f"Company Values Mentioned: {', '.join(analysis.job_requirements.company_values)}"
        )
        result = await Runner.run(research_agent, input_text)
        print(f"Research complete — {len(result.final_output_as(CompanyResearch).personalization_hooks)} hooks found")
        return result.final_output_as(CompanyResearch)

    async def tailor_cv(
        self,
        candidate_cv: str,
        analysis: JobAnalysis,
        research: CompanyResearch,
    ) -> TailoredCV:
        """Use the CV tailor agent to rewrite the CV for this specific role."""
        print("Running CV tailor agent...")
        input_text = (
            f"Original CV:\n{candidate_cv}\n\n"
            f"Job Title: {analysis.job_title}\n"
            f"Company: {analysis.company_name}\n"
            f"Required Skills: {', '.join(analysis.job_requirements.required_skills)}\n"
            f"Preferred Skills: {', '.join(analysis.job_requirements.preferred_skills)}\n"
            f"ATS Keywords: {', '.join(analysis.job_requirements.ats_keywords)}\n"
            f"Candidate Strengths: {', '.join(analysis.candidate_analysis.strongest_selling_points)}\n"
            f"Gaps to Address: {', '.join(analysis.candidate_analysis.gaps)}\n"
            f"Sections to Focus On: {', '.join(analysis.candidate_analysis.suggested_cv_focus)}\n"
            f"Seniority Level: {analysis.job_requirements.seniority_level}\n"
            f"Company Mission: {research.company_insights.mission_and_values}"
        )
        result = await Runner.run(cv_tailor_agent, input_text)
        print(f"CV tailored — {len(result.final_output_as(TailoredCV).keywords_added)} keywords added")
        return result.final_output_as(TailoredCV)

    async def write_cover_letter(
        self,
        tailored_cv: TailoredCV,
        analysis: JobAnalysis,
        research: CompanyResearch,
    ) -> CoverLetter:
        """Use the cover letter agent to write a personalized cover letter."""
        print("Running cover letter agent...")
        input_text = (
            f"Job Title: {analysis.job_title}\n"
            f"Company: {analysis.company_name}\n"
            f"Seniority Level: {analysis.job_requirements.seniority_level}\n"
            f"Strongest Selling Points: {', '.join(analysis.candidate_analysis.strongest_selling_points)}\n"
            f"Gaps to Address: {', '.join(analysis.candidate_analysis.gaps)}\n"
            f"Company Mission and Values: {research.company_insights.mission_and_values}\n"
            f"Company Culture: {research.company_insights.culture_and_environment}\n"
            f"Recent News: {', '.join(research.company_insights.recent_news)}\n"
            f"Personalization Hooks: {', '.join(research.personalization_hooks)}\n"
            f"Industry Trends: {', '.join(research.industry_insights.key_trends)}\n"
            f"Research Summary: {research.research_summary}\n\n"
            f"Tailored CV:\n{tailored_cv.tailored_cv_markdown}"
        )
        result = await Runner.run(cover_letter_agent, input_text)
        print(f"Cover letter written — {result.final_output_as(CoverLetter).word_count} words")
        return result.final_output_as(CoverLetter)

    async def send_email(
        self,
        analysis: JobAnalysis,
        tailored_cv: TailoredCV,
        cover_letter: CoverLetter,
    ) -> None:
        """Use the email agent to send the full application via SendGrid."""
        print("Running email agent...")
        input_text = (
            f"Job Title: {analysis.job_title}\n"
            f"Company: {analysis.company_name}\n"
            f"Match Score: {analysis.overall_match_score}/10\n\n"
            f"Cover Letter:\n{cover_letter.cover_letter_markdown}\n\n"
            f"Tailored CV:\n{tailored_cv.tailored_cv_markdown}"
        )
        await Runner.run(email_agent, input_text)
        print("Application email sent")

    # ── Output formatter ──────────────────────────────────────────────────────

    def _format_final_output(
        self,
        analysis: JobAnalysis,
        tailored_cv: TailoredCV,
        cover_letter: CoverLetter,
    ) -> str:
        """Format the final output as a structured markdown report for the Gradio UI."""
        return f"""
## Application Summary

| | |
|---|---|
| **Role** | {analysis.job_title} |
| **Company** | {analysis.company_name} |
| **Match Score** | {analysis.overall_match_score}/10 |
| **CV Keywords Added** | {len(tailored_cv.keywords_added)} |
| **Cover Letter Words** | {cover_letter.word_count} |
| **Tone** | {cover_letter.tone_used} |

---

## Match Analysis
{analysis.overall_match_summary}

**Strongest Selling Points:**
{chr(10).join(f"- {point}" for point in analysis.candidate_analysis.strongest_selling_points)}

**Gaps Addressed:**
{chr(10).join(f"- {gap}" for gap in analysis.candidate_analysis.gaps)}

---

## Tailoring Summary
{tailored_cv.tailoring_summary}

**ATS Keywords Added:**
{chr(10).join(f"`{kw}`" for kw in tailored_cv.keywords_added)}

---

## Cover Letter Strategy
{cover_letter.cover_letter_summary}

**Personalization References Used:**
{chr(10).join(f"- {ref}" for ref in cover_letter.personalization_references)}

---

## Your Tailored Cover Letter

{cover_letter.cover_letter_markdown}

---

## Your Tailored CV

{tailored_cv.tailored_cv_markdown}
"""