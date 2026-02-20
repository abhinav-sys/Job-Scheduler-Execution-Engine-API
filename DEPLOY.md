# Deploy options

You can either:
- **Option A – Full on Railway** (API + Worker on Railway, DB on Neon) — simpler, one platform.
- **Option B – Hybrid** (API on Vercel, Worker on Railway, DB on Neon) — API on Vercel free tier.

---

# Option A: Full deploy on Railway (recommended)

Everything runs on Railway except the database (you keep Neon).

## 1. Neon database

Use your Neon URL with the **async** driver for `DATABASE_URL`:
```text
postgresql+asyncpg://neondb_owner:YOUR_PASSWORD@ep-blue-cake-air88kje-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require
```

## 2. Railway project with two services

1. Go to [railway.app](https://railway.app) → **New Project**.
2. **Deploy from GitHub** → select your repository.
3. You’ll get **one service** (the API). Add the **second** (worker) next.

## 3. Configure the API service

1. Click the **first service** (your repo).
2. **Variables** → add:
   - `DATABASE_URL` = your async Neon URL (above).
3. **Settings** → **Build**:
   - Build Command: `pip install -r requirements.txt` (or leave default if it installs deps).
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   (Railway sets `PORT`; use it so the API listens on the right port.)
4. **Settings** → generate a **domain** (e.g. `your-api.up.railway.app`) so you can call the API.

## 4. Add the Worker service

1. In the same project, click **+ New** → **GitHub Repo** → select the **same** repo again.
2. You now have **two services** from the same repo.
3. Open the **second** service (the worker).
4. **Variables** → add the **same** `DATABASE_URL` (async Neon URL).
5. **Settings** → Start Command: `python -m app.worker.main`
6. No need to expose a domain for the worker; it only talks to the DB.

## 5. Create tables (first time)

Open your API URL (e.g. `https://your-api.up.railway.app/health` or `/docs`). The app runs `init_db()` on startup and creates tables in Neon.

Done. API and worker both run on Railway and use Neon.

---

# Option B: Vercel (API) + Neon (DB) + Railway (Worker)

## 1. Neon database (you have the URL)

Your Neon URL is in this form:
```text
postgresql://USER:PASSWORD@HOST/DB?sslmode=require&channel_binding=require
```

For this project you must use the **async** driver. Set `DATABASE_URL` as:
```text
postgresql+asyncpg://USER:PASSWORD@HOST/DB?sslmode=require
```
Same URL, but change `postgresql://` to `postgresql+asyncpg://`. You can drop `&channel_binding=require` if you want (asyncpg works with `sslmode=require`).

Example (replace with your real values):
```text
postgresql+asyncpg://neondb_owner:YOUR_PASSWORD@ep-blue-cake-air88kje-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require
```

---

## 2. Push code to GitHub

From your project root (e.g. `Job Scheduler & Execution Engine`):

```bash
git init
git add .
git commit -m "Job Scheduler API + Worker + Docker"
git branch -M main
git remote add origin https://github.com/YOUR_ORG/YOUR_REPO.git
git push -u origin main
```

If the repo already has content (e.g. README), you may need to pull first:
```bash
git pull origin main --allow-unrelated-histories
# resolve any conflicts, then
git push -u origin main
```

---

## 3. Deploy API to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in.
2. **Add New** → **Project** → **Import** your repo.
3. **Environment Variables** (before deploying):
   - Name: `DATABASE_URL`
   - Value: your **async** Neon URL (`postgresql+asyncpg://...`).
   - Add for Production (and Preview if you want).
4. **Deploy**.  
   Vercel will use `index.py` as the FastAPI app and `vercel.json` for config.

After deploy you’ll get a URL like:
`https://your-project.vercel.app`

- API base: `https://your-project.vercel.app/api`
- Health: `https://your-project.vercel.app/health`
- Docs: `https://your-project.vercel.app/docs`

---

## 4. Create tables (first time only)

Either:

**Option A – Let the API create them**  
Call the API once (e.g. open `/health` or `/docs`). The app runs `init_db()` on startup and creates tables if they don’t exist.

**Option B – Run Alembic from your machine**  
```bash
# Set DATABASE_URL to your Neon URL (sync: postgresql://... not +asyncpg)
# Then run:
alembic upgrade head
```

---

## 5. Deploy the worker (required for jobs to run)

The **worker cannot run on Vercel** (no long-running processes). Deploy it to **Railway** (or Render / EC2):

1. Go to [railway.app](https://railway.app), sign in, **New Project**.
2. **Deploy from GitHub** → select your repository.
3. **Variables**: add `DATABASE_URL` with the **same** async Neon URL as on Vercel.
4. **Settings** → set **Start Command** to:
   ```text
   python -m app.worker.main
   ```
5. Deploy. Railway will run the worker 24/7; it will poll Neon and execute jobs.

---

## Summary

| Component | Where        | Purpose                          |
|----------|--------------|----------------------------------|
| API      | Vercel       | Create/list jobs, health, docs   |
| DB       | Neon         | Store jobs and executions        |
| Worker   | Railway      | Poll DB, run jobs, retries       |

Use the **same** `DATABASE_URL` (postgresql+asyncpg) for both Vercel and Railway. Never commit the real URL or password; use Vercel/Railway environment variables only.
