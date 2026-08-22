import os
import gradio as gr
from backend.app.main import app as fastapi_app

# Gradio Wrapper compatible Hugging Face Spaces
with gr.Blocks(title="GetVideo 2.0") as demo:
    gr.HTML('<meta http-equiv="refresh" content="0; url=/">')

# Montage de notre application FastAPI complète
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    import uvicorn
    uvicorn.run(fastapi_app, host="0.0.0.0", port=port)
