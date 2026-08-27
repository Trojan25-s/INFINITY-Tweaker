FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements & install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV INFINITY_HOST=0.0.0.0
ENV PORT=8000

# Expose server port
EXPOSE 8000

# Run FastAPI Licensing Backend Server with dynamic PORT support
CMD ["sh", "-c", "uvicorn Backend.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
