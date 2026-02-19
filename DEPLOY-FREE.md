# Deploy 100% free (no Railway, no payment)

Use these so you don’t pay anything:

| Part    | Where (free) | Notes |
|---------|----------------|-------|
| **API** | Vercel        | Free tier, serverless |
| **Worker** | Render or Fly.io | Free tier for one worker |
| **DB**  | Neon          | Free tier (you already have it) |

---

## 1. API on Vercel (free)

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project** → import `abhinav-sys/Job-Scheduler-Execution-Engine-API`.
2. **Environment Variables** → add:
   - `DATABASE_URL` = your Neon URL with async driver:
   ```text
   postgresql+asyncpg://neondb_owner:YOUR_PASSWORD@ep-blue-cake-air88kje-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
3. **Deploy**.  
   Your API will be at `https://your-project.vercel.app` (e.g. `/api/jobs`, `/docs`, `/health`).

---

## 2. Worker on Render (free)

Render’s free tier can run one **Background Worker** (no credit card on free tier in many regions).

1. Go to [render.com](https://render.com) → Sign in with GitHub.
2. **New +** → **Background Worker**.
3. Connect repo: `abhinav-sys/Job-Scheduler-Execution-Engine-API`.
4. **Environment** → add variable:
   - Key: `DATABASE_URL`  
   - Value: same async Neon URL as above.
5. **Build Command:** `pip install -r requirements.txt`
6. **Start Command:** `python -m app.worker.main`
7. **Instance Type:** leave **Free** (if available).
8. **Create Background Worker**.

Limitation: free tier may spin down after some inactivity; when it’s up, jobs will run. For “always on” without paying, use Fly.io or Oracle below.

---

## 3. Worker on Fly.io (free)

Fly.io has a free allowance. The repo includes `fly.toml` and `Dockerfile.worker` for the worker.

1. Install Fly CLI: [fly.io/docs/hands-on/install-flyctl](https://fly.io/docs/hands-on/install-flyctl/)
2. In your project folder:
   ```bash
   fly launch --no-deploy
   ```
   Say **no** to Postgres (you use Neon).
3. Set your Neon URL (use the async one):
   ```bash
   fly secrets set DATABASE_URL="postgresql+asyncpg://neondb_owner:YOUR_PASSWORD@ep-blue-cake-air88kje-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"
   ```
4. Deploy the worker (uses `Dockerfile.worker`):
   ```bash
   fly deploy --dockerfile Dockerfile.worker
   ```

The worker will run on Fly’s free tier. If Fly asks for a card, it’s for verification; stay within free limits.

---

## 4. Worker on Oracle Cloud (always-free, no card required in some regions)

Oracle gives always-free VMs. You run the worker yourself (no trial expiry).

1. Sign up: [oracle.com/cloud/free](https://www.oracle.com/cloud/free/).
2. Create an **Always Free** VM (e.g. Ubuntu).
3. SSH into the VM and install Python 3.11+, git, and clone your repo (or copy the `app/` folder and `requirements.txt`).
4. Set env:
   ```bash
   export DATABASE_URL="postgresql+asyncpg://..."
   ```
5. Run in background (e.g. with `screen` or `systemd`):
   ```bash
   pip install -r requirements.txt
   screen -S worker
   python -m app.worker.main
   # Ctrl+A then D to detach
   ```

This stays free and doesn’t depend on a platform trial.

---

## Summary (free only)

- **API:** Vercel (free).  
- **Worker:** Render (free tier) or Fly.io (free allowance) or Oracle (always-free VM).  
- **DB:** Neon (free tier).

No Railway, no payment. Start with **Vercel + Render**; if Render free worker isn’t available in your region, use **Fly.io** or **Oracle** for the worker.
