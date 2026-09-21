# load-test.ps1 - Generate high-concurrency ticket traffic to test HPA autoscaling
param(
    [int]$DurationSeconds = 45,
    [int]$Concurrency = 8,
    [string]$TargetUrl = "http://localhost:8080/api/v1/predict"
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting High-Concurrency Load Test for HPA             " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Target:     $TargetUrl" -ForegroundColor White
Write-Host "Duration:   $DurationSeconds seconds" -ForegroundColor White
Write-Host "Threads:    $Concurrency concurrent workers" -ForegroundColor White
Write-Host "`nGenerating traffic... (Watch 'kubectl get hpa -w' in another terminal)" -ForegroundColor Yellow

$script = {
    param($url, $endTime)
    $payloads = @(
        '{"ticket_id":"LOAD-1","text":"Critical database connection pool exhausted on worker node 4","customer_id":"CUST-1001","urgency_hint":"Critical"}',
        '{"ticket_id":"LOAD-2","text":"Billed twice for yearly subscription invoice 8891","customer_id":"CUST-1002","urgency_hint":"High"}',
        '{"ticket_id":"LOAD-3","text":"VPN gateway timeout and packet loss during all-hands meeting","customer_id":"CUST-1005","urgency_hint":"Medium"}',
        '{"ticket_id":"LOAD-4","text":"Monitor flickering green and losing display signal on desk 4B","customer_id":"CUST-1005","urgency_hint":"High"}'
    )
    $i = 0
    while ((Get-Date) -lt $endTime) {
        $body = $payloads[$i % $payloads.Count]
        try {
            Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json" -TimeoutSec 2 | Out-Null
        } catch {
            # Ignore timeouts under heavy saturation
        }
        $i++
    }
}

$endTime = (Get-Date).AddSeconds($DurationSeconds)
$jobs = @()
for ($t = 0; $t -lt $Concurrency; $t++) {
    $jobs += Start-Job -ScriptBlock $script -ArgumentList $TargetUrl, $endTime
}

Write-Host "Stress traffic running..." -ForegroundColor Cyan
while ($jobs | Where-Object { $_.State -eq "Running" }) {
    $remaining = [math]::Max(0, [int]($endTime - (Get-Date)).TotalSeconds)
    Write-Host -NoNewline "`rRemaining: $remaining s ...   "
    Start-Sleep -Seconds 2
}

$jobs | Remove-Job -Force
Write-Host "`n`n[Complete] Load test finished! Observe HPA scaling down gracefully." -ForegroundColor Green
