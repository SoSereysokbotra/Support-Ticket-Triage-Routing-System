# cluster-down.ps1 - Teardown local k3d Kubernetes cluster
$ErrorActionPreference = "SilentlyContinue"

$wingetLinks = "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
if (Test-Path $wingetLinks) {
    $env:Path = "$wingetLinks;$env:Path"
}

Write-Host "Tearing down k3d cluster 'ticket-triage-cluster'..." -ForegroundColor Yellow
k3d cluster delete ticket-triage-cluster
Write-Host "[OK] Cluster deleted successfully." -ForegroundColor Green
