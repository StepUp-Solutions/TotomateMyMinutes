@echo off
:: Check if the .venv folder exists
if exist ".venv" (
    echo Activating virtual environment...
    call .venv\Scripts\activate
) else (
    echo No virtual environment found. Running without activating venv.
)

:: Launch the Python script
python main.py

:: Deactivate the virtual environment if it was activated
if defined VIRTUAL_ENV (
    deactivate
)
