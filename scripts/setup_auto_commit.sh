#!/bin/bash

# Setup Auto-Commit for macOS/Linux
# Creates a LaunchAgent that runs the commit bot on laptop startup

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PLIST_FILE="$HOME/Library/LaunchAgents/com.discord.autocommit.plist"
PYTHON_SCRIPT="$PROJECT_ROOT/scripts/daily_commit_bot.py"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python3"

echo "================================================"
echo "Discord Bot Auto-Commit Setup"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ ERROR: Virtual environment not found at $VENV_PYTHON"
    echo "Please create a virtual environment first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

echo "✓ Using Python: $VENV_PYTHON"

# Make commit bot executable
chmod +x "$PYTHON_SCRIPT"
echo "✓ Made commit bot executable"

# Create LaunchAgent plist
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.discord.autocommit</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_PYTHON</string>
        <string>$PYTHON_SCRIPT</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>StartInterval</key>
    <integer>3600</integer>
    
    <key>WorkingDirectory</key>
    <string>$PROJECT_ROOT</string>
    
    <key>StandardOutPath</key>
    <string>$PROJECT_ROOT/automation_data/commit_bot.log</string>
    
    <key>StandardErrorPath</key>
    <string>$PROJECT_ROOT/automation_data/commit_bot_error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

echo "✓ Created LaunchAgent plist: $PLIST_FILE"

# Load the LaunchAgent
launchctl unload "$PLIST_FILE" 2>/dev/null
launchctl load "$PLIST_FILE"

echo "✓ LaunchAgent loaded and active"
echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "The commit bot will now run:"
echo "  • On laptop startup"
echo "  • Every hour while laptop is on"
echo ""
echo "To manually run the bot:"
echo "  python3 $PYTHON_SCRIPT"
echo ""
echo "To stop auto-commits:"
echo "  launchctl unload $PLIST_FILE"
echo ""
echo "To restart auto-commits:"
echo "  launchctl load $PLIST_FILE"
echo ""
echo "Logs are saved to:"
echo "  $PROJECT_ROOT/automation_data/commit_bot.log"
echo ""
