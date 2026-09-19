# argocd-ui.ps1 - Forward port and open ArgoCD Dashboard
$wingetLinks = "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
if (Test-Path $wingetLinks) {
    $env:Path = "$wingetLinks;$env:Path"
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Launching ArgoCD Web Dashboard                          " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Fetch password
$rawPassword = kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" 2>$null
if ($rawPassword) {
    $adminPassword = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($rawPassword))
} else {
    $adminPassword = "(Check: kubectl get secret argocd-initial-admin-secret -n argocd)"
}

Write-Host "`nArgoCD Dashboard Credentials:" -ForegroundColor Yellow
Write-Host "  URL:      http://localhost:8081" -ForegroundColor White
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: $adminPassword" -ForegroundColor Green
Write-Host "`nStarting port-forward on port 8081 (Press Ctrl+C to stop)...`n" -ForegroundColor DarkGray

Start-Process "http://localhost:8081"

kubectl port-forward svc/argocd-server -n argocd 8081:80
