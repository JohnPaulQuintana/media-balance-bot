@echo off
cd /d "%~dp0"

:: Check if venv exists, if not, create it
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Install requirements
echo Installing dependencies...
pip install -r requirements.txt

:: Install Playwright (if not installed)
echo Installing Playwright...
playwright install

:: Run main.py
echo Running main.py...
python main.py

:: Deactivate virtual environment
echo Deactivating virtual environment...
deactivate

:: Keep the window open
pause
