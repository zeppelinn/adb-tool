@echo off
echo ========================================
echo    ADB Tool Build Script for Windows
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Install dependencies
echo [1/3] Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

:: Build executable
echo.
echo [2/3] Building executable...
pyinstaller --clean build.spec

if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

:: Copy scrcpy folder
echo.
echo [3/3] Copying scrcpy files...
if exist "..\scrcpy-win64-v1.25" (
    xcopy /E /I /Y "..\scrcpy-win64-v1.25" "dist\scrcpy-win64-v1.25"
    echo [SUCCESS] scrcpy files copied
) else (
    echo [WARNING] scrcpy folder not found, please copy manually
)

echo.
echo ========================================
echo    Build Complete!
echo ========================================
echo.
echo Output: dist\AdbTool.exe
echo.
echo Make sure scrcpy-win64-v1.25 folder is in the same directory as AdbTool.exe
echo.
pause
