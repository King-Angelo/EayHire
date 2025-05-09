@echo off
setlocal enabledelayedexpansion

echo Starting server setup and testing...

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

REM Check for pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo pip is not installed. Please install pip.
    exit /b 1
)

REM Create and activate virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Upgrade pip first
python -m pip install --upgrade pip

REM Install wheel and setuptools first
pip install --upgrade wheel setuptools

REM Install dependencies with specific order for critical packages
pip install djangorestframework==3.14.0
pip install Django==4.2.7
pip install -r requirements.txt

REM Run migrations
python manage.py makemigrations
python manage.py migrate

REM Start Redis server if installed
where redis-server >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" redis-server
    echo Redis server started
) else (
    echo Redis server not found. Some features may not work.
)

REM Start Celery worker if celery is installed
where celery >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" celery -A django_social_login_allauth worker --pool=solo -l info
    echo Celery worker started
) else (
    echo Celery not found. Background tasks will not work.
)

REM Start Django development server
echo Starting Django development server...
python manage.py runserver

REM Cleanup on exit
taskkill /F /IM "redis-server.exe" >nul 2>nul
taskkill /F /IM "celery.exe" >nul 2>nul

endlocal 