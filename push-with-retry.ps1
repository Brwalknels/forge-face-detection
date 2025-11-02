# Docker push with automatic retry for forge-face-detection
# Retries up to 20 times with 5 second delay between attempts

param(
    [int]$MaxRetries = 20,
    [int]$DelaySeconds = 5
)

$imageName = "ghcr.io/brwalknels/forge-face-detection:latest"
$attempt = 1

Write-Host "Pushing $imageName with up to $MaxRetries retries..." -ForegroundColor Cyan

while ($attempt -le $MaxRetries) {
    Write-Host "`nAttempt $attempt of $MaxRetries..." -ForegroundColor Yellow
    
    docker push $imageName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Push successful!" -ForegroundColor Green
        exit 0
    }
    
    if ($attempt -lt $MaxRetries) {
        Write-Host "Push failed. Retrying in $DelaySeconds seconds..." -ForegroundColor Red
        Start-Sleep -Seconds $DelaySeconds
    }
    
    $attempt++
}

Write-Host "`n❌ Push failed after $MaxRetries attempts" -ForegroundColor Red
exit 1
