#!/bin/bash

# Navigate to project directory
cd "/Users/aayush07/Desktop/Discord Project Manager"

# Activate virtual environment
source venv/bin/activate

# Run the bot in background with output logging
nohup python bot.py > bot_output.log 2>&1 &

# Log that bot was started
echo "$(date): Bot started" >> startup.log
