#!/bin/bash
# Script to run the backend with local PostgreSQL connection

# Set the database URL to localhost
export DATABASE_URL=postgresql://skillboard:skillboard@localhost:5432/skillboard

# Run the backend
echo "Starting backend with local PostgreSQL connection..."
echo "Database URL: $DATABASE_URL"
uvicorn app.main:app --reload
