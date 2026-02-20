# Deploy 100% free (no Railway, no payment)

Use these so you don’t pay anything.

**Live jobs (no paid worker):** **(1)** GitHub Actions cron — set `CRON_SECRET` on Render and in GitHub Actions. **(2)** `RUN_WORKER=true` on Render. See [LIVE-DEPLOYMENT.md](LIVE-DEPLOYMENT.md).

**No payment card?** Many cloud workers (Fly, Render, Oracle) can ask for a card. The **simplest option with no card** is to **run the worker on your own PC** (section 5) — free, no sign-up, same Neon DB. Jobs run whenever the worker is running on your machine.

| Part    | Where (free) | Notes |
|---------|----------------|-------|
| **API** | Vercel or Render | Free tier |
| **Worker** | **Your PC** (no card) or Oracle / Fly / Render | Your PC: no card, runs when you run it |
| **DB**  | Neon          | Free tier (you already have it) |

---

## 1. API on Vercel (free)

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project** → import your repository.
2. **Environment Variables** → add:
   - `DATABASE_URL` = your Neon URL with async driver:
   ```text
   postgresql+asyncpg://neondb_owner:YOUR_PASSWORD@ep-blue-cake-air88kje-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
3. **Deploy**.  
   Your API will be at `https://your-project.vercel.app` (e.g. `/api/jobs`, `/docs`, `/health`).

---

## 2. Worker on Render

**If jobs show “SCHEDULED” but stay at “0 run(s)”, the worker is not running.** The API only creates and lists jobs; a separate **Background Worker** process must be running to execute them.

