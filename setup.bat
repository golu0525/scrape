@echo off
REM Quick start guide for ISP Plan Scraper (Windows)

echo.
echo ==========================================
echo ISP Plan Scraper - Setup (Windows)
echo ==========================================
echo.

REM Check Python version
python --version

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Install Playwright browsers
echo Installing Playwright browsers...
playwright install chromium

REM Create environment file
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo Please edit .env with your database credentials
)

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit .env with your MySQL credentials
echo 2. Create MySQL database: CREATE DATABASE isp_plans;
echo 3. Run: python main.py
echo.

pause
