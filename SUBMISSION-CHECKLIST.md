# Submission checklist (live demo ready)

Use this to confirm everything is set and to show evaluators that jobs run in production.

---

## What’s already set (you did this)

- **Neon** – database (DATABASE_URL)
- **Render** – Web Service with `DATABASE_URL` and `CRON_SECRET` (rebuilt/deployed)
- **GitHub** – repo secret `CRON_SECRET` and variable `API_URL` (optional)
- **GitHub Actions** – workflow **Execute pending jobs** runs every 5 minutes

---

## Live URLs

| What        | URL |
|------------|-----|
| **App (UI)** | https://job-scheduler-execution-engine-api.onrender.com/ |
| **API docs** | https://job-scheduler-execution-engine-api.onrender.com/docs |
| **Health**   | https://job-scheduler-execution-engine-api.onrender.com/health |

---

## Quick test (you or evaluators)

1. Open the **App** URL above.
2. Create a job: e.g. **Interval**, every 5 seconds, name "demo-job".
3. **Option A – wait:** Within about **5 minutes** the workflow runs and the job executes (run count increases).
4. **Option B – run now:** In GitHub go to **Actions** → **Execute pending jobs** → **Run workflow**. Wait ~30 seconds, then refresh the app; the job should have run.

---

## If jobs don’t run

- **GitHub:** Settings → Secrets and variables → Actions → confirm `CRON_SECRET` is set.
- **Render:** Environment → confirm `CRON_SECRET` matches the GitHub secret exactly (same value).
- **Actions:** Open the latest **Execute pending jobs** run; check the log for "Response (200)" and "jobs_processed".

You’re ready to submit.
