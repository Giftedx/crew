#!/usr/bin/env pwsh
# Move Docker to F Drive - Run in PowerShell as Administrator

Write-Host "🐳 Moving Docker Desktop to F Drive..." -ForegroundColor Cyan

# Step 1: Stop Docker Desktop
Write-Host "`n1️⃣ Stopping Docker Desktop..." -ForegroundColor Yellow
Get-Process "Docker Desktop" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

# Step 2: Shutdown WSL
Write-Host "`n2️⃣ Shutting down WSL..." -ForegroundColor Yellow
wsl --shutdown
Start-Sleep -Seconds 2

# Step 3: Create F drive directories
Write-Host "`n3️⃣ Creating F:\Docker directories..." -ForegroundColor Yellow
New-Item -Path "F:\Docker" -ItemType Directory -Force | Out-Null
New-Item -Path "F:\Docker\wsl" -ItemType Directory -Force | Out-Null
New-Item -Path "F:\Docker\wsl\distro" -ItemType Directory -Force | Out-Null

# Step 4: Export Docker distros
Write-Host "`n4️⃣ Exporting docker-desktop (this may take a few minutes)..." -ForegroundColor Yellow
wsl --export docker-desktop "F:\Docker\wsl\docker-desktop.tar"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to export docker-desktop" -ForegroundColor Red
    exit 1
}

Write-Host "`n   Exporting docker-desktop-data (this may take several minutes)..." -ForegroundColor Yellow
wsl --export docker-desktop-data "F:\Docker\wsl\docker-desktop-data.tar"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to export docker-desktop-data" -ForegroundColor Red
    exit 1
}

# Step 5: Unregister old distros
Write-Host "`n5️⃣ Unregistering old Docker distros..." -ForegroundColor Yellow
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data

# Step 6: Import to F drive
Write-Host "`n6️⃣ Importing docker-desktop to F drive..." -ForegroundColor Yellow
wsl --import docker-desktop "F:\Docker\wsl\distro\docker-desktop" "F:\Docker\wsl\docker-desktop.tar" --version 2
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to import docker-desktop" -ForegroundColor Red
    exit 1
}

Write-Host "`n   Importing docker-desktop-data to F drive..." -ForegroundColor Yellow
wsl --import docker-desktop-data "F:\Docker\wsl\distro\docker-desktop-data" "F:\Docker\wsl\docker-desktop-data.tar" --version 2
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to import docker-desktop-data" -ForegroundColor Red
    exit 1
}

# Step 7: Update Docker settings
Write-Host "`n7️⃣ Updating Docker Desktop settings..." -ForegroundColor Yellow
$dockerConfigPath = "$env:APPDATA\Docker"
New-Item -Path $dockerConfigPath -ItemType Directory -Force | Out-Null

$settingsPath = "$dockerConfigPath\settings.json"
if (Test-Path $settingsPath) {
    Copy-Item $settingsPath "$settingsPath.backup" -Force
    Write-Host "   Backed up existing settings to settings.json.backup" -ForegroundColor Gray
}

$settings = @"
{
  "dataFolder": "F:\\Docker\\data",
  "wslEngineEnabled": true
}
"@
$settings | Out-File -FilePath $settingsPath -Encoding utf8

# Step 8: Start Docker Desktop
Write-Host "`n8️⃣ Starting Docker Desktop..." -ForegroundColor Yellow
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

Write-Host "`n✅ Migration complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Wait for Docker Desktop to start fully (check system tray)" -ForegroundColor White
Write-Host "  2. Go to Settings → Resources → Advanced" -ForegroundColor White
Write-Host "  3. Verify 'Disk image location' shows F drive path" -ForegroundColor White
Write-Host "  4. From WSL, run: docker info | grep 'Docker Root Dir'" -ForegroundColor White
Write-Host "`n  5. After verification, clean up with:" -ForegroundColor White
Write-Host "     Remove-Item 'F:\Docker\wsl\docker-desktop.tar'" -ForegroundColor Gray
Write-Host "     Remove-Item 'F:\Docker\wsl\docker-desktop-data.tar'" -ForegroundColor Gray
Write-Host "`n🎯 Your Docker data is now on F drive with 1.4TB available!" -ForegroundColor Green
