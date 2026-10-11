# JARVIS safe updater for Windows PowerShell.
# Run from the cloned repository: .\scripts\update.ps1
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host ""
Write-Host " J.A.R.V.I.S. UPDATE" -ForegroundColor Cyan
Write-Host " Repository: $RepoRoot"
Write-Host ""

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git was not found. Install Git for Windows and reopen PowerShell."
}
if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    throw "This folder is not a Git clone. Re-clone the repository before using the updater."
}

$branch = (& git branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or $branch -ne "main") {
    throw "Updater expects the main branch; current branch is '$branch'. Switch to main and retry."
}
$changes = & git status --porcelain
if ($LASTEXITCODE -ne 0) { throw "Could not inspect Git working tree." }
if ($changes) {
    Write-Host "Local changes were found:" -ForegroundColor Yellow
    $changes | ForEach-Object { Write-Host "  $_" }
    throw "Update stopped to protect local edits. Commit or back up your changes, then retry."
}

Write-Host "Checking GitHub for updates..." -ForegroundColor Cyan
& git fetch origin main
if ($LASTEXITCODE -ne 0) { throw "Git fetch failed. Check network access and the origin remote." }

$local = (& git rev-parse HEAD).Trim()
$remote = (& git rev-parse origin/main).Trim()
if ($local -eq $remote) {
    Write-Host "JARVIS is already up to date." -ForegroundColor Green
} else {
    & git merge --ff-only origin/main
    if ($LASTEXITCODE -ne 0) { throw "Fast-forward update failed. No automatic reset was performed." }
    Write-Host "Source code updated. Restart JARVIS to load the new version." -ForegroundColor Green
}

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if ($Python) {
    Write-Host "Refreshing dependencies..." -ForegroundColor Cyan
    & $Python -m pip install -r (Join-Path $RepoRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed. Review pip output above." }
} else {
    Write-Host "Python not found; skipped dependency refresh." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Update process finished. Restart JARVIS before using the updated code." -ForegroundColor Cyan
