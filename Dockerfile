FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dépendances système légères
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie des sources backend et frontend
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

EXPOSE 8000

# Lancement de FastAPI
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
