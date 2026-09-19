# deploy.ps1 - Build, Import Images, and Deploy Helm Chart
$ErrorActionPreference = "Stop"

$wingetLinks = "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
if (Test-Path $wingetLinks) {
    $env:Path = "$wingetLinks;$env:Path"
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Phase B: Building Images & Deploying Helm Release        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $projectRoot

# 1. Build backend Docker image
Write-Host "[1/4] Building backend Docker image: ticket-triage:latest..." -ForegroundColor Yellow
docker build -t ticket-triage:latest -f Dockerfile .

# 2. Build frontend Docker image
Write-Host "[2/4] Building frontend Docker image: ticket-triage-frontend:latest..." -ForegroundColor Yellow
docker build -t ticket-triage-frontend:latest -f frontend/Dockerfile ./frontend

# 3. Import images into k3d cluster
Write-Host "[3/4] Importing local images into k3d cluster..." -ForegroundColor Yellow
k3d image import ticket-triage:latest ticket-triage-frontend:latest -c ticket-triage-cluster

# 4. Deploy or Upgrade with Helm
Write-Host "[4/4] Deploying Helm release 'ticket-triage'..." -ForegroundColor Yellow
helm upgrade --install ticket-triage ./deploy/helm/ticket-triage `
    --namespace default `
    --wait `
    --timeout 5m

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Deployment Complete!                                    " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Services available at:" -ForegroundColor Cyan
Write-Host "  • Triage Portal (Frontend): http://localhost:8080" -ForegroundColor White
Write-Host "  • FastAPI Health Endpoint:  http://localhost:8080/api/v1/health" -ForegroundColor White
Write-Host "  • Swagger Documentation:    http://localhost:8080/api/docs" -ForegroundColor White
Write-Host ""
Write-Host "Check cluster pods with: kubectl get pods -l app.kubernetes.io/name=ticket-triage" -ForegroundColor Yellow
