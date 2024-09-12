#!/bin/bash

# Check if the .venv directory exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "No virtual environment found. Running without activating venv."
fi

# Launch the Python script
python main.py

# Deactivate the virtual environment if it was activated
if [ ! -z "$VIRTUAL_ENV" ]; then
    deactivate
fi
