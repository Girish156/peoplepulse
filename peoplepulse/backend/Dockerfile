# ---------- Stage 1: build dependencies ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
# Extract dependencies and install into a prefix for copying
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir \
        "fastapi>=0.115.0" \
        "uvicorn[standard]>=0.32.0" \
        "sqlalchemy>=2.0.36" \
        "alembic>=1.14.0" \
        "psycopg2-binary>=2.9.10" \
        "pydantic>=2.9.0" \
        "pydantic[email]>=2.9.0" \
        "email-validator>=2.2.0" \
        "pydantic-settings>=2.6.0" \
        "pandas>=2.2.0" \
        "numpy>=1.26.0" \
        "python-jose[cryptography]>=3.3.0" \
        "passlib[bcrypt]>=1.7.4" \
        "python-multipart>=0.0.12" \
        "httpx>=0.28.0" \
        "pytest>=8.3.0" \
        "pytest-asyncio>=0.24.0" \
        "pytest-cov>=6.0.0" \
        "anyio>=4.7.0"

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy site-packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Runtime system dependencies only (libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy application source
COPY . .

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
