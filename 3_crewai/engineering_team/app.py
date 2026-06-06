import gradio as gr
import os
from engineering_team.crew import EngineeringTeam

os.makedirs("output", exist_ok=True)

def run_crew(requirements, module_name, class_name):
    inputs = {
        "requirements": requirements,
        "module_name": module_name,
        "class_name": class_name
    }
    result = EngineeringTeam().crew().kickoff(inputs=inputs)
    
    # Read generated files
    outputs = {}
    for filename in [module_name, "app.py", f"test_{module_name}", f"{module_name.replace('.py', '')}_design.md"]:
        path = f"output/{filename}"
        if os.path.exists(path):
            with open(path) as f:
                outputs[filename] = f.read()
    
    return (
        outputs.get(module_name, "Not generated"),
        outputs.get("app.py", "Not generated"),
        outputs.get(f"test_{module_name}", "Not generated"),
        outputs.get(f"{module_name.replace('.py','')}_design.md", "Not generated")
    )

with gr.Blocks(title="Engineering Team") as demo:
    gr.Markdown("# Engineering Team — CrewAI")
    
    with gr.Row():
        requirements = gr.Textbox(label="Requirements", lines=6, placeholder="Describe what you want to build...")
        with gr.Column():
            module_name = gr.Textbox(label="Module Name", value="accounts.py")
            class_name = gr.Textbox(label="Class Name", value="Account")
    
    run_btn = gr.Button("Run Engineering Team", variant="primary")
    
    with gr.Tabs():
        with gr.Tab("Backend Module"):
            backend_out = gr.Code(language="python", label="Generated Module")
        with gr.Tab("Gradio UI"):
            frontend_out = gr.Code(language="python", label="Generated app.py")
        with gr.Tab("Unit Tests"):
            test_out = gr.Code(language="python", label="Generated Tests")
        with gr.Tab("Design Doc"):
            design_out = gr.Markdown(label="Design Document")
    
    run_btn.click(run_crew, inputs=[requirements, module_name, class_name],
                  outputs=[backend_out, frontend_out, test_out, design_out])

demo.launch()