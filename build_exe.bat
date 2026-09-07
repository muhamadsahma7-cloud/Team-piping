@echo off
echo Building Team Piping Application...
echo.

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "main.spec" del "main.spec"

echo Installing/upgrading PyInstaller...
pip install --upgrade pyinstaller

echo.
echo Building executable...
pyinstaller --onefile ^
    --windowed ^
    --name "TeamPiping" ^
    --icon="MIE.png" ^
    --add-data "MIE.png;." ^
    --add-data "NAEC logo.jpg;." ^
    --add-data "database;database" ^
    --add-data "report template;report template" ^
    --add-data "QC Report template;QC Report template" ^
    --add-data "master file;master file" ^
    --hidden-import "tkinter" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL.Image" ^
    --hidden-import "PIL.ImageTk" ^
    --hidden-import "sqlite3" ^
    --hidden-import "pandas" ^
    --hidden-import "openpyxl" ^
    --hidden-import "pytz" ^
    --hidden-import "tkcalendar" ^
    main.py

if %errorlevel% equ 0 (
    echo.
    echo Build completed successfully!
    echo Executable created: dist\TeamPiping.exe
    echo.
    
    REM Copy additional files to dist folder
    echo Copying additional files...
    if not exist "dist\database" mkdir "dist\database"
    if not exist "dist\report template" mkdir "dist\report template"
    if not exist "dist\QC Report template" mkdir "dist\QC Report template"
    if not exist "dist\master file" mkdir "dist\master file"
    
    copy "database\*.db" "dist\database\" 2>nul
    copy "report template\*.xlsx" "dist\report template\" 2>nul
    copy "QC Report template\*.xlsx" "dist\QC Report template\" 2>nul
    copy "master file\*.xlsx" "dist\master file\" 2>nul
    copy "master file\*.xlsm" "dist\master file\" 2>nul
    copy "MIE.png" "dist\" 2>nul
    copy "NAEC logo.jpg" "dist\" 2>nul
    
    echo.
    echo All files copied successfully!
    echo Ready to distribute: dist\TeamPiping.exe
) else (
    echo.
    echo Build failed! Check the error messages above.
)

pause