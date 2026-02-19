# Deploy in one go (no CLI)

Do this once to get a **public URL** (e.g. `https://job-scheduler-api.onrender.com`).

---

## Option 1: Render (recommended – from browser)

1. **Push this repo to GitHub** (if not already):  
   `abhinav-sys/Job-Scheduler-Execution-Engine-API`

2. Open **https://render.com** and sign in (GitHub is fine).

3. Click **New +** → **Blueprint**.

4. Connect the repo **Job-Scheduler-Execution-Engine-API** (or “Configure account” and select it).

5. Render will read `render.yaml` and show one service: **job-scheduler-api**.  
   Add the required env var:
   - **DATABASE_URL** → paste your **Neon** connection string  
     (e.g. `postgresql://neondb_owner:YOUR_PASSWORD@...-pooler....neon.tech/neondb?sslmode=require`).

6. Click **Apply**.

7. Wait for the first deploy to finish (build + start). Your app will be at:
   - **https://job-scheduler-api.onrender.com** (or the URL Render shows).

8. Open that URL in the browser: you should see the Job Scheduler UI.  
   - `/docs` → API docs  
   - `/health` → health check  

**Note:** On the free tier the service may sleep after inactivity; the first open can take a few seconds to wake.

### If you see "password authentication failed for user 'neondb_owner'"

The **DATABASE_URL** in Render is wrong (usually the password):

1. **Get a fresh connection string** from the [Neon dashboard](https://console.neon.tech): your project → **Connection string** → copy the **pooled** URL (not the direct one).
2. If your password has **special characters** (`@`, `#`, `/`, `%`, `?`, etc.), they must be **URL-encoded** in the connection string:
   - `@` → `%40`
   - `#` → `%23`
   - `/` → `%2F`
   - `%` → `%25`
   - Or in Neon: use **Reset password** and pick a password without special characters, then copy the new URL.
3. In Render: **Dashboard** → your service **job-scheduler-api** → **Environment** → edit **DATABASE_URL** → paste the full URL with **no leading/trailing spaces** → **Save Changes**. Render will redeploy automatically.
4. If you use the **Neon SQL Editor** or another client, test the same URL there to confirm it works.

---

## Option 2: Fly.io (needs Fly CLI)

1. Install: `winget install Fly-io.flyctl` then restart the terminal.
2. Log in: `fly auth login`
3. In the project folder run: `.\fly-deploy.ps1`
4. When asked, paste your **Neon** `DATABASE_URL`.
5. When deploy finishes, run `fly open` or use the URL Fly prints.

---

## Before first deploy (Neon)

Migrations must be run **once** on your Neon DB. If you already ran them (e.g. via Docker earlier), skip this.

From the project folder:

```powershell
$env:DATABASE_URL = "postgresql://YOUR_NEON_URL_HERE"
docker run --rm -e DATABASE_URL="$env:DATABASE_URL" jobschedulerexecutionengine-api:latest alembic upgrade head
```

(Or run `alembic upgrade head` locally with `DATABASE_URL` set.)

After that, use **Option 1** or **Option 2** above; the deployed app will use the same Neon DB.
