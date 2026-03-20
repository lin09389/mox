FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip wheel

RUN pip install --no-cache-dir -e ".[dev]"


FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY pyproject.toml .
COPY mox mox/
COPY examples examples/
COPY docs docs/
COPY data data/

RUN useradd -m -u 1000 mox && chown -R mox:mox /app
USER mox

ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV MOX_HOST=0.0.0.0
ENV MOX_PORT=8000

EXPOSE 8000 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "-m", "mox", "api"]
