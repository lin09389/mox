# Mox - LLM Adversarial Attack & Defense Platform
# Multi-stage build for optimized production image using uv

FROM python:3.11-slim as builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies (caching layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code and install the project
COPY . .
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi7 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash mox

# Copy the virtual environment from builder
COPY --from=builder --chown=mox:mox /app/.venv /app/.venv

# Copy application code
COPY --chown=mox:mox . .

# Create data directory
RUN mkdir -p /data && chown mox:mox /data

# Switch to non-root user
USER mox

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/app/.venv/bin:$PATH \
    PYTHONPATH=/app

# Expose ports
EXPOSE 8000 7860 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default: Run API server
CMD ["python", "-m", "mox", "api"]
