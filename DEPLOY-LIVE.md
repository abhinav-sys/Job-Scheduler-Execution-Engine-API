# Deploy live: Neon + Vercel (API) + Fly.io (Worker)

Use **Neon** for the database, **Vercel** for the API + frontend, and **Fly.io** for the background worker. All have free tiers.

---

## 1. Neon (database) – already have it

You have a Neon DB. Use this URL (with your real password) everywhere below:

- Format:  
  `postgresql://USER:PASSWORD@YOUR-NEON-HOST.aws.neon.tech/neondb?sslmode=require`  
  (copy the full connection string from Neon dashboard; pooler URL is recommended)

The app converts `postgresql://` to `postgresql+asyncpg://` automatically, so you can paste the URL as Neon gives it.

**Run migrations once** (from your machine, with the same URL in env):

```bash
export DATABASE_URL="postgresql://USER:PASSWORD@YOUR-NEON-HOST/neondb?sslmode=require"
cd "Job Scheduler & Execution Engine"
pip install -r requirements.txt
alembic upgrade head
```

---

## 2. Vercel (API + frontend)

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project** → import your repo.
2. **Environment Variables** → add:
   - `DATABASE_URL` = your full Neon URL (the `postgresql://...?sslmode=require` one).
3. **Build Command:** leave default or `pip install -r requirements.txt`.
4. **Output Directory:** leave default.
5. **Deploy.**

The app uses **index.py** at the repo root as the FastAPI entrypoint. After deploy you get:

- `https://your-project.vercel.app/` → frontend
- `https://your-project.vercel.app/api/jobs` → API
- `https://your-project.vercel.app/docs` → Swagger
- `https://your-project.vercel.app/health` → health check

**If you see “application not found” or wrong routes:**  
- Ensure **index.py** exists at the repo root and contains `from app.main import app` and `__all__ = ["app"]`.  
- In **vercel.json**, rewrites should send `/(.*)` to `"/"` (root), not `/api/index`.

---

## 3. Fly.io (API or Worker)

The repo has two Fly configs:
- **fly.toml** → API (for “Launch from GitHub” in the dashboard).
- **fly.worker.toml** → Worker (deploy via CLI).

### Option A: Deploy the API from the Fly dashboard

1. Go to [fly.io/dashboard](https://fly.io/dashboard) → **Launch an App from GitHub**.
2. Select repo **abhinav-sys/Job-Scheduler-Execution-Engine-API**, branch **main**.
3. App name: e.g. **job-scheduler-execution-engine-api** (or leave default).
4. Region: e.g. **ams** (Amsterdam).
5. **Internal port:** **8080** (the Dockerfile uses the `PORT` env).
6. **Add environment variable:**  
   - Key: **DATABASE_URL**  
   - Value: your full Neon URL (`postgresql://...?sslmode=require`).
7. **Database:** leave as “No” (you use Neon).
8. Click to create and deploy.

If you get **“Failed to create app”**: try again; ensure the app name is unique and you’re not over free-tier limits. You can also deploy from the CLI: `fly launch` in the project folder (it will use **fly.toml** for the API).

### Option B: Deploy the Worker via CLI

1. Install Fly CLI: [fly.io/docs/hands-on/install-flyctl](https://fly.io/docs/hands-on/install-flyctl).
2. In the project folder:

   ```bash
   cd "Job Scheduler & Execution Engine"
   fly launch --no-deploy --config fly.worker.toml
   ```
   When asked “Do you want to set up a Postgres database?” choose **No** (you use Neon).

3. Set the Neon URL:

   ```bash
   fly secrets set DATABASE_URL="postgresql://USER:PASSWORD@YOUR-NEON-HOST/neondb?sslmode=require"
   ```

4. Deploy the worker:

   ```bash
   fly deploy --config fly.worker.toml
   ```

5. Check: `fly status` and `fly logs`.

The worker listens on port **8080** for health checks. If you see errors in logs:

- **“connection refused” / “could not connect to server”** → Check `DATABASE_URL` (correct host, password, `?sslmode=require`).  
- **“relation jobs does not exist”** → Run `alembic upgrade head` against Neon (step 1).  
- **“no such table”** → Same: run migrations on Neon.

---

## Quick checklist

| Step | Where | What to do |
|------|--------|------------|
| 1 | Neon | Have DB URL; run `alembic upgrade head` once with `DATABASE_URL` set. |
| 2 | Vercel | Add env `DATABASE_URL` (Neon URL); deploy; open `/` and `/docs`. |
| 3 | Fly.io | `fly launch --no-deploy`, `fly secrets set DATABASE_URL="..."`, `fly deploy --dockerfile Dockerfile.worker`. |

Use the **same** Neon URL (with your password) for: local migrations, Vercel env, and Fly.io secrets.

---

## If something breaks

- **Vercel:** “Application not found” → Use root **index.py** and rewrite to `"/"`. Check [Vercel FastAPI docs](https://vercel.com/docs/frameworks/backend/fastapi).
- **Fly.io:** Crashes or “connection refused” → Run `fly logs`; fix `DATABASE_URL` and/or run migrations on Neon.
- **Neon:** “too many connections” → Use the **pooler** host (e.g. `-pooler` in the hostname); the URL above already uses it.
