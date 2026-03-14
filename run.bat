@echo off
REM Windows startup script for PEG Stock Valuation Microservice (Python)

echo ======================================
echo PEG Stock Valuation Microservice
echo (Python Version)
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist venv\ (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Check if .env file exists
if not exist .env (
    echo.
    echo Warning: .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo Please edit .env and add your API keys.
    echo.
    pause
)

REM Start the server
echo.
echo Starting PEG Stock Valuation Microservice...
echo.
python app.py
pause
