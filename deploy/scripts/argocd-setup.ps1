# argocd-setup.ps1 - Install and Configure ArgoCD in k3d
$ErrorActionPreference = "Stop"

$wingetLinks = "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
if (Test-Path $wingetLinks) {
    $env:Path = "$wingetLinks;$env:Path"
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Phase C: Setting up ArgoCD GitOps Engine                 " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Create namespace
Write-Host "`n[1/5] Creating 'argocd' namespace..." -ForegroundColor Yellow
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# 2. Install ArgoCD
Write-Host "[2/5] Applying ArgoCD official manifests..." -ForegroundColor Yellow
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 3. Patch argocd-server to run in --insecure mode for local HTTP access
Write-Host "[3/5] Configuring argocd-server for local development (--insecure)..." -ForegroundColor Yellow
try {
    kubectl patch deployment argocd-server -n argocd --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--insecure"}]' 2>$null
} catch {
    Write-Host "Patch already applied or pending..." -ForegroundColor DarkGray
}

# 4. Wait for core components to be Ready
Write-Host "[4/5] Waiting for ArgoCD controllers to be ready..." -ForegroundColor Yellow
kubectl rollout status deployment argocd-repo-server -n argocd --timeout=180s
kubectl rollout status statefulset argocd-application-controller -n argocd --timeout=180s
kubectl rollout status deployment argocd-server -n argocd --timeout=180s

# 5. Apply the GitOps Application
Write-Host "[5/5] Registering 'ticket-triage' Application in ArgoCD..." -ForegroundColor Yellow
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$appYaml = Join-Path $scriptDir "..\argocd\application.yaml"
kubectl apply -f $appYaml

# Fetch initial admin password
Write-Host "`nRetrieving ArgoCD initial admin credentials..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
$rawPassword = kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" 2>$null
if ($rawPassword) {
    $adminPassword = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($rawPassword))
} else {
    $adminPassword = "(Secret already rotated or not yet generated. Check 'kubectl get secrets -n argocd')"
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  ArgoCD Installation Complete!                          " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "ArgoCD Access Credentials:" -ForegroundColor Cyan
Write-Host "  URL:      http://localhost:8081" -ForegroundColor White
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: $adminPassword" -ForegroundColor Green
Write-Host ""
Write-Host "To launch the dashboard, run: .\deploy\scripts\argocd-ui.ps1" -ForegroundColor Yellow
Write-Host "To monitor sync status, run:   kubectl get application ticket-triage -n argocd" -ForegroundColor Yellow
