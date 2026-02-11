@echo off
REM World Bank Chatbot - Windows Startup Script
REM Usage: Double-click this file or run in terminal

echo ========================================
echo  World Bank Chatbot - Starting...
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

REM Check if in virtual environment
if not defined VIRTUAL_ENV (
    echo WARNING: Not in a virtual environment
    echo Recommendation: Create venv with 'python -m venv venv'
    echo.
)

REM Check OPENAI_API_KEY
if not defined OPENAI_API_KEY (
    echo ERROR: OPENAI_API_KEY not set!
    echo.
    echo Please set it:
    echo   1. Create .env file from .env.example
    echo   2. Or run: set OPENAI_API_KEY=sk-your-key-here
    echo.
    pause
    exit /b 1
)

REM Check if data exists
if not exist "data\world_bank_data.json" (
    echo WARNING: world_bank_data.json not found
    echo.
    echo Running extraction first...
    cd EXTRACTION_WB
    python collector.py
    if errorlevel 1 (
        echo.
        echo ERROR: Extraction failed!
        pause
        exit /b 1
    )
    cd ..
)

REM Start application
echo.
echo Starting FastAPI server...
echo.
echo The chatbot will be available at:
echo   http://localhost:8000
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

python app.py
