# Submitting the project so evaluators see workers working live

When you submit the project to a company, they will open your **live URL** (e.g. `https://job-scheduler-execution-engine-api.onrender.com/`). For them to see that **workers are actually running jobs** (run count increasing, status changing to COMPLETED, etc.), you need one of these — no paid worker service, no payment card.

---

## Option A: GitHub Actions cron (free, interview-impressive)

**Neon (DB) → Render Web Service (API only) → GitHub Actions hits `POST /api/cron/execute-pending-jobs` every 5 minutes.** No worker process; the API executes pending jobs when the cron runs. Fully free.

### 1. Render (API only)

- Deploy the **Web Service** on Render as usual. Add **`DATABASE_URL`** (Neon). Do **not** add `RUN_WORKER`.
- Add one more environment variable:
  - **Key:** `CRON_SECRET`
  - **Value:** pick a long random string (e.g. run `openssl rand -hex 32` and paste it). You’ll use the same value in GitHub.

### 2. GitHub (cron trigger)

1. In your repo: **Settings** → **Secrets and variables** → **Actions**.
2. **New repository secret:** name **`CRON_SECRET`**, value = the **same** string you set in Render.
3. **(Optional)** **New repository variable:** name **`API_URL`**, value = your live API URL (e.g. `https://job-scheduler-execution-engine-api.onrender.com`). If you don’t set it, the workflow uses the default URL in the workflow file.
4. The workflow **Execute pending jobs** (`.github/workflows/execute-pending-jobs.yml`) runs every 5 minutes and calls `POST /api/cron/execute-pending-jobs` with header `X-Cron-Secret: <CRON_SECRET>`.

### 3. What evaluators see

- They open your live URL, create a job (e.g. interval every 5 seconds). Within about 5 minutes (next cron run), the job runs and **run(s)** increase. For faster feedback during demo, they can trigger the workflow manually from the **Actions** tab → **Execute pending jobs** → **Run workflow**.

---

## Option B: One service — API + worker together

Your **existing** Render (or other) **Web Service** can run both the API and the worker in a single process. No second service, no extra cost.

### On Render

1. Open [Render Dashboard](https://dashboard.render.com) → your **Web Service** (the one serving the app).
2. Go to **Environment**.
3. Add a variable:
   - **Key:** `RUN_WORKER`
   - **Value:** `true`
4. **Save Changes**. Render will redeploy automatically.
5. After deploy, create a job on the live site (e.g. an interval job). Within a few seconds you should see **run(s)** increase and status update — the worker is running in the same container as the API.

Evaluators can then:

- Open your live URL.
- Create a job (e.g. “Interval” every 5 seconds, or “One time” with a future time).
- See the job move from SCHEDULED → RUNNING → COMPLETED and **run(s)** increase, proving the worker is working in production.

### How it works

- The Docker image starts a small script that checks `RUN_WORKER`.
- If `RUN_WORKER=true`, it starts the worker in the background (health on port 9090) and then starts the API (uvicorn on `PORT`). Both use the same `DATABASE_URL`.
- If `RUN_WORKER` is not set, only the API runs (previous behavior).

### Turning it off

To run only the API again (e.g. if you switch to Option A), remove the `RUN_WORKER` variable or set it to `false`, then redeploy.

---

**Summary:** Use **Option A** (GitHub Actions cron) for a clean, free, no-worker setup. Use **Option B** (RUN_WORKER=true) if you want jobs to run every few seconds without waiting for the 5-minute cron.
