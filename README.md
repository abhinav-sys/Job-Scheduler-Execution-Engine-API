# Job Scheduler & Execution Engine

Production-grade job scheduler with FastAPI, PostgreSQL, SQLAlchemy 2.0 (async), Alembic, and Docker. Separate **API** and **worker** with concurrency-safe execution and crash recovery.

| | |
|---|---|
| **Live demo** | [https://job-scheduler-execution-engine-api.onrender.com](https://job-scheduler-execution-engine-api.onrender.com) |
| **API docs** | [/docs](https://job-scheduler-execution-engine-api.onrender.com/docs) · **Health** [/health](https://job-scheduler-execution-engine-api.onrender.com/health) |
| **Repo** | [GitHub](https://github.com/abhinav-sys/Job-Scheduler-Execution-Engine-API) |

Jobs run via GitHub Actions (cron every 5 min) or in-process worker; see [LIVE-DEPLOYMENT.md](LIVE-DEPLOYMENT.md) and [LIVE-DEMO.md](LIVE-DEMO.md).

## Architecture

```
Client → FastAPI API → PostgreSQL
                        ↑
                     Worker Service( s )
```

- **API**: REST API for creating and listing jobs.
- **Worker**: Polls the database every 5 seconds, claims one job at a time with row-level locking, executes it, and updates status and retries.
- **PostgreSQL**: Single source of truth; all state is durable in the DB.

## Tech Stack

- **FastAPI** – API
- **PostgreSQL** – persistence
- **SQLAlchemy 2.0 (async)** – ORM with asyncpg
- **Alembic** – migrations
- **Pydantic v2** – validation
- **Docker & Docker Compose** – run API, worker(s), and Postgres

## Deploy API to Vercel (with Neon)

1. **Database**: Use [Neon](https://neon.tech). Your connection URL is `postgresql://...`. For this app set:
   ```bash
   DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST/DB?sslmode=require
   ```
   (Same URL with `postgresql+asyncpg` instead of `postgresql`.)

2. **Push to GitHub** (e.g. repo: `abhinav-sys/Job-Scheduler-Execution-Engine-API`):
   ```bash
   git init && git add . && git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/abhinav-sys/Job-Scheduler-Execution-Engine-API.git
   git push -u origin main
   ```

3. **Vercel**: Import the repo → add env var `DATABASE_URL` (async Neon URL above) → Deploy.  
   The API runs from `index.py` (see `vercel.json`). **Worker does not run on Vercel**; deploy it to Railway/Render (see [DEPLOY.md](DEPLOY.md)).

4. **Worker**: Deploy to [Railway](https://railway.app) (or Render), same `DATABASE_URL`, start command: `python -m app.worker.main`.

See **[DEPLOY.md](DEPLOY.md)** for step-by-step Vercel + Neon + Railway.

---

## Quick Start (local)

### With Docker Compose (recommended)

```bash
docker-compose up --build
```

- **Frontend (web UI):** http://localhost:8001 — create jobs, view list and status.  
- API: http://localhost:8001 (port 8001 to avoid conflict with other services; change in `docker-compose.yml` if needed)  
- Docs: http://localhost:8001/docs  
- Health: http://localhost:8001/health  

Create a one-time job:

```bash
curl -X POST http://localhost:8001/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"name":"my-job","schedule_type":"one_time","run_at":"2026-12-31T12:00:00Z","max_retries":3}'
```

Create an interval job (runs every 10 seconds):

```bash
curl -X POST http://localhost:8001/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"name":"interval-job","schedule_type":"interval","interval_seconds":10,"max_retries":2}'
```

### Live test (recommended)

1. Open **http://localhost:8001** (frontend).
2. Click **Run test job now**. A 5-second interval job is created and the list auto-refreshes every 2s for 20s.
3. Watch the new job move from **SCHEDULED** to **COMPLETED** (or **RUNNING** briefly). Run count increases each cycle.
4. By default the worker uses **0% simulated failure** so demos succeed; set `WORKER_FAILURE_PROBABILITY=0.3` (e.g. in `.env` or Docker) to test retries.

### Running multiple workers

To run several worker containers (same code, same DB):

```bash
docker-compose up --build --scale worker=3
```

Or set in `docker-compose.yml`:

```yaml
worker:
  ...
  deploy:
    replicas: 3
```

Only one worker will process a given job at a time thanks to **row-level locking** (see below).

---

## How concurrency is handled

- **No duplicate execution**: The worker selects a single row with:
  ```sql
  SELECT * FROM jobs
  WHERE status = 'SCHEDULED' AND (run_at IS NULL OR run_at <= NOW())
  ORDER BY run_at ASC NULLS LAST
  LIMIT 1
  FOR UPDATE SKIP LOCKED;
  ```
  `FOR UPDATE` locks the row in the current transaction; `SKIP LOCKED` makes other workers skip that row and pick another (or nothing), so the same job is never claimed by two workers.

- **Atomic state transition**: After selecting the row, the worker updates `status` to `RUNNING` in the **same transaction** before committing. So the transition `SCHEDULED → RUNNING` is atomic and visible to other workers only after commit.

- **Multiple workers**: Each worker runs the same poll loop; each poll claims at most one job. With 3 workers you can process up to 3 jobs concurrently (different rows), with no double execution of the same job.

---

## How crash recovery works

- If a worker dies after setting a job to `RUNNING` but before setting it to `COMPLETED` or `FAILED`, that job would stay `RUNNING` forever.

- **Stale job reset**: On every poll cycle, before claiming new work, the worker runs a **crash recovery** step: it resets any job in `RUNNING` whose `updated_at` is older than a configured threshold (default 10 minutes) back to `SCHEDULED`. So a job that was “in progress” when the worker crashed will be picked up again by any worker.

- Threshold is configured via `WORKER_STALE_RUNNING_MINUTES` (e.g. in `.env` or Docker env).

---

## How durability is ensured

- **State in DB only**: Job and job execution state (status, retry_count, run_at, etc.) live only in PostgreSQL. No in-memory queue.

- **Idempotent retry**: On simulated failure, the worker records a `JobExecution` row (attempt number, status FAILED, error_message), increments `retry_count`, and sets the job back to `SCHEDULED` until `retry_count` reaches `max_retries`, then sets the job to `FAILED`. Retries are driven by the same polling and locking; no duplicate execution thanks to `FOR UPDATE SKIP LOCKED`.

- **Server/container restart**: After a restart, workers reconnect to the same DB and continue polling. No extra recovery step is required beyond the stale-`RUNNING` reset above.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/jobs` | Create a job (body: name, schedule_type, run_at / interval_seconds, max_retries, optional payload) |
| GET | `/api/jobs` | List jobs (query: `status`, `schedule_type`, `limit`, `offset`) |
| GET | `/api/jobs/{id}` | Get one job and its executions |
| GET | `/health` | Health check |

### Validation rules

- **one_time**: `run_at` required, must be in the future (timezone-aware). No `interval_seconds`.
- **interval**: `interval_seconds` required and > 0. Optional `run_at` for first run (must be future if set).
- Invalid combinations (e.g. one_time with interval_seconds) are rejected with 422.

---

## Execution engine (worker) behavior

- Polls the DB every **5 seconds** (configurable: `WORKER_POLL_INTERVAL_SECONDS`).
- Uses **SELECT ... FOR UPDATE SKIP LOCKED** and processes **one job per poll**.
- Simulates work with a random sleep of 1–3 seconds. **Failure rate** is configurable: `WORKER_FAILURE_PROBABILITY` (default **0** for demos; **0.3** to test retries).
- **Retries**: On failure, creates a `JobExecution` (FAILED), increments `retry_count`, and sets job back to `SCHEDULED` until `retry_count >= max_retries`, then sets job to `FAILED`.
- **Interval jobs**: On success, sets next `run_at = now + interval_seconds` and status back to `SCHEDULED`.
- **Crash recovery**: Before each poll, resets `RUNNING` jobs older than `WORKER_STALE_RUNNING_MINUTES` to `SCHEDULED`.

---

## Deployment (why not Vercel for the worker)

- **Vercel is serverless**: No long-running processes, no persistent polling, no custom Docker images. The worker needs a **continuous loop** and **persistent DB connections**, so it cannot run on Vercel.

**Suggested split:**

| Component | Where to deploy |
|-----------|------------------|
| FastAPI API | Vercel (serverless) or same host as worker |
| Worker | Railway, Render, or EC2 (Docker or process) |
| PostgreSQL | Neon, Supabase, or managed Postgres |

**Simplest production option:** Run **everything in Docker** on one host (Railway, Render, or EC2): same `docker-compose.yml` with `api`, `worker`, and external or managed Postgres. That way you get one deployment unit and clear concurrency/crash-recovery behavior as in this README.

---

## Project layout

```
app/
├── api/
│   └── routes/       # FastAPI routers (jobs)
├── core/
│   └── config.py     # Settings
├── db/
│   └── session.py    # Async engine and session
├── models/           # SQLAlchemy models (Job, JobExecution)
├── schemas/          # Pydantic schemas
├── services/         # Business logic (JobService)
├── worker/
│   └── main.py      # Polling loop, FOR UPDATE SKIP LOCKED, execution, crash recovery
├── main.py           # FastAPI app
Dockerfile
docker-compose.yml
alembic/
README.md
```

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/job_scheduler` | Async Postgres URL |
| `WORKER_POLL_INTERVAL_SECONDS` | 5 | Seconds between poll cycles |
| `WORKER_STALE_RUNNING_MINUTES` | 10 | Minutes after which RUNNING is reset to SCHEDULED |
| `WORKER_EXECUTION_MIN_SLEEP` | 1 | Min simulated execution time (seconds) |
| `WORKER_EXECUTION_MAX_SLEEP` | 3 | Max simulated execution time (seconds) |
| `WORKER_FAILURE_PROBABILITY` | 0 | Simulated failure rate (0–1); use 0.3 to test retries |

---

## Migrations

With a local or composed Postgres:

```bash
# Create .env with DATABASE_URL if needed
alembic upgrade head
```

In Docker, run once after Postgres is up:

```bash
docker-compose run api alembic upgrade head
```

(If you rely on `init_db()` in the API lifespan, tables are created on first run without Alembic; use Alembic for versioned schema changes.)

---

## Optional improvements (senior-level)

- **Optimistic locking**: Use the `version` column on `Job` (already in the model) and increment it on update; reject updates with stale version to avoid lost updates.
- **Idempotency key**: Accept an idempotency key on `POST /jobs` and deduplicate by key so duplicate requests create only one job.
- **Exponential backoff**: For retries, set `run_at = now + 2^retry_count` (or similar) instead of running at next poll.
- **Structured logging**: Replace `print` in the worker with `structlog` or standard `logging` with JSON output.
- **Tests**: Add `pytest` + `pytest-asyncio` and `httpx` for API tests and unit tests for the worker logic.

This project demonstrates **transaction isolation**, **concurrency control**, **state machine design**, and **failure handling** suitable for mid-to-senior backend discussions.
