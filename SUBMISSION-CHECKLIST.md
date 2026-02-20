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
2. **To see webhook.site ping:** Go to [webhook.site](https://webhook.site), copy your unique URL. In the app, create a job: **Interval** (e.g. 5s), add the webhook URL in the "Webhook URL" field. When the job runs, webhook.site will show the POST.
3. **To see realtime quotes:** Create a job **without** a webhook URL; when it runs, the worker fetches a live quote and stores it (visible in job executions/result).
4. **Trigger execution:** The workflow runs every 5 minutes. To run **now**: GitHub → **Actions** → **Execute pending jobs** → **Run workflow**. Wait ~1 minute (Render may cold-start), then refresh the app — run count should increase and webhook.site will show the request.

---

## If jobs don’t run

- **Run the workflow manually:** Actions → **Execute pending jobs** → **Run workflow**. Wait 1–2 min (first run may wake Render from cold start), then refresh the app.
- **GitHub:** Settings → Secrets and variables → Actions → confirm `CRON_SECRET` is set (same as on Render).
- **Render:** Environment → confirm `CRON_SECRET` matches exactly (e.g. `Abhi@123`). No extra spaces.
- **Actions log:** Open the latest **Execute pending jobs** run. You should see `Response (200): {"ok":true,"stale_reset":0,"jobs_processed":1}` (or similar). If you see 401, the secret doesn’t match. If you see timeout, run the workflow again (second attempt retries after 55s).

You’re ready to submit.