1. Go to [render.com](https://render.com) → Sign in with GitHub.
2. **New +** → **Background Worker**.
3. Connect the same repo as your API.
4. **Environment** → add variable:
   - Key: `DATABASE_URL`  
   - Value: **exactly the same** Neon URL as your API (so the worker sees the same jobs).
5. **Build Command:** `pip install -r requirements.txt`
6. **Start Command:** `python -m app.worker.main`
7. **Create Background Worker**.

Note: Render’s free tier does not include background workers; the worker uses a paid plan (e.g. Starter). For a free worker without a card, use [Oracle Cloud (section 4)](#4-worker-on-oracle-cloud-always-free-no-card-required-in-some-regions).

---

## 3. Worker on Fly.io (free, but asks for a card)

Fly.io gives a free allowance, but **it will ask for a payment method** before creating the app (used for verification; you can stay at $0 if within limits). If you prefer not to add a card, use [Oracle Cloud (section 4)](#4-worker-on-oracle-cloud-always-free-no-card-required-in-some-regions) for the worker instead.

1. Install Fly CLI: [fly.io/docs/hands-on/install-flyctl](https://fly.io/docs/hands-on/install-flyctl/)
2. Log in: `fly auth login`
3. In your project folder (with `fly.worker.toml`):
   ```bash
   fly launch --no-deploy --config fly.worker.toml --no-db --yes --copy-config
   ```
   (Add a card at the billing URL if Fly prompts.)
4. Set your Neon URL:
   ```bash
   fly secrets set DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@HOST/neondb?sslmode=require"
   ```
5. Deploy:
   ```bash
   fly deploy --config fly.worker.toml
   ```

---

## 4. Worker on Oracle Cloud (always-free; may ask for card in some regions)

Oracle’s Always Free tier can give a small VM. **Note:** Oracle may ask for a payment method in some regions even for free tier. If they ask for a card and you don’t have one, use [**Run the worker on your PC** (section 5)](#5-worker-on-your-own-pc-no-card-no-sign-up) instead.

### Step 1: Sign up and create a VM

1. Go to **[oracle.com/cloud/free](https://www.oracle.com/cloud/free/)** and click **Start for free**.
2. Create an Oracle account (email, password, region). Choose a region where **Always Free** is available (e.g. Phoenix, Ashburn, Frankfurt).
3. In the Oracle Cloud Console, open the **hamburger menu** (top left) → **Compute** → **Instances** → **Create instance**.
4. Set:
   - **Name:** e.g. `job-worker`
   - **Placement:** keep default (or pick an Always Free–eligible availability domain).
   - **Image and shape:** Click **Edit** next to “Image and shape”:
     - **Image:** Pick **Ubuntu 22.04** (or 24.04).
     - **Shape:** Click **Change shape** → under “Ampere” select **VM.Standard.A1.Flex** → set **1 OCPU** and **6 GB memory** (within Always Free limits) → **Select shape**.
   - **Add SSH keys:** Either “Generate a key pair for me” (download the private key and keep it safe) or “Upload public key” if you already have one.
5. Click **Create**. Wait until the instance shows **Running** (green). Note its **Public IP address**.

### Step 2: Connect and install

6. From your computer, connect (replace `PRIVATE_KEY_PATH` and `PUBLIC_IP`):

   **Windows (PowerShell):**
   ```powershell
   ssh -i "C:\path\to\your\private-key.key" ubuntu@PUBLIC_IP
   ```

   **Mac/Linux:**
   ```bash
   chmod 600 /path/to/your/private-key.key
   ssh -i /path/to/your/private-key.key ubuntu@PUBLIC_IP
   ```

7. Once logged in, run this on the VM (copy-paste as one block):

   ```bash
   sudo apt update -y
   sudo apt install -y python3 python3-pip python3-venv git
   git clone https://github.com/YOUR_ORG/YOUR_REPO.git
   cd YOUR_REPO
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

### Step 3: Set your Neon URL and run the worker

8. Set the same Neon URL you use for your API (one line, replace with your real URL):

   ```bash
   export DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@HOST/neondb?sslmode=require"
   ```

9. Run the worker (foreground, to test):

   ```bash
   python -m app.worker.main
   ```

   You should see log lines like “Polling…” and “Executing job…”. Leave it running a minute, then check your Render app — job “run(s)” should increase. Press **Ctrl+C** to stop.

### Step 4: Run the worker in the background (keeps running after you disconnect)

10. Install `screen` and start the worker in a session:

    ```bash
    sudo apt install -y screen
    screen -S worker
    export DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@HOST/neondb?sslmode=require"
    python -m app.worker.main
    ```

    Detach from the session: press **Ctrl+A**, then **D**. The worker keeps running. To reattach later: `screen -r worker`.

11. **(Optional)** To run the worker as a service (starts on reboot):

    ```bash
    # Create env file with your Neon URL (run once)
    echo 'DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST/neondb?sslmode=require' | sudo tee /etc/job-worker.env
    sudo chmod 600 /etc/job-worker.env
    # Install and start the service
    sudo bash scripts/oracle-worker-setup.sh install
    # Check status
    sudo systemctl status job-scheduler-worker
    ```

This stays free and doesn’t depend on a platform trial (Oracle may still ask for a card in some regions).

---

## 5. Worker on your own PC (no card, no sign-up)

**No payment card and no cloud VM?** Run the worker on your Windows PC (or Mac/Linux). It uses the **same Neon database** as your API on Render, so jobs you create in the live app will run whenever this worker is running.

1. On your PC, open the project folder (clone the repo if needed):
   ```powershell
   cd "c:\Users\Aspire7\Desktop\Job Scheduler & Execution Engine"
   ```

2. Create a `.env` file in the project root (or set the variable in PowerShell) with the **exact same** Neon URL as your Render API:
   ```text
   DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST/neondb?sslmode=require
   ```

3. Install dependencies if you haven’t:
   ```powershell
   pip install -r requirements.txt
   ```

4. Run the worker:
   ```powershell
   python -m app.worker.main
   ```

   Leave this window open. While it’s running, your live app’s jobs (e.g. on Render) will be picked up and executed. You’ll see log lines like “Polling…” and “Executing job…”. To stop, press **Ctrl+C**.

5. **Optional — run in background:** You can run it in a separate terminal or use `Start-Process` to run it in the background. Jobs will run whenever the worker process is running on your PC.

**Pros:** No card, no cloud sign-up, free. **Cons:** Jobs only run when your PC is on and the worker is running.

---

## Summary (free only)

- **API:** Vercel or Render (free).  
- **Worker:** **Your PC** (no card), or Oracle / Fly.io / Render (may ask for card).  
- **DB:** Neon (free tier).

**No card?** Run the **worker on your own PC** (section 5) — same Neon URL as your API, no sign-up. **OK with adding a card?** Use Fly.io (section 3), Render (section 2), or Oracle (section 4) for an always-on worker.
