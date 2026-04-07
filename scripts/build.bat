@echo off
setlocal
:: Change directory to project root (parent folder of scripts/)
cd /d "%~dp0.."

echo.
echo ========================================================
echo   Refiner Build Script
echo ========================================================
echo.
echo [1/3] Cleaning previous build files...
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist Refiner.spec del /f /q Refiner.spec

echo.
echo [2/3] Building Refiner.exe with PyInstaller...
echo Icon Path: assets\images\icon.ico
:: Bundling assets, core, and ui folders into the executable
pyinstaller --noconsole --onefile ^
    --icon="assets/images/icon.ico" ^
    --add-data "assets;assets" ^
    --add-data "core;core" ^
    --add-data "ui;ui" ^
    --name "Refiner" ^
    main.py

echo.
echo [3/3] Build Completed!
echo Output: dist\Refiner.exe
echo.
echo ========================================================
pause
