FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=7860

# Installation de ffmpeg et utilitaires système
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Création de l'utilisateur non-root (requis par Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Installation des dépendances Python
COPY --chown=user backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

# Copie de tous les fichiers du projet
COPY --chown=user . $HOME/app

# Port officiel Hugging Face Spaces
EXPOSE 7860

# Lancement propre de l'application FastAPI
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
