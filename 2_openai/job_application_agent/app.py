import gradio as gr
from dotenv import load_dotenv
from manager import JobApplicationManager

load_dotenv(override=True)


async def run_application(job_description: str, candidate_cv: str):
    """Bridge function connecting Gradio UI to the JobApplicationManager pipeline."""
    if not job_description.strip():
        yield "Please paste a job description to continue."
        return
    if not candidate_cv.strip():
        yield "Please paste your CV to continue."
        return

    output = ""
    async for chunk in JobApplicationManager().run(job_description, candidate_cv):
        output += chunk + "\n"
        yield output


# ── UI Layout ─────────────────────────────────────────────────────────────────

with gr.Blocks(title="Job Application Agent") as app:

    gr.Markdown(
        """
        # Job Application Agent
        Paste a job description and your CV. The agent will analyse the role, research the company,
        tailor your CV, write a personalized cover letter, and send your application — automatically.
        """
    )

    with gr.Row():
        with gr.Column():
            job_description_input = gr.Textbox(
                label="Job Description",
                placeholder="Paste the full job description here...",
                lines=20,
            )
        with gr.Column():
            candidate_cv_input = gr.Textbox(
                label="Your CV",
                placeholder="Paste your CV here in plain text or markdown...",
                lines=20,
            )

    with gr.Row():
        run_button = gr.Button("Run Application Agent", variant="primary", scale=2)
        clear_button = gr.Button("Clear", variant="secondary", scale=1)

    gr.Markdown("### Application Output")
    output_display = gr.Markdown(label="Output")

    # ── Event handlers ────────────────────────────────────────────────────────

    run_button.click(
        fn=run_application,
        inputs=[job_description_input, candidate_cv_input],
        outputs=output_display,
    )

    clear_button.click(
        fn=lambda: ("", "", ""),
        inputs=[],
        outputs=[job_description_input, candidate_cv_input, output_display],
    )

    gr.Markdown(
        """
        ---
        **How it works:**
        - **Stage 1** — Analyses the job description and your CV, identifies gaps and strengths
        - **Stage 2** — Researches the company, culture, recent news, and industry trends
        - **Stage 3** — Rewrites your CV with ATS keywords tailored to this specific role
        - **Stage 4** — Writes a personalized cover letter using real company insights
        - **Stage 5** — Sends your complete application via email
        """
    )


app.launch(
    server_name="0.0.0.0",
    server_port=7860,
    theme=gr.themes.Default(primary_hue="orange"),
)