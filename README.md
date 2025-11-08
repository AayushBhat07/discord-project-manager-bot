# 🤖 Discord Project Manager Bot

> Your project's overachieving assistant that never sleeps ☕️

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![discord.py](https://img.shields.io/badge/discord.py-2.0+-blue.svg)](https://github.com/Rapptz/discord.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready Discord bot that monitors your project management web application and sends automated 12-hour reports to Discord channels.

![Bot Demo](https://img.shields.io/badge/Status-Production%20Ready-success)

## ✨ Features

✅ **Automated 12-Hour Reports** - Sends comprehensive project status updates at 8 AM and 8 PM IST \
✅ **Task Tracking** - Monitor completed, pending, and overdue tasks \
✅ **Team Performance** - View user completion statistics \
✅ **GitHub Integration** - Track recent commits and code changes \
✅ **User Mentions** - Automatically @mentions users with pending tasks \
✅ **Manual Commands** - Get status updates on demand \
✅ **Account Linking** - Link Discord accounts to web app users \

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or use a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
DISCORD_BOT_TOKEN=your_bot_token_here
REPORT_CHANNEL_ID=your_channel_id
WEBAPP_API_URL=https://your-app.convex.site
```

### 3. Test Configuration

Run the test script to verify everything is set up correctly:

```bash
python test_setup.py
```

### 4. Start the Bot

**Using the start script:**
```bash
./start.sh
```

**Or manually:**
```bash
python bot.py
```

## ⚙️ Configuration

### Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the bot token to `.env`
5. Enable these Privileged Gateway Intents:
   - Message Content Intent
   - Server Members Intent
6. Invite the bot to your server using OAuth2 URL generator:
   - Scopes: `bot`
   - Permissions: `Send Messages`, `Embed Links`, `Read Message History`, `Mention Everyone`

### Finding Channel ID

1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click the channel you want reports in
3. Click "Copy ID"
4. Paste it into `.env` as `REPORT_CHANNEL_ID`

## 📋 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!help` | Show all available commands | `!help` |
| `!report` | Trigger manual report (Admin only) | `!report` |
| `!status [project]` | Show status of a specific project | `!status Website Redesign` |
| `!mytasks` | Show your assigned tasks | `!mytasks` |
| `!link <email>` | Link Discord account to web app | `!link user@example.com` |
| `!ping` | Check bot latency | `!ping` |

## 📁 Project Structure

```
discord-bot/
├── bot.py                      # Main bot file
├── config.py                   # Configuration and constants
├── services/
│   ├── api_service.py         # API calls to web app
│   └── report_builder.py      # Discord embed builder
├── utils/
│   ├── scheduler.py           # 12-hour scheduling
│   └── formatters.py          # Text formatting utilities
├── .env                       # Environment variables (not in git)
├── .env.example               # Example environment file
├── requirements.txt           # Python dependencies
├── start.sh                   # Startup script
├── test_setup.py             # Configuration test script
└── README.md                  # This file
```

## 🔌 API Endpoints

The bot expects these endpoints from your Convex web app (use `.convex.site` domain):

- `GET /discord/projects` - Fetch all active projects
- `POST /discord/tasks/recent` - Fetch tasks updated in last N hours
- `POST /discord/stats` - Fetch user completion statistics
- `POST /discord/incomplete` - Fetch pending/overdue tasks
- `POST /discord/commits` - Fetch recent GitHub commits
- `POST /discord/link` - Link Discord user to web app user

## 📊 Report Format

Each 12-hour report includes:

- **Task Summary** - Completed and pending task counts
- **Completion Rate** - Percentage of tasks completed
- **Team Performance** - Top performers and their stats
- **Pending Tasks** - Tasks requiring attention with @mentions
- **GitHub Activity** - Recent commits and code changes
- **Next Report Time** - When the next automated report will run

## 🚀 Deployment

### Local Development

```bash
python bot.py
```

### Production (Railway)

1. Create a new project on [Railway](https://railway.app)
2. Connect your GitHub repository
3. Add environment variables in Railway dashboard
4. Deploy

### Production (Render)

1. Create a new Web Service on [Render](https://render.com)
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python bot.py`
5. Add environment variables
6. Deploy

### Running as a Service (Linux)

Create a systemd service file `/etc/systemd/system/discord-bot.service`:

```ini
[Unit]
Description=Discord Project Manager Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/discord-bot
ExecStart=/path/to/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable discord-bot
sudo systemctl start discord-bot
```

## 📝 Logging

Logs are written to both console and `bot.log` file.

View logs:
```bash
tail -f bot.log
```

## Error Handling

The bot handles:
- ✅ API endpoint failures (retries 3 times)
- ✅ Network timeouts (exponential backoff)
- ✅ Discord rate limiting (automatic queueing)
- ✅ Invalid API responses (logged and skipped)
- ✅ Bot reconnection after network issues

## 🐛 Troubleshooting

### Bot doesn't connect
- Verify `DISCORD_BOT_TOKEN` is correct
- Check bot has necessary permissions
- Ensure bot is invited to your server

### No reports sent
- Verify `REPORT_CHANNEL_ID` is correct
- Check bot has permission to send messages in the channel
- Review logs for errors

### API errors
- Verify `WEBAPP_API_URL` is correct and accessible
- Test API endpoints manually
- Check API authentication if required

### Dependencies issues
```bash
pip install --upgrade -r requirements.txt
```

## 🔒 Security Notes

⚠️ **Never commit `.env` file to version control**
- It contains sensitive tokens
- `.gitignore` already excludes it
- Use `.env.example` as a template

## 💬 Support

For issues or questions:
1. Check the logs in `bot.log`
2. Run `python test_setup.py` to verify configuration
3. Review API endpoint responses
4. Open an issue on GitHub

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - Feel free to use and modify

---

<p align="center">Made with ☕️ and 💻</p>
<p align="center">Built for teams who code > sleep 🌙</p>
