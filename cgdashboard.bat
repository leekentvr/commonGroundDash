@echo off
cd /d "%~dp0"

REM Use venv Python explicitly
set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo ERROR: venv Python not found at %PYTHON_EXE%
    pause
    exit /b 1
)

"%PYTHON_EXE%" "%~dp0main.py"
echo.
echo Script finished.
pause
