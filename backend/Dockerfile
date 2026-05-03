FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (required for some Python packages like psycopg2/asyncpg or cryptography)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Run Alembic migrations and start FastAPI via Uvicorn
# Note: In production, migrations should ideally be run in a separate CI/CD step,
# but running them on startup is common for simple App Service setups.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
