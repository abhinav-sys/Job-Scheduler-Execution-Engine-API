# Do these steps to deploy (in order)

## Step 1: Install Fly CLI

**Option A – Windows (winget):**
```powershell
winget install Fly-io.flyctl
```
Close and reopen PowerShell.

**Option B – Windows (PowerShell script):**
```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```
Then add to PATH: `$env:USERPROFILE\.fly\bin`

**Check:** Run `fly version` (or `flyctl version`).

---

## Step 2: Log in to Fly

```powershell
fly auth login
```
A browser will open; sign in with your Fly.io account.

---

## Step 3: Run migrations on Neon (once)

In the project folder, set your Neon URL and run migrations:

```powershell
cd "c:\Users\Aspire7\Desktop\Job Scheduler & Execution Engine"
$env:DATABASE_URL = "postgresql://YOUR_USER:YOUR_PASSWORD@YOUR_NEON_HOST/neondb?sslmode=require"
pip install -r requirements.txt
alembic upgrade head
```

Use the full connection string from the Neon dashboard (Connection string → pooler).

---

## Step 4: Deploy the API to Fly

**Option A – Use the script (easiest):**
```powershell
cd "c:\Users\Aspire7\Desktop\Job Scheduler & Execution Engine"
.\fly-deploy.ps1
```
When it asks for DATABASE_URL, paste your Neon URL.

**Option B – Manual commands:**
```powershell
cd "c:\Users\Aspire7\Desktop\Job Scheduler & Execution Engine"
fly launch --no-deploy --name job-scheduler-api --region ams
# When asked "Postgres database?" → No
fly secrets set DATABASE_URL="postgresql://YOUR_USER:YOUR_PASSWORD@YOUR_NEON_HOST/neondb?sslmode=require"
fly deploy
fly open
```

---

## Step 5: Open the app

After deploy, open: **https://job-scheduler-api.fly.dev/** (or the URL Fly shows).

- `/` = frontend  
- `/docs` = API docs  
- `/health` = health check  

---

## If "fly" is not recognized

- Use full path: `& "$env:USERPROFILE\.fly\bin\flyctl.exe" launch ...`
- Or add to your user PATH: `C:\Users\YOUR_USERNAME\.fly\bin`
