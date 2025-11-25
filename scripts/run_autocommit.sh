#!/bin/bash

# Wrapper script for LaunchAgent to run daily_commit_bot.py
# Uses absolute paths to avoid symlink resolution issues

PROJECT_ROOT="/Users/aayush07/Desktop/Discord Project Manager"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python3"
PYTHON_SCRIPT="$PROJECT_ROOT/scripts/daily_commit_bot.py"

# Change to project directory
cd "$PROJECT_ROOT"

# Run the bot with virtual environment Python



exec "$VENV_PYTHON" "$PYTHON_SCRIPT"
