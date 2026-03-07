# -------------------------------
# Base image
# -------------------------------
FROM python:3.12-slim

# -------------------------------
# Set environment variables
# -------------------------------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# -------------------------------
# Set working directory
# -------------------------------
WORKDIR /app

# -------------------------------
# Copy project files
# -------------------------------
COPY . /app

# -------------------------------
# Install system dependencies required to build some Python packages
# -------------------------------
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
        gcc \
        g++ \
        libomp-dev \
        libopenblas-dev \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------
# Install Python dependencies
# -------------------------------
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------
# Expose API port
# -------------------------------
EXPOSE 8000

# -------------------------------
# Default command
# -------------------------------
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
