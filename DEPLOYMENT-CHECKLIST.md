# Deployment checklist

Use this after the project runs locally.

---

## 1. Run locally (done)

- **Docker:** `docker-compose up --build -d`
- **API:** http://localhost:8001/health → `{"status":"ok"}`
- **Docs:** http://localhost:8001/docs

If you need port 8000 instead of 8001, edit `docker-compose.yml`: set `ports` to `"8000:8000"` for the `api` service.

---

## 2. Deploy (free tier)

| Component | Where | Action |
|-----------|--------|--------|
| **Database** | [Neon](https://neon.tech) | Create project → copy connection URL → use **async** form: `postgresql+asyncpg://USER:PASSWORD@HOST/DB?sslmode=require` |
| **API** | [Vercel](https://vercel.com) | Import repo → add env `DATABASE_URL` (Neon async URL) → Deploy. API entry: `api/index.py` (see `vercel.json`). |
| **Worker** | [Render](https://render.com) or [Fly.io](https://fly.io) | Same `DATABASE_URL`. **Render:** Background Worker, build `pip install -r requirements.txt`, start `python -m app.worker.main`. **Fly:** `fly deploy --dockerfile Dockerfile.worker` after `fly secrets set DATABASE_URL=...`. |

Details: **[DEPLOY-FREE.md](DEPLOY-FREE.md)** (Vercel + Render/Fly/Oracle, no payment).

---

## 3. After deploy

- **API base URL:** `https://your-project.vercel.app` (or your custom domain)
- **Endpoints:** `/health`, `/api/jobs`, `/docs`
- Worker runs in the background on Render/Fly; no extra URL.

---

## Optional: run API locally without Docker

1. Create `.env` with `DATABASE_URL` (e.g. Neon async URL or `postgresql+asyncpg://postgres:postgres@localhost:5432/job_scheduler` if Postgres is local).
2. `.\run_local.ps1` (or `py -3.9 -m uvicorn app.main:app --host 127.0.0.1 --port 8080`).
3. Open http://127.0.0.1:8080/health and http://127.0.0.1:8080/docs.

See **[RUN-LOCALLY.md](RUN-LOCALLY.md)**.
