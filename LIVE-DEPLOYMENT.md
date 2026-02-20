# Live deployment options

The app can run jobs in production in two ways without a separate paid worker service.

---

## Option A: GitHub Actions cron (recommended)

**Neon (DB) → Render Web Service (API) → GitHub Actions** calls `POST /api/cron/execute-pending-jobs` every 5 minutes. No worker process; the API executes pending jobs when the cron runs.

### Render

- Deploy the **Web Service** with **`DATABASE_URL`** (Neon) and **`CRON_SECRET`** (any secure random string). Same value must be set in GitHub Actions secrets.

### GitHub

- **Settings** → **Secrets and variables** → **Actions**: add secret **`CRON_SECRET`** (same value as Render).
- Optional: add variable **`API_URL`** with your live API base URL (default in workflow is the Render URL).
- Workflow **Execute pending jobs** (`.github/workflows/execute-pending-jobs.yml`) runs every 5 minutes. To run immediately: **Actions** → **Execute pending jobs** → **Run workflow**.

---

## Option B: API + worker in one service

Run both the API and the worker in the same Render Web Service.

- **Environment:** add **`RUN_WORKER`** = **`true`**.
- Redeploy. The container starts the worker in the background and the API on `PORT`. Jobs run every few seconds (no 5‑minute wait).

To switch back to cron-only, remove `RUN_WORKER` or set it to `false` and redeploy.
