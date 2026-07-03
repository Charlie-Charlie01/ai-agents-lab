# Import the necessary libraries
import asyncio
import gradio as gr
from sidekick import Sidekick
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Initialize sidekick before the UI launches
sidekick_instance = None

async def setup():
    # Initialize the sidekick instance
    global sidekick_instance
    sidekick_instance = Sidekick()
    await sidekick_instance.setup()
    return sidekick_instance

async def process_message(sidekick, message, success_criteria, history):
     # Fall back to global instance if state is None
    agent = sidekick or sidekick_instance
    if agent is None:
        return history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": "Sidekick is still initializing, please try again in a moment."}
        ], None
    results = await agent.run_superstep(message, success_criteria, history)
    return results, agent

async def reset():
    global sidekick_instance
    if sidekick_instance:
        await sidekick_instance.cleanup()
    sidekick_instance = Sidekick()
    await sidekick_instance.setup()
    return "", "", None, sidekick_instance

async def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            await sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")

with gr.Blocks(title="Sidekick") as ui:
    gr.Markdown("## Sidekick Personal Co-Worker")
    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=300)
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False, placeholder="What are your success critiera?"
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [sidekick])
    message.submit(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )
    success_criteria.submit(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )
    go_button.click(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )
    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick])


ui.launch(inbrowser=True, theme=gr.themes.Default(primary_hue="emerald"))

