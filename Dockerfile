FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Installation de ffmpeg et des certificats SSL
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copie des fichiers sources (backend, frontend, config)
COPY . .

# Création des dossiers de travail
RUN mkdir -p /app/data /tmp

EXPOSE 8000

# Lancement haute performance Uvicorn avec streaming de chunks
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
