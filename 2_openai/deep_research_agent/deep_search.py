import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

async def run_research(query: str):
    async for chunk in ResearchManager().run_research(query):
        yield chunk

with gr.Blocks(theme=gr.themes.Default(primary_hue="orange")) as app:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run Research", variant="primary")
    report = gr.Markdown(label="Final Report")

    run_button.click(fn=run_research, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run_research, inputs=query_textbox, outputs=report)

app.launch(inbrowser=True)