FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY ./scheduler/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared package
COPY ./shared /shared
RUN pip install -e /shared

# Copy application code
COPY ./scheduler .

# Run scheduler
CMD ["python", "-m", "scheduler.main"]
