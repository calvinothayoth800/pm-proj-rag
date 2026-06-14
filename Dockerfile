FROM python:3.11-slim

# Cache buster - change this to force rebuild
ARG CACHE_BUST=20240614-3

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy only necessary files (NOT .venv, NOT data/)
COPY setup.py .
COPY src/ src/
COPY configs/ configs/
COPY scripts/ scripts/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Create data directories (index built at runtime via start.sh)
RUN mkdir -p data/raw data/processed data/indexes

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Make startup script executable
RUN chmod +x scripts/start.sh

# Expose HF Spaces required port
EXPOSE 7860

# Run startup script (builds index if needed, then starts server)
CMD ["bash", "scripts/start.sh"]
