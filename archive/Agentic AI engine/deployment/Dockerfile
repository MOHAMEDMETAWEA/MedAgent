# MEDAgent Multi-Agent Smart Hospital System
# Production Dockerfile

FROM python:3.11-slim

# Install system dependencies for PDF generation and FAISS
RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create directory for medical data and uploads
RUN mkdir -p data/uploads

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000
EXPOSE 8501

# Entrypoint script to run both services
CMD ["python", "run_system.py"]
