FROM python:3.11-slim

WORKDIR /app

# System deps needed for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the LaBSE embedding model so the container starts fast
# Remove this line if you want a smaller image and are OK with a slow first startup
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/LaBSE')"

# Copy source code
COPY . .

# Persistent data lives in volumes, not in the image
VOLUME ["/app/chroma_db", "/app/uploads"]

EXPOSE 8090

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090"]
