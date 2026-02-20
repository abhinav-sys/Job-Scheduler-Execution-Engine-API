# Multi-stage Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY . .
# Don't run as root in production
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Start script: if RUN_WORKER=true, runs worker + API in one container (for demo/submission)
RUN chmod +x /app/scripts/start-api-with-worker.sh
CMD ["sh", "-c", "./scripts/start-api-with-worker.sh"]
