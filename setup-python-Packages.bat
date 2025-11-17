@echo off
rem Create a virtual environment in the ./venv folder if it doesn't exist
if not exist venv (
	python -m venv venv
)

rem Activate the venv (Windows batch)
call venv\Scripts\activate.bat

rem Upgrade pip then install requirements
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

rem Keep the window open when run interactively
if "%DEBUG%"=="1" pause