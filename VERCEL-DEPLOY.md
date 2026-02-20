# Fix: Vercel keeps building old commit (5225eba)

If your build log shows **Commit: 5225eba** instead of the latest, Vercel is not using the newest code.

## Do this first

### 1. Connect GitHub (if not already)

1. Vercel dashboard → your project → **Settings** → **Git**.
2. Under **Connected Git Repository**, it should show your connected repository.
3. If it says **No Git Repository** or a different repo:
   - Click **Connect Git Repository**.
   - Choose **GitHub** → select your repository.
   - **Production Branch**: set to **main** → Save.

### 2. Deploy the latest commit

**Option A – From the Deployments tab**

1. Go to **Deployments**.
2. Click the **three dots (⋯)** on the **top** deployment (latest).
3. Click **Redeploy**.
4. **Important:** Leave **“Use existing Build Cache”** **unchecked** (or turn it off).
5. Click **Redeploy** so it uses the latest commit from **main**.

**Option B – From your computer (uses your local code)**

1. Install Vercel CLI: `npm i -g vercel`
2. In the project folder:
   ```bash
   cd "Job Scheduler & Execution Engine"
   vercel --prod
   ```
3. Log in if asked and link to your existing project when prompted.  
   This deploys your **current local files** (including the fixed `vercel.json`).

After this, the build should use the latest commit and the runtime error should be gone.
