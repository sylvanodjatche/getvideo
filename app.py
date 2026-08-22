import os
import gradio as gr
from backend.app.main import app as fastapi_app

# Interface Gradio avec intégration de GetVideo
with gr.Blocks(title="GetVideo 2.0", css="footer {visibility: hidden} body {margin: 0; padding: 0; overflow: hidden;}") as demo:
    gr.HTML("""
        <iframe src="/index.html" style="position:fixed; top:0; left:0; bottom:0; right:0; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999999;"></iframe>
    """)

# Montage de notre API FastAPI complète sur Gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_api=False)
