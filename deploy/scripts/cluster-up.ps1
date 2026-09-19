# cluster-up.ps1 - Initialize local k3d Kubernetes cluster
$ErrorActionPreference = "Stop"

$wingetLinks = "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
if (Test-Path $wingetLinks) {
    $env:Path = "$wingetLinks;$env:Path"
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Phase B: Initializing Local k3d Kubernetes Cluster       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify Docker
try {
    docker info | Out-Null
    Write-Host "[OK] Docker daemon is running." -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker Desktop is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# 2. Check if cluster already exists
$clusterExists = k3d cluster list -o json | ConvertFrom-Json | Where-Object { $_.name -eq "ticket-triage-cluster" }

if ($clusterExists) {
    Write-Host "[INFO] Cluster 'ticket-triage-cluster' already exists. Starting it if stopped..." -ForegroundColor Yellow
    k3d cluster start ticket-triage-cluster
} else {
    Write-Host "[INFO] Creating k3d cluster 'ticket-triage-cluster' with Traefik Ingress on port 8080..." -ForegroundColor Yellow
    # Map host port 8080 to k3s load balancer port 80
    k3d cluster create ticket-triage-cluster `
        --port "8080:80@loadbalancer" `
        --agents 1 `
        --k3s-arg "--disable=metrics-server@server:0" `
        --wait
}

# 3. Ensure Windows localhost endpoint is mapped in kubeconfig
$k3dServer = (kubectl config view -o jsonpath="{.clusters[?(@.name=='k3d-ticket-triage-cluster')].cluster.server}")
if ($k3dServer -match "host\.docker\.internal") {
    $fixedServer = $k3dServer -replace "host\.docker\.internal", "127.0.0.1"
    kubectl config set-cluster k3d-ticket-triage-cluster --server=$fixedServer | Out-Null
}

Write-Host "[OK] Cluster is ready!" -ForegroundColor Green
kubectl cluster-info
Write-Host ""
Write-Host "Next step: run .\deploy\scripts\deploy.ps1 to build images and deploy the Helm chart." -ForegroundColor Cyan
