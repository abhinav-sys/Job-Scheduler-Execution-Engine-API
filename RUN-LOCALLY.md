# Run locally (before deploy)

1. **Set the database URL**
   - Open `.env` in the project root.
   - Replace `DATABASE_URL` with your real Postgres URL (e.g. from [Neon](https://neon.tech) dashboard).
   - Use the **async** form: `postgresql+asyncpg://USER:PASSWORD@HOST/DB?sslmode=require`.

2. **Start the API**
   - In PowerShell, from the project folder:
   ```powershell
   .\run_local.ps1
   ```
   - Or:
   ```powershell
   $env:PYTHONPATH = (Get-Location).Path
   py -3.9 -m uvicorn app.main:app --host 127.0.0.1 --port 8080
   ```

3. **Check it**
   - Open: http://127.0.0.1:8080/health → should return `{"status":"ok"}`.
   - API docs: http://127.0.0.1:8080/docs.

4. **Optional: run migrations**
   ```powershell
   py -3.9 -m alembic upgrade head
   ```

After it runs locally, you can deploy (e.g. Vercel + Render + Neon) as in `DEPLOY-FREE.md`.
