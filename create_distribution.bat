@echo off
echo ===============================================
echo Creating Distribution Package
echo ===============================================
echo.

if not exist "dist\TeamPipingTracker.exe" (
    echo ERROR: TeamPipingTracker.exe not found!
    echo Please run build.bat first to create the executable.
    pause
    exit /b 1
)

echo [1/3] Creating distribution folder...
if exist "TeamPiping_Distribution" rmdir /s /q "TeamPiping_Distribution"
mkdir "TeamPiping_Distribution"

echo [2/3] Copying files...
copy "dist\TeamPipingTracker.exe" "TeamPiping_Distribution\"
xcopy "database" "TeamPiping_Distribution\database\" /E /I /H /Y
if exist "exports" xcopy "exports" "TeamPiping_Distribution\exports\" /E /I /H /Y
if not exist "TeamPiping_Distribution\exports" mkdir "TeamPiping_Distribution\exports"

echo [3/3] Creating README file...
echo Team Piping Tracker - Portable Application > "TeamPiping_Distribution\README.txt"
echo ============================================= >> "TeamPiping_Distribution\README.txt"
echo. >> "TeamPiping_Distribution\README.txt"
echo INSTALLATION: >> "TeamPiping_Distribution\README.txt"
echo 1. Extract all files to a folder on your computer >> "TeamPiping_Distribution\README.txt"
echo 2. Double-click TeamPipingTracker.exe to run >> "TeamPiping_Distribution\README.txt"
echo. >> "TeamPiping_Distribution\README.txt"
echo REQUIREMENTS: >> "TeamPiping_Distribution\README.txt"
echo - Windows 7/8/10/11 (64-bit) >> "TeamPiping_Distribution\README.txt"
echo - No additional software required >> "TeamPiping_Distribution\README.txt"
echo. >> "TeamPiping_Distribution\README.txt"
echo IMPORTANT FILES: >> "TeamPiping_Distribution\README.txt"
echo - TeamPipingTracker.exe: Main application >> "TeamPiping_Distribution\README.txt"
echo - database/: Contains your project data >> "TeamPiping_Distribution\README.txt"
echo - exports/: Folder for exported reports >> "TeamPiping_Distribution\README.txt"
echo. >> "TeamPiping_Distribution\README.txt"
echo BACKUP: >> "TeamPiping_Distribution\README.txt"
echo Always backup your database folder before updates! >> "TeamPiping_Distribution\README.txt"
echo. >> "TeamPiping_Distribution\README.txt"
echo Generated on: %date% %time% >> "TeamPiping_Distribution\README.txt"

echo.
echo ===============================================
echo Distribution package created successfully!
echo ===============================================
echo.
echo Location: TeamPiping_Distribution\
echo.
echo Contents:
dir "TeamPiping_Distribution" /B
echo.
echo You can now zip this folder and distribute it to users.
echo.
pause