@echo off
echo Setting up PostgreSQL database for Guides...
echo =========================================

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.7 or higher and try again.
    pause
    exit /b 1
)

:: Create a virtual environment
echo Creating virtual environment...
if not exist "venv" (
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

:: Activate the virtual environment and install dependencies
echo Installing dependencies...
call venv\Scripts\activate
pip install -r database/requirements-db.txt

:: Run the database setup script
echo.
echo Starting database setup...
python database/setup_database.py

:: Deactivate the virtual environment
deactivate

echo.
echo =========================================
echo Database setup completed!
echo You can now start the Django development server with:
echo    python manage.py runserver
echo =========================================
pause
