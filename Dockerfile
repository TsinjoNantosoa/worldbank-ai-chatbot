# Dockerfile - World Bank Chatbot (FastAPI + RAG)

FROM python:3.11-slim

LABEL maintainer="Tsinjo"
LABEL description="World Bank Data Chatbot with RAG"

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie requirements
COPY requirements.txt .

# Installation dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie code application
COPY core/ ./core/
COPY models/ ./models/
COPY templates/ ./templates/
COPY static/ ./static/
COPY app.py .
COPY config.json* ./

# Créer dossiers nécessaires
RUN mkdir -p data data/faiss_index templates static

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Exposition port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Command par défaut
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
