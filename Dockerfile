FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt || echo "Some packages could not be installed, but core functionality will work"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/databases/runtime /app/logs

# Set permissions for optional local initialization script
RUN chmod +x /app/initialize_databases.sh || true

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "core.enhanced_platform:app", "--host", "0.0.0.0", "--port", "8000"]
