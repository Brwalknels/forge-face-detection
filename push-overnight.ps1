# Overnight Docker Push Script for forge-face-detection
# Attempts to push to GitHub Container Registry repeatedly until success
# Press Ctrl+C to stop

param(
    [int]$MaxAttempts = 999,
    [int]$DelaySeconds = 300  # 5 minutes between attempts
)

$ErrorActionPreference = "Continue"
$attempt = 1
$success = $false

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Overnight Docker Push Script" -ForegroundColor Cyan
Write-Host "  (forge-face-detection)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host "Image: ghcr.io/brwalknels/forge-face-detection:latest" -ForegroundColor Yellow
Write-Host "Max Attempts: $MaxAttempts" -ForegroundColor Yellow
Write-Host "Delay Between Attempts: $DelaySeconds seconds" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

while (-not $success -and $attempt -le $MaxAttempts) {
    Write-Host "----------------------------------------" -ForegroundColor Cyan
    Write-Host "Attempt $attempt of $MaxAttempts" -ForegroundColor White
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host "----------------------------------------" -ForegroundColor Cyan
    
    try {
        # Attempt the push
        Write-Host "Pushing image to GitHub Container Registry..." -ForegroundColor Yellow
        $pushOutput = docker push ghcr.io/brwalknels/forge-face-detection:latest 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "  SUCCESS!" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "Completed: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Green
            Write-Host "Total Attempts: $attempt" -ForegroundColor Green
            Write-Host ""
            Write-Host "Push output:" -ForegroundColor Gray
            Write-Host $pushOutput -ForegroundColor Gray
            $success = $true
            
            # Success sound (optional)
            [console]::beep(800, 200)
            [console]::beep(1000, 200)
            [console]::beep(1200, 400)
        } else {
            Write-Host ""
            Write-Host "Push failed with exit code: $LASTEXITCODE" -ForegroundColor Red
            Write-Host ""
            
            # Show last few lines of output for debugging
            $lastLines = $pushOutput | Select-Object -Last 5
            Write-Host "Last 5 lines of output:" -ForegroundColor Gray
            $lastLines | ForEach-Object { Write-Host $_ -ForegroundColor DarkGray }
            
            if ($attempt -lt $MaxAttempts) {
                Write-Host ""
                Write-Host "Waiting $DelaySeconds seconds before retry..." -ForegroundColor Yellow
                Start-Sleep -Seconds $DelaySeconds
            }
            
            $attempt++
        }
    } catch {
        Write-Host ""
        Write-Host "Error during push attempt:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        
        if ($attempt -lt $MaxAttempts) {
            Write-Host ""
            Write-Host "Waiting $DelaySeconds seconds before retry..." -ForegroundColor Yellow
            Start-Sleep -Seconds $DelaySeconds
        }
        
        $attempt++
    }
}

if (-not $success) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  FAILED AFTER $MaxAttempts ATTEMPTS" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Finished: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Red
    Write-Host ""
    Write-Host "Suggestion: Use manual tar file upload instead:" -ForegroundColor Yellow
    Write-Host "  1. docker save ghcr.io/brwalknels/forge-face-detection:latest -o forge-face-detection.tar" -ForegroundColor Gray
    Write-Host "  2. scp forge-face-detection.tar truenas_admin@10.0.0.120:~/" -ForegroundColor Gray
    Write-Host "  3. ssh truenas_admin@10.0.0.120" -ForegroundColor Gray
    Write-Host "  4. sudo docker load -i ~/forge-face-detection.tar" -ForegroundColor Gray
    exit 1
}
