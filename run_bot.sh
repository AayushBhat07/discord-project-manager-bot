#!/bin/bash

# Navigate to project directory
cd "/Users/aayush07/Desktop/Discord Project Manager"

# Activate virtual environment
source venv/bin/activate

# Run the bot (no nohup needed when launched via LaunchAgent)
python bot.py
