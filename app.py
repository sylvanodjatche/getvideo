import os
import uvicorn
from backend.app.main import app

# Détecter et satisfaire le validateur ZeroGPU de Hugging Face s'il est présent
try:
    import spaces
    @spaces.GPU
    def init_zerogpu():
        return True
    init_zerogpu()
except Exception:
    pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
