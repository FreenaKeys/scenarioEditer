@echo off
rem run-in-venv.bat
rem Activates (or creates) the venv and runs main.py with any passed args.

rem Create a virtual environment in the ./venv folder if it doesn't exist
if not exist venv (
    python -m venv venv
)

rem Activate the venv for cmd.exe
call venv\Scripts\activate.bat

rem Install requirements if any (silent if requirements.txt empty)
if exist requirements.txt (
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
)

rem Run the application
python main.py %*

rem Keep console open so the user can see output when launched by double-click
if "%DEBUG%"=="1" pause
