# Quick push script for forge-face-detection
# Build and push Docker image to GitHub Container Registry

$ErrorActionPreference = "Stop"

$imageName = "ghcr.io/brwalknels/forge-face-detection:latest"

Write-Host "Building Docker image..." -ForegroundColor Cyan
docker build -t $imageName .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Build successful!" -ForegroundColor Green
Write-Host "`nPushing to GitHub Container Registry..." -ForegroundColor Cyan

docker push $imageName

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Push successful!" -ForegroundColor Green
    Write-Host "`nImage: $imageName" -ForegroundColor Gray
} else {
    Write-Host "`n❌ Push failed!" -ForegroundColor Red
    exit 1
}
