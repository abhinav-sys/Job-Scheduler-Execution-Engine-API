# Interview showcase — what this project does (real work)

Use this to explain your project in an interview. Everything the worker does is **real**, not simulated.

---

## What runs in production

1. **API (FastAPI)** — Create and list jobs via REST; optional web UI at `/`.
2. **Worker** — Polls Postgres every 5s, claims one job at a time with `FOR UPDATE SKIP LOCKED`, then does **real work**.
3. **PostgreSQL** — Single source of truth; durable state, crash recovery, no in-memory queue.

---

## Real work the worker does (no fake “sleep and random fail”)

- **If the job has a webhook URL** (in `payload.webhook_url` or `payload.callback_url`):  
  The worker **POSTs** to that URL with job id, name, run time, and attempt. You can use [webhook.site](https://webhook.site) or [RequestBin](https://requestbin.com) and show the interviewer the **real HTTP request** that arrived when the job ran.  
  **Remember:** Worker uses `verify=False` and trims the URL so webhook.site works from Docker; if the POST fails, the red error under the job in the UI shows the reason.

- **Otherwise:**  
  The worker **calls a real public API** ([quotable.io](https://api.quotable.io/random)), gets a **real quote**, and **stores it** in the execution record. The UI shows that quote under the job (e.g. *"The only way to do great work is to love what you do." — Steve Jobs*).

So every run is either:
- a **real outbound HTTP call** (webhook), or  
- a **real inbound API call + stored result** (quote).

---

## How to demo in 2 minutes

1. **Open the app**  
   `http://localhost:8001` (or your deployed URL).

2. **“Run test job now”**  
   Creates a 5s-interval job. In ~5–10 seconds the list shows the job with a **green result line**: the **actual quote** fetched from the API.  
   *“Here you can see the worker didn’t just sleep — it called an external API and we store and display the result.”*

3. **Optional: webhook**  
   Create a job and in “Webhook URL” put a URL from [webhook.site](https://webhook.site) (copy your unique URL). Create the job. When it runs, open webhook.site and show the **real POST body** (job_id, job_name, run_at, etc.).  
   *“For integrations we support webhooks: the worker POSTs to any URL you provide so you can trigger Slack, email, or your own service.”*

4. **One sentence summary**  
   *“It’s a production-style job scheduler: API + worker + Postgres, with row-level locking so multiple workers don’t double-run the same job, crash recovery for stuck RUNNING jobs, and real work — HTTP webhooks and live API data — not just simulated tasks.”*

---

## Technical highlights to mention

- **Concurrency:** `SELECT ... FOR UPDATE SKIP LOCKED` so only one worker claims a given job; multiple workers can run in parallel on different jobs.
- **Crash recovery:** Jobs stuck in `RUNNING` for too long are reset to `SCHEDULED` so another worker can retry.
- **Retries:** Failed runs are retried up to `max_retries`; state is in the DB, so restarts don’t lose jobs.
- **Real I/O:** Worker uses `httpx` for real HTTP (webhook + quote API); results are persisted and shown in the UI.
