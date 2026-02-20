# Live demo guide

## Links

| | |
|---|---|
| **App (UI)** | https://job-scheduler-execution-engine-api.onrender.com/ |
| **API docs** | https://job-scheduler-execution-engine-api.onrender.com/docs |
| **Health** | https://job-scheduler-execution-engine-api.onrender.com/health |

---

## Try it

1. Open the **App** link. Create a job: **Interval** (e.g. every 5 seconds), optional **Webhook URL** (e.g. from [webhook.site](https://webhook.site)).
2. **With webhook URL:** When the job runs, webhook.site receives a POST with job details.
3. **Without webhook URL:** The worker fetches a live quote from an external API; the result appears under the job.
4. Jobs are executed every 5 minutes by the GitHub Actions workflow. To run sooner: **GitHub** → **Actions** → **Execute pending jobs** → **Run workflow**, then wait ~1 minute and refresh the app.

---

## If jobs stay at 0 runs

- Run the workflow manually (see above). First request may wake Render from cold start; the workflow retries after 55s if needed.
- Ensure **`CRON_SECRET`** is set on Render and in GitHub Actions and that both values match exactly.
- Check the latest **Execute pending jobs** run in Actions: log should show `Response (200)` and `jobs_processed`.
