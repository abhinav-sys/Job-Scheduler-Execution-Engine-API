#!/bin/sh
# Run API and optionally worker in one process (for single-service deploy so evaluators see jobs running).
# Set RUN_WORKER=true to run both; otherwise only the API runs.
set -e
if [ "$RUN_WORKER" = "true" ] || [ "$RUN_WORKER" = "1" ]; then
  export WORKER_HEALTH_PORT="${WORKER_HEALTH_PORT:-9090}"
  python -m app.worker.main &
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
