# enable-metrics.ps1 - Start k3d cluster and deploy metrics-server for HPA
$ErrorActionPreference = "Stop"

$wingetLinks = "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
if (Test-Path $wingetLinks) {
    $env:Path = "$wingetLinks;$env:Path"
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting Cluster & Enabling Metrics Server               " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Start k3d cluster
Write-Host "`n[1/4] Ensuring k3d cluster is running..." -ForegroundColor Yellow
k3d cluster start ticket-triage-cluster

# 2. Fix kubeconfig server address for Windows
Write-Host "[2/4] Verifying kubeconfig connection..." -ForegroundColor Yellow
$k3dServer = (kubectl config view -o jsonpath="{.clusters[?(@.name=='k3d-ticket-triage-cluster')].cluster.server}")
if ($k3dServer -match "host\.docker\.internal") {
    $fixedServer = $k3dServer -replace "host\.docker\.internal", "127.0.0.1"
    kubectl config set-cluster k3d-ticket-triage-cluster --server=$fixedServer | Out-Null
}

# 3. Deploy metrics-server
Write-Host "[3/4] Deploying metrics-server components..." -ForegroundColor Yellow
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 4. Patch with --kubelet-insecure-tls for local development
Write-Host "[4/4] Configuring --kubelet-insecure-tls and waiting for rollout..." -ForegroundColor Yellow
try {
    kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]' 2>$null
} catch {
    Write-Host "Patch already applied or pending..." -ForegroundColor DarkGray
}

kubectl rollout status deployment metrics-server -n kube-system --timeout=120s

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  Metrics Server Active!                                  " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Test top commands:" -ForegroundColor Cyan
Write-Host "  kubectl top nodes" -ForegroundColor White
Write-Host "  kubectl top pods" -ForegroundColor White
