FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install system dependencies for build packages (psycopg2, greenlet, etc) and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase
COPY . /app/

# Expose port
EXPOSE 8000

# Start app using uvicorn (inside /app, the module root is app.main:app)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
