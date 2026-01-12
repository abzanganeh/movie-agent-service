FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements-docker.txt* ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY app.py ./

# Copy templates and static files (if they exist)
COPY templates/ ./templates/ 2>/dev/null || true
COPY static/ ./static/ 2>/dev/null || true

# Copy data directory (if exists)
COPY data/ ./data/ 2>/dev/null || true

# Copy vector store (if pre-built, optional)
COPY movie_vectorstore/ ./movie_vectorstore/ 2>/dev/null || true

# Expose port (Hugging Face Spaces uses port 7860)
EXPOSE 7860

# Set environment variables
ENV PORT=7860
ENV PYTHONUNBUFFERED=1

# Run Flask app
CMD ["python", "app.py"]
