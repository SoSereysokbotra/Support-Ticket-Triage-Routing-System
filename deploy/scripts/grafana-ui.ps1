# grafana-ui.ps1 - Forward port and open Grafana Dashboard
$wingetLinks = "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
if (Test-Path $wingetLinks) {
    $env:Path = "$wingetLinks;$env:Path"
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Launching Grafana Observability Dashboard               " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

Write-Host "`nGrafana Observability Credentials:" -ForegroundColor Yellow
Write-Host "  URL:      http://localhost:3000" -ForegroundColor White
Write-Host "  Auth:     Anonymous Admin enabled (No password required)" -ForegroundColor Green
Write-Host "`nStarting port-forward on port 3000 (Press Ctrl+C to stop)...`n" -ForegroundColor DarkGray

Start-Process "http://localhost:3000/d/ticket-triage-mlops"

kubectl port-forward svc/ticket-triage-grafana 3000:3000
