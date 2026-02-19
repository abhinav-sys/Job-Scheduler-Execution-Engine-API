# Run the API locally (no reload to avoid Windows reloader issues)
# Make sure .env has DATABASE_URL set (e.g. your Neon URL or local Postgres)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONPATH = (Get-Location).Path
py -3.9 -m uvicorn app.main:app --host 127.0.0.1 --port 8080
