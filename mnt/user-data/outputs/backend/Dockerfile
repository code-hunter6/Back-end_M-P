FROM python:3.12-slim

# Don't write .pyc files; stream logs straight to the container output.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Build deps for asyncpg/bcrypt, plus curl for the healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first so pip install is cached when only source changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run as a non-root user — a container process should never be root.
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# --reload is deliberately NOT here; docker-compose adds it for local dev only.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
