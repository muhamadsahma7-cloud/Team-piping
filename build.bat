@echo off
echo ===============================================
echo Team Piping Tracker - Build Script
echo ===============================================
echo.

echo [1/4] Installing/Upgrading required packages...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [2/4] Cleaning previous build...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"
for /d %%d in (tabs\__pycache__) do if exist "%%d" rmdir /s /q "%%d"

echo.
echo [3/4] Creating directories if they don't exist...
if not exist "database" mkdir "database"
if not exist "exports" mkdir "exports"
if not exist "database\backups" mkdir "database\backups"

echo.
echo [4/4] Building executable with PyInstaller...
pyinstaller --clean --onefile team_piping.spec

echo.
if exist "dist\TeamPipingTracker.exe" (
    echo ===============================================
    echo SUCCESS! Build completed successfully!
    echo ===============================================
    echo.
    echo Executable created at: dist\TeamPipingTracker.exe
    echo File size: 
    dir "dist\TeamPipingTracker.exe" /B /-C | findstr TeamPipingTracker.exe
    echo.
    echo You can now run the application by double-clicking:
    echo dist\TeamPipingTracker.exe
    echo.
    echo Note: Make sure to copy the 'database' folder to the same
    echo directory as the executable when distributing.
) else (
    echo ===============================================
    echo ERROR: Build failed!
    echo ===============================================
    echo Check the output above for error messages.
    echo Common issues:
    echo 1. Missing dependencies - install with: pip install -r requirements.txt
    echo 2. Python path issues - ensure Python is in PATH
    echo 3. Permission issues - run as administrator
)

echo.
pause