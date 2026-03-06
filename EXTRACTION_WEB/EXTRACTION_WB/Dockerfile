# Dockerfile pour World Bank Data Extraction

FROM python:3.11-slim

LABEL maintainer="Tsinjo <tsinjo@example.com>"
LABEL description="World Bank Data Collector for Chatbot RAG"

WORKDIR /app

# Installation dépendances système
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie requirements et installation dépendances Python
COPY EXTRACTION_WB/requirements.txt ./extraction_requirements.txt
RUN pip install --no-cache-dir -r extraction_requirements.txt

# Copie code source extraction
COPY EXTRACTION_WB/ ./EXTRACTION_WB/

# Copie config (si existe)
COPY config.json* ./

# Créer dossier data
RUN mkdir -p data

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Healthcheck (vérifie que Python fonctionne)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Command par défaut: lancer le collecteur
CMD ["python", "-m", "EXTRACTION_WB.collector"]
