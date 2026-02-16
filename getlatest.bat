echo.
echo ============================================
echo   CommonGround Dashboard - Github/Dashboard Download
echo ============================================
echo.

@echo off
setlocal enabledelayedexpansion

set REPO_URL=https://github.com/leekentvr/commonGroundDash.git

:: Cleanly capture the script directory WITHOUT adding extra quotes
set "TARGET_DIR=%~dp0"

echo Using script directory: "%TARGET_DIR%"
echo Checking for Git...

git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Git not found. Installing Git using winget...

    winget install --id Git.Git -e --source winget --silent

    echo Waiting for Git to finish installing...
    timeout /t 5 >nul

    git --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Git installation failed. Exiting.
        pause
        exit /b 1
    )

    echo Git installed successfully.
) else (
    echo Git is already installed.
)

if exist "%TARGET_DIR%\.git" (
    echo Repository exists. Pulling latest changes...
    cd /d "%TARGET_DIR%"
    git pull
) else (
    echo Repository not found. Cloning fresh copy...
    git clone "%REPO_URL%" "%TARGET_DIR%"
)

echo Done.
pause
