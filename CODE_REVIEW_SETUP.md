# 🤖 AI-Powered Code Review Setup Guide

This guide will help you set up the automated code review feature that uses local AI (Ollama) to review GitHub pull requests and send reviews via Discord DM.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installing Ollama](#installing-ollama)
3. [Installing Python Dependencies](#installing-python-dependencies)
4. [Configuration](#configuration)
5. [GitHub Setup](#github-setup)
6. [Testing the Feature](#testing-the-feature)
7. [Commands](#commands)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

- **macOS** (this guide is for your MacBook)
- **Python 3.10+** with virtual environment
- **GitHub repository** with admin access
- **Discord bot** already running
- **Internet connection** for GitHub webhooks

---

## 🦙 Installing Ollama

Ollama is a local AI that runs on your laptop.

### Step 1: Install Ollama

```bash
brew install ollama
```

### Step 2: Start Ollama Service

```bash
ollama serve
```

Keep this terminal open, or run it in the background.

### Step 3: Download the Code Review Model

```bash
ollama pull qwen2.5-coder:14b
```

This downloads a 14B parameter coding model (~8GB). You can also use smaller models:
- `qwen2.5-coder:7b` (smaller, faster)
- `codellama:13b` (alternative model)

### Step 4: Verify Ollama is Running

```bash
curl http://localhost:11434/api/tags
```

You should see a JSON response with available models.

---

## 📦 Installing Python Dependencies

### Step 1: Activate Your Virtual Environment

```bash
cd "/Users/aayush07/Desktop/Discord Project Manager"
source venv/bin/activate
```

### Step 2: Install New Requirements

```bash
pip install -r requirements.txt
```

This installs:
- `ollama` - Talk to local AI
- `PyGithub` - Fetch PR data from GitHub
- `Flask` - Webhook server

---

## ⚙️ Configuration

### Step 1: Update `.env` File

Add these new variables to your `.env` file:

```env
# ======= CODE REVIEW CONFIGURATION =======

# DM Recipient Mode
# Options: "specific", "author", "owner"
REVIEW_RECIPIENT_MODE=specific

# Your Discord User ID (if mode is "specific")
SPECIFIC_DISCORD_USER_ID=690415992362500106

# Fallback channel if DM fails
FALLBACK_CHANNEL_ID=1304433064099385414

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:14b

# GitHub Token (create at https://github.com/settings/tokens)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx

# Webhook Secret (generate a random string)
GITHUB_WEBHOOK_SECRET=your_random_secret_here_12345

# Webhook Port
WEBHOOK_PORT=5000
```

### Step 2: Get Your Discord User ID

1. Enable Developer Mode in Discord: Settings → Advanced → Developer Mode
2. Right-click your username → Copy User ID
3. Paste it in `SPECIFIC_DISCORD_USER_ID`

### Step 3: Create GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Set scopes: `repo` (full control of private repositories)
4. Copy the token and paste in `GITHUB_TOKEN`

### Step 4: Generate Webhook Secret

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste in `GITHUB_WEBHOOK_SECRET`

---

## 🐙 GitHub Setup

### Step 1: Expose Your Local Webhook Server

Since GitHub needs to send webhooks to your laptop, you need to expose port 5000.

**Option A: Using ngrok (Recommended)**

```bash
# Install ngrok
brew install ngrok

# Start ngrok tunnel
ngrok http 5000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

**Option B: Using localhost.run (Free alternative)**

```bash
ssh -R 80:localhost:5000 ssh.localhost.run
```

Copy the provided URL.

### Step 2: Add Webhook to GitHub Repository

1. Go to your GitHub repo → Settings → Webhooks → Add webhook
2. **Payload URL:** `https://your-ngrok-url.ngrok.io/webhook/github`
3. **Content type:** `application/json`
4. **Secret:** Paste your `GITHUB_WEBHOOK_SECRET`
5. **Events:** Select "Pull requests" only
6. **Active:** ✅ Check this
7. Click "Add webhook"

### Step 3: Test the Webhook

GitHub will send a ping. Check if it shows a green ✅ checkmark.

---

## 🧪 Testing the Feature

### Step 1: Start the Bot

```bash
cd "/Users/aayush07/Desktop/Discord Project Manager"
source venv/bin/activate
python bot.py
```

You should see:
```
✅ Connected to Ollama at http://localhost:11434
Webhook server started on port 5000
```

### Step 2: Map Your GitHub Username

In Discord DM with the bot:

```
!map-user YourGitHubUsername @YourDiscordName
```

Example:
```
!map-user AayushBhat07 @Aayush
```

### Step 3: Create a Test Pull Request

1. Create a new branch in your repo
2. Make a small code change
3. Create a pull request
4. **Merge the pull request**

### Step 4: Check Your Discord DM

Within 30 seconds, you should receive a DM from the bot with:
- PR summary
- AI code review
- Security analysis
- Changed files list

---

## 📝 Commands

### User Mapping Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!map-user <github_username> @discord_user` | Map GitHub user to Discord | `!map-user john_dev @John` |
| `!unmap-user <github_username>` | Remove a mapping | `!unmap-user john_dev` |
| `!list-mappings` | Show all mappings | `!list-mappings` |

### Recipient Modes

Set in `.env` with `REVIEW_RECIPIENT_MODE`:

- **`specific`** - Always send to `SPECIFIC_DISCORD_USER_ID` (you get all reviews)
- **`author`** - Send to PR author's Discord DM
- **`owner`** - Send to repository owner's Discord DM

---

## 🐛 Troubleshooting

### Issue: "Could not connect to Ollama"

**Solution:**
```bash
# Check if Ollama is running
ps aux | grep ollama

# If not, start it
ollama serve
```

### Issue: "No DM received after PR merge"

**Checks:**
1. Is ngrok/localhost.run still running?
2. Check GitHub webhook deliveries (repo → Settings → Webhooks → Recent Deliveries)
3. Check bot logs for errors
4. Verify GitHub username is mapped: `!list-mappings`

### Issue: "DM failed, posted in channel"

This means:
- You have DMs disabled from server members, OR
- You don't share a server with the bot

**Solution:**
Enable DMs in Discord: Server → Privacy Settings → Allow direct messages

### Issue: Webhook shows "502 Bad Gateway"

**Solution:**
Restart ngrok and update the webhook URL in GitHub.

### Issue: AI review is slow

**Solutions:**
- Use a smaller model: `ollama pull qwen2.5-coder:7b`
- Update `.env`: `OLLAMA_MODEL=qwen2.5-coder:7b`

### Issue: Reviews missing for large PRs

Large PRs (>20 files or >1000 lines) are automatically truncated to fit in AI context.

---

## 🔄 Workflow Diagram

```
PR Merged on GitHub
       ↓
GitHub sends webhook to your laptop (via ngrok)
       ↓
Flask server receives webhook
       ↓
Bot fetches PR data from GitHub API
       ↓
Bot sends code + PR data to Ollama (local AI)
       ↓
Ollama analyzes code and generates review
       ↓
Bot determines recipient (you / author / owner)
       ↓
Bot tries to send DM
       ↓
   Success? ✅ Done
       ↓
   Failed? ❌ Post in fallback channel
```

---

## 🎯 Next Steps

1. **Test with real PRs** - Try merging actual code changes
2. **Fine-tune prompts** - Edit `services/local_llm_service.py` to customize AI prompts
3. **Add more users** - Use `!map-user` for your team
4. **Set up auto-start** - Add to macOS Login Items (optional)

---

## 🆘 Need Help?

- Check bot logs: `tail -f bot.log`
- Check Ollama logs: `ollama logs`
- Test webhook: GitHub → Settings → Webhooks → Redeliver

---

**Happy Reviewing! 🚀**
