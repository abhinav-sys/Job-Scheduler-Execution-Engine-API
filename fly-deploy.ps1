# Deploy API to Fly.io - run from project root.
# 1. Install Fly CLI first: https://fly.io/docs/flyctl/install/ (or: winget install Fly-io.flyctl)
# 2. Run: .\fly-deploy.ps1
# 3. When asked for DATABASE_URL, paste your Neon URL (postgresql://...?sslmode=require)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Check fly is available
$fly = Get-Command fly -ErrorAction SilentlyContinue
if (-not $fly) {
    $fly = Get-Command flyctl -ErrorAction SilentlyContinue
}
if (-not $fly) {
    Write-Host "Fly CLI not found. Install it first:"
    Write-Host "  winget install Fly-io.flyctl"
    Write-Host "  Or: https://fly.io/docs/flyctl/install/"
    exit 1
}

Write-Host "Using: $($fly.Source)"
fly version

# Login if needed
Write-Host "`n--- Checking Fly login ---"
fly auth whoami 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Log in to Fly (browser will open)..."
    fly auth login
}

# Launch app (no deploy yet). When asked "Postgres database?" answer No.
Write-Host "`n--- Creating app (no deploy) ---"
Write-Host "If prompted 'Would you like to set up a Postgres database?' choose No (you use Neon)."
fly launch --no-deploy --name job-scheduler-api --region ams

# Set DATABASE_URL
Write-Host "`n--- Set DATABASE_URL (your Neon URL) ---"
$url = Read-Host "Paste your Neon DATABASE_URL (postgresql://...?sslmode=require)"
if ($url) {
    fly secrets set "DATABASE_URL=$url"
}

# Deploy
Write-Host "`n--- Deploying ---"
fly deploy

Write-Host "`n--- Done. Open your app: ---"
fly open
