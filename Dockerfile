FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (minimal API and full)
COPY requirements.api.txt .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.api.txt \
    && (pip install --no-cache-dir -r requirements.txt || echo "Full requirements had failures; API deps installed successfully")

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/databases/runtime /app/logs

# Set permissions for optional local initialization script
RUN chmod +x /app/initialize_databases.sh || true

# Expose default port (platforms may override with $PORT)
EXPOSE 8000

# Run the application (bind to $PORT if provided)
CMD ["sh", "-c", "exec uvicorn core.enhanced_platform:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
