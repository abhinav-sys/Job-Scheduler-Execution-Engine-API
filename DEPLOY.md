# Deploy: Vercel (API) + Neon (DB) + Railway (Worker)

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
git remote add origin https://github.com/abhinav-sys/Job-Scheduler-Execution-Engine-API.git
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
2. **Add New** → **Project** → **Import** your repo: `abhinav-sys/Job-Scheduler-Execution-Engine-API`.
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
2. **Deploy from GitHub** → select `Job-Scheduler-Execution-Engine-API`.
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
