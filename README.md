# 🤖 Discord Project Manager Bot

> Your project's overachieving **AI-powered** assistant that never sleeps ☕️

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![discord.py](https://img.shields.io/badge/discord.py-2.0+-blue.svg)](https://github.com/Rapptz/discord.py)
[![Ollama](https://img.shields.io/badge/Ollama-AI%20Powered-green.svg)](https://ollama.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready Discord bot with **local AI integration** that monitors your project management web application, provides intelligent code reviews, and enables natural language conversations - all via Discord DMs and channels.

![Bot Demo](https://img.shields.io/badge/Status-Production%20Ready-success)
![AI Powered](https://img.shields.io/badge/AI-Ollama%20Local-blue)

## ✨ Features

### 📊 **Project Management**
✅ **Automated 12-Hour Reports** - Sends comprehensive project status updates at 8 AM and 8 PM IST
✅ **Project-Specific Reports** - Enable/disable reports per project with `!enable` and `!disable`
✅ **Task Tracking** - Monitor completed, pending, and overdue tasks grouped by priority
✅ **Team Performance** - View user completion statistics
✅ **GitHub Integration** - Track recent commits and code changes
✅ **User Mentions** - Automatically @mentions users with pending tasks
✅ **Account Linking** - Link Discord accounts to web app users

### 🤖 **AI-Powered Code Reviews** (NEW!)
✅ **Automatic PR Reviews** - AI analyzes every merged pull request using local Ollama
✅ **Security Scanning** - Identifies vulnerabilities and potential security issues
✅ **Smart Polling** - Checks GitHub every 5 minutes (no webhooks needed!)
✅ **Private DM Delivery** - Code reviews sent directly to you or PR authors
✅ **User Mapping** - Map GitHub usernames to Discord users for targeted reviews
✅ **Detailed Analysis** - File-by-file review with improvement suggestions

### 💬 **Conversational AI Assistant** (NEW!)
✅ **Natural Language Chat** - Ask questions naturally in DMs (no commands!)
✅ **Context-Aware** - Remembers conversation history and current topic
✅ **Smart Data Fetching** - Automatically pulls relevant project/task data
✅ **Local Privacy** - All AI runs on your laptop using Ollama (no external APIs)
✅ **Conversation Memory** - Maintains context across 10 messages
✅ **Follow-up Questions** - Understands references like "What about John?"

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Discord Bot Token** ([Get one here](https://discord.com/developers/applications))
- **Ollama** (for AI features) - [Install here](https://ollama.ai)
- **GitHub Personal Access Token** (for code reviews) - [Create here](https://github.com/settings/tokens)

### 1. Install Ollama and AI Models

```bash
# Install Ollama (macOS)
brew install ollama

# Or download from https://ollama.ai for other platforms

# Start Ollama server
ollama serve &

# Pull AI models
ollama pull llama3.1:8b          # For conversational AI (chat)
ollama pull qwen2.5-coder:14b    # For code reviews
```

### 2. Install Python Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Discord Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
REPORT_CHANNEL_ID=your_channel_id
FALLBACK_CHANNEL_ID=your_fallback_channel_id

# Web App API
WEBAPP_API_URL=https://your-app.convex.site

# AI Features (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_CODE_MODEL=qwen2.5-coder:14b
ENABLE_CONVERSATIONAL_AI=true

# Code Reviews
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_REPOS_TO_WATCH=owner/repo1,owner/repo2
REVIEW_RECIPIENT_MODE=specific  # or 'author' or 'owner'
SPECIFIC_DISCORD_USER_ID=your_discord_user_id
```

### 4. Initialize User Mappings (for Code Reviews)

Create `user_mappings.json` to map GitHub usernames to Discord IDs:

```json
{
  "your_github_username": "your_discord_user_id"
}
```

Or use the bot command after starting: `!map-user <github_username> @DiscordUser`

### 5. Start the Bot

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

### Project Management Commands
| Command | Description | Example |
|---------|-------------|---------|
| `!help` | Show all available commands | `!help` |
| `!status [project]` | Show project status or list all projects | `!status Mobile App` |
| `!mytasks` | Show your assigned tasks (grouped by priority) | `!mytasks` |
| `!report` | Trigger manual report (Admin only) | `!report` |
| `!enable <project>` | Enable scheduled reports for a project | `!enable Mobile App` |
| `!disable <project>` | Disable scheduled reports for a project | `!disable Mobile App` |
| `!enabled` | List projects with reports enabled | `!enabled` |
| `!link <email>` | Link Discord account to web app | `!link user@example.com` |
| `!ping` | Check bot latency and status | `!ping` |

### AI Code Review Commands
| Command | Description | Example |
|---------|-------------|---------|
| `!map-user <github> @user` | Map GitHub username to Discord user | `!map-user john_dev @John#1234` |
| `!unmap-user <github>` | Remove GitHub to Discord mapping | `!unmap-user john_dev` |
| `!list-mappings` | Show all user mappings | `!list-mappings` |

### Conversational AI (in DMs)
| Command | Description | Example |
|---------|-------------|---------|
| Just chat naturally! | Ask questions about projects/tasks | `How's the mobile app going?` |
| `!reset` | Clear conversation history | `!reset` |
| `!context` | Show what the bot remembers | `!context` |
| `!help-chat` | Show example questions | `!help-chat` |

## 📁 Project Structure

```
discord-bot/
├── bot.py                              # Main bot file with AI integration
├── config.py                           # Configuration and constants
├── services/
│   ├── api_service.py                 # API calls to web app
│   ├── report_builder.py              # Discord embed builder
│   ├── github_pr_service.py           # GitHub API integration
│   ├── github_poll_service.py         # Poll GitHub for merged PRs
│   ├── local_llm_service.py           # Ollama AI for code reviews
│   ├── conversational_ai_service.py   # Chat AI service
│   ├── conversation_manager.py        # Conversation history manager
│   ├── webapp_query_service.py        # Smart data fetching
│   ├── code_review_builder.py         # Code review embeds
│   └── user_mapping_service.py        # GitHub↔Discord mapping
├── utils/
│   ├── scheduler.py                   # 12-hour scheduling
│   ├── formatters.py                  # Text formatting utilities
│   └── diff_analyzer.py               # Git diff parsing
├── data/
│   └── conversation_history.json      # Conversation memory (gitignored)
├── user_mappings.json                 # GitHub→Discord user mappings
├── enabled_projects.json              # Projects with reports enabled
├── .env                              # Environment variables (not in git)
├── .env.example                      # Example environment file
├── requirements.txt                  # Python dependencies
├── run_bot.sh                        # Auto-start script (macOS)
└── README.md                         # This file
```

## 🔌 API Endpoints

The bot expects these endpoints from your Convex web app:

**Project Management:**
- `GET /discord/projects` - Fetch all active projects
- `POST /discord/tasks/recent` - Fetch tasks updated in last N hours
- `POST /discord/stats` - Fetch user completion statistics
- `POST /discord/incomplete` - Fetch pending/overdue tasks
- `POST /discord/commits` - Fetch recent GitHub commits
- `POST /discord/link` - Link Discord user to web app user

**AI Features:**
- Uses **GitHub REST API** for pull request data
- Uses **local Ollama** for AI analysis (no external API needed!)

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
