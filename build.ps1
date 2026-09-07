# Team Piping Tracker - PowerShell Build Script

Write-Host "===============================================" -ForegroundColor Green
Write-Host "Team Piping Tracker - Build Script" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

try {
    Write-Host "[1/4] Installing/Upgrading required packages..." -ForegroundColor Yellow
    & python -m pip install --upgrade pip
    & pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Failed to install dependencies" }

    Write-Host ""
    Write-Host "[2/4] Cleaning previous build..." -ForegroundColor Yellow
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "__pycache__") { Remove-Item -Recurse -Force "__pycache__" }
    if (Test-Path "tabs/__pycache__") { Remove-Item -Recurse -Force "tabs/__pycache__" }

    Write-Host ""
    Write-Host "[3/4] Creating directories if they don't exist..." -ForegroundColor Yellow
    if (!(Test-Path "database")) { New-Item -ItemType Directory -Path "database" }
    if (!(Test-Path "exports")) { New-Item -ItemType Directory -Path "exports" }
    if (!(Test-Path "database/backups")) { New-Item -ItemType Directory -Path "database/backups" }

    Write-Host ""
    Write-Host "[4/4] Building executable with PyInstaller..." -ForegroundColor Yellow
    & pyinstaller --clean --onefile team_piping.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }

    Write-Host ""
    if (Test-Path "dist/TeamPipingTracker.exe") {
        Write-Host "===============================================" -ForegroundColor Green
        Write-Host "SUCCESS! Build completed successfully!" -ForegroundColor Green
        Write-Host "===============================================" -ForegroundColor Green
        Write-Host ""
        
        $fileSize = (Get-Item "dist/TeamPipingTracker.exe").Length
        $fileSizeMB = [math]::Round($fileSize / 1MB, 2)
        
        Write-Host "Executable created at: dist/TeamPipingTracker.exe" -ForegroundColor Cyan
        Write-Host "File size: $fileSizeMB MB" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "You can now run the application by double-clicking:" -ForegroundColor White
        Write-Host "dist/TeamPipingTracker.exe" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Note: Make sure to copy the 'database' folder to the same" -ForegroundColor Magenta
        Write-Host "directory as the executable when distributing." -ForegroundColor Magenta
    } else {
        throw "Executable not found after build"
    }

} catch {
    Write-Host ""
    Write-Host "===============================================" -ForegroundColor Red
    Write-Host "ERROR: Build failed!" -ForegroundColor Red
    Write-Host "===============================================" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "1. Missing dependencies - install with: pip install -r requirements.txt" -ForegroundColor White
    Write-Host "2. Python path issues - ensure Python is in PATH" -ForegroundColor White
    Write-Host "3. Permission issues - run as administrator" -ForegroundColor White
    Write-Host "4. PyInstaller not installed - run: pip install pyinstaller" -ForegroundColor White
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")