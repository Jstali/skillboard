#!/bin/bash
# Local development runner for Skillboard backend

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

# Activate the Python 3.12 virtual environment
source venv/bin/activate

# Run the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

