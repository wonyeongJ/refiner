@echo off
setlocal
:: Change directory to project root (parent folder of scripts/)
cd /d "%~dp0.."

set "APP_NAME=Refiner"
set "APP_VERSION=1.0.0-stable"
set "EXE_NAME=%APP_NAME%.exe"
set "DIST_DIR=dist"
set "PACKAGE_DIR=%DIST_DIR%\%APP_NAME%_package"
set "ZIP_PATH=%DIST_DIR%\%APP_NAME%_v%APP_VERSION%.zip"

echo.
echo ========================================================
echo   Refiner Build Script
echo ========================================================
echo.
echo [1/4] Cleaning previous build files...
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist Refiner.spec del /f /q Refiner.spec

echo.
echo [2/4] Building %EXE_NAME% with PyInstaller...
echo Icon Path: assets\images\icon.ico
:: Bundling assets, core, and ui folders into the executable
pyinstaller --noconsole --onefile ^
    --icon="assets/images/icon.ico" ^
    --add-data "assets;assets" ^
    --add-data "core;core" ^
    --add-data "ui;ui" ^
    --name "%APP_NAME%" ^
    main.py

echo.
echo [3/4] Creating distribution package folder...
if exist "%PACKAGE_DIR%" rd /s /q "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%"

copy /y "%DIST_DIR%\%EXE_NAME%" "%PACKAGE_DIR%\%EXE_NAME%" >nul

:: Keep icon with package as an optional external asset fallback.
if not exist "%PACKAGE_DIR%\assets\images" mkdir "%PACKAGE_DIR%\assets\images"
copy /y "assets\images\icon.ico" "%PACKAGE_DIR%\assets\images\icon.ico" >nul

(
echo Refiner Distribution Package
echo.
echo 1. Run %EXE_NAME%
echo 2. If SmartScreen warns, choose "More info" ^> "Run anyway".
echo.
echo Note:
echo - Required runtime resources are already bundled in the executable.
echo - assets\images\icon.ico is included as an optional fallback resource.
) > "%PACKAGE_DIR%\README_DIST.txt"

echo.
echo [4/4] Creating ZIP file...
if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"
powershell -NoProfile -Command "Compress-Archive -Path '%PACKAGE_DIR%\*' -DestinationPath '%ZIP_PATH%' -Force"

echo.
echo Build Completed!
echo EXE: %DIST_DIR%\%EXE_NAME%
echo ZIP: %ZIP_PATH%
echo.
echo ========================================================
pause
