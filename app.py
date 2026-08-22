import os
import uvicorn
from backend.app.main import app

if __name__ == "__main__":
    # Hugging Face Spaces écoute sur le port 7860
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
