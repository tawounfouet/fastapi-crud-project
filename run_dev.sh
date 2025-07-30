#!/bin/bash

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Run FastAPI application
.venv/bin/fastapi run --reload --port 8001 app/main.py
