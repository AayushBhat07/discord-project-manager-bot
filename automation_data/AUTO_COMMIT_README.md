# Discord Bot Auto-Commit System

Automated development system that implements features incrementally with daily commits.

## 📋 What It Does

This system automatically:
- Implements 3 major Discord bot features over 15 days
- Makes 3 commits per day (spaced 30-90 minutes apart)
- Creates a professional development history
- Tracks progress in `development_plan.json`

## 🎯 Features Being Built

1. **Time Tracking & Reports** (Days 1-5)
   - Start/stop timers for tasks
   - Weekly time reports
   - Estimated vs actual comparison

2. **Project Health Score** (Days 6-10)
   - 0-100 health scoring
   - Risk identification
   - Weekly health reports

3. **Deadline Alerts & Reminders** (Days 11-15)
   - Automated DM reminders
   - Custom preferences
   - Snooze functionality

## 🚀 Quick Start

### Setup (One Time)

```bash
cd "/Users/aayush07/Desktop/Discord Project Manager"
./scripts/setup_auto_commit.sh
```

This creates a macOS LaunchAgent that runs the commit bot:
- On laptop startup
- Every hour while laptop is running

### Manual Run

```bash
python3 scripts/daily_commit_bot.py
```

## 📂 File Structure

```
automation_data/
  ├── development_plan.json    # Task list and progress
  ├── commit_bot.log          # Execution logs
  └── commit_bot_error.log    # Error logs

scripts/
  ├── daily_commit_bot.py     # Main automation script
  └── setup_auto_commit.sh    # LaunchAgent setup

services/
  ├── time_tracking_service.py      # (Generated)
  ├── health_score_service.py       # (Generated)
  └── deadline_reminder_service.py  # (Generated)
```

## ⚙️ How It Works

1. **Check**: Has today's quota of commits been made?
2. **Skip**: If yes, exit gracefully
3. **Branch**: Switch to `features-dev` branch
4. **Implement**: Get next pending task from plan
5. **Commit**: Create meaningful commit with proper message
6. **Push**: Push to GitHub
7. **Wait**: Random delay (30-90 min) before next commit
8. **Repeat**: Continue until 3 commits made today

## 📊 Progress Tracking

View current status:
```bash
cat automation_data/development_plan.json | grep -A 5 "current_day"
```

View recent commits:
```bash
git log --oneline -10
```

View logs:
```bash
tail -f automation_data/commit_bot.log
```

## 🎮 Control Commands

### Stop Auto-Commits
```bash
launchctl unload ~/Library/LaunchAgents/com.discord.autocommit.plist
```

### Resume Auto-Commits
```bash
launchctl load ~/Library/LaunchAgents/com.discord.autocommit.plist
```

### Check Status
```bash
launchctl list | grep autocommit
```

## 🛡️ Safety Features

- **No Double Commits**: Checks if commits already made today
- **Git Safety**: Won't commit if working tree is dirty from manual changes
- **Logs Everything**: Full audit trail in log files
- **Reversible**: Can pause by unloading LaunchAgent
- **Smart Spacing**: Random delays between commits (30-90 min)

## 📝 Development Plan

The plan is broken into 45 tasks across 15 days:
- Days 1-5: Time Tracking features
- Days 6-10: Health Score features
- Days 11-15: Reminder features

Each task:
- Creates or modifies specific files
- Has descriptive commit message
- Implements working code
- Tracks status (pending/completed)

## 🔍 Monitoring

### Real-time Monitoring
```bash
# Watch logs
tail -f automation_data/commit_bot.log

# Check if running
ps aux | grep daily_commit_bot
```

### Verify Commits
```bash
# Today's commits
git log --since="midnight" --oneline

# All feature commits
git log --grep="feat(" --oneline
```

## 🚨 Troubleshooting

### Bot Not Running?
```bash
# Check LaunchAgent status
launchctl list | grep autocommit

# Reload LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.discord.autocommit.plist
launchctl load ~/Library/LaunchAgents/com.discord.autocommit.plist
```

### No Commits Today?
```bash
# Run manually to see errors
python3 scripts/daily_commit_bot.py

# Check logs
cat automation_data/commit_bot.log
```

### Wrong Branch?
The bot auto-creates and switches to `features-dev` branch.

## 📅 Timeline

- **Day 1**: Start timers, stop timers, time storage
- **Day 2**: Timer commands in bot
- **Day 3**: Time reports and statistics
- **Day 4**: Estimated vs actual, breakdowns
- **Day 5**: Active timers, editing, error handling
- **Day 6**: Health score calculator
- **Day 7**: Risk detection, bottlenecks
- **Day 8**: Health reports and automation
- **Day 9**: Trends, visualization, alerts
- **Day 10**: Velocity, dashboard, caching
- **Day 11**: Reminder service foundation
- **Day 12**: Deadline detection, escalation
- **Day 13**: User preferences, custom times
- **Day 14**: Snooze, batching, statistics
- **Day 15**: Integration and testing

## 🎯 Expected Results

After 15 days:
- ✅ 45 commits on GitHub (3 per day × 15 days)
- ✅ 3 complete features implemented
- ✅ Professional commit history
- ✅ Working code at each step
- ✅ Clear development progression

## 💡 Tips

1. **Let it run**: Don't manually commit on days the bot is active
2. **Check logs**: Monitor progress in commit_bot.log
3. **Be patient**: Commits are spaced throughout the day
4. **Test features**: After each day, test the new functionality
5. **Merge when done**: After 15 days, merge `features-dev` to `main`

## 🔐 Privacy

All code generation happens locally. No external APIs used.
