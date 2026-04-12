# Discord Project Manager Bot

A powerful Discord bot for project management with automated GitHub commit scheduling. Track tasks, generate reports, and automate your GitHub workflow directly from Discord.

![Discord](https://img.shields.io/badge/Discord-5865F2?style=flat&logo=discord&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-18%2B-brightgreen)
![GitHub](https://img.shields.io/badge/GitHub-Automation-blue)

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Commands](#commands)
  - [Task Management](#task-management)
  - [Commit Scheduler](#commit-scheduler)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## Features

### Task Management
- Create, update, and track project tasks
- Assign tasks to team members
- Set deadlines and priorities
- Generate automated 12-hour reports

### Commit Scheduler (v2.0)
- **Commit Now**: Create immediate GitHub commits
- **Backdated Commits**: Commit with past timestamps
- **Scheduled Commits**: Set up recurring commits with cron expressions
- **Pattern Generator**: Create contribution graph art with batch commits

## Prerequisites

- Node.js 18 or higher
- A Discord Bot Token
- A GitHub Personal Access Token (PAT)
- Git installed on the machine running the bot

## Installation

```bash
# Clone the repository
git clone https://github.com/AayushBhat07/discord-project-manager-bot.git
cd discord-project-manager-bot

# Install dependencies
npm install

# Copy the environment file
cp .env.example .env
```

## Configuration

Edit the `.env` file with your credentials:

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token
CLIENT_ID=your_discord_client_id
GUILD_ID=your_discord_server_id

# GitHub Configuration
GITHUB_PAT=your_github_personal_access_token
TARGET_REPO_PATH=./path/to/your/repo
TARGET_REPO_REMOTE=origin
TARGET_REPO_BRANCH=main

# Scheduler Configuration
MAX_SCHEDULED_JOBS=50
MAX_JOBS_PER_USER=10
```

### Getting Your Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to Bot section and create a bot
4. Copy the token

### Getting Your GitHub PAT

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a classic token with `repo` scope

## Commands

### Task Management

| Command | Description |
|---------|-------------|
| `/task create <title> <description>` | Create a new task |
| `/task list` | List all tasks |
| `/task assign <task-id> <user>` | Assign a task to a user |
| `/task complete <task-id>` | Mark a task as complete |
| `/report` | Generate a 12-hour task report |

### Commit Scheduler

| Command | Description |
|---------|-------------|
| `/commit now <message>` | Create a commit with current timestamp |
| `/commit at <date> <time> <message>` | Create a backdated commit |
| `/commit schedule <cron> <message>` | Schedule recurring commits |
| `/commit cancel <job-id>` | Cancel a scheduled job |
| `/commit log` | View all scheduled jobs |
| `/commit pattern <template> <message>` | Generate contribution graph pattern |

#### Date/Time Formats for `/commit at`

The `date` parameter accepts:
- ISO format: `2024-01-15`
- Relative: `yesterday`, `3 days ago`, `in 2 weeks`
- Day of week: `next Monday`, `last Friday`

#### Cron Expressions for `/commit schedule`

| Expression | Description |
|-------------|-------------|
| `0 9 * * *` | Daily at 9:00 AM |
| `0 9 * * 1` | Every Monday at 9:00 AM |
| `0 0 * * 1,3,5` | Mon/Wed/Fri at midnight |
| `*/15 * * * *` | Every 15 minutes |

#### Pattern Templates for `/commit pattern`

Available templates: `A`, `B`, `C`, `heart`, `star`, `check`, `smiley`

## Usage Examples

### Create an Immediate Commit

```
/commit now "feat: Add new feature"
```

Result: Creates a commit with the current timestamp and pushes to remote.

### Create a Backdated Commit

```
/commit at date: yesterday time: 14:30 message: "docs: Update documentation"
```

Result: Creates a commit dated yesterday at 2:30 PM.

### Schedule Weekly Commits

```
/commit schedule cron: "0 9 * * 1" message: "chore: Weekly status update"
```

Result: Creates a commit every Monday at 9:00 AM.

### Generate Contribution Graph Pattern

```
/commit pattern template: heart message: "contribution: {date}" start-week: 48
```

Result: Creates commits forming a heart pattern on the GitHub contribution graph.

### View Scheduled Jobs

```
/commit log
```

Result: Shows all your scheduled commit jobs with their status and next run time.

### Cancel a Scheduled Job

```
/commit cancel job-id: <job-id-from-log>
```

Result: Stops the scheduled commit from running.

## Testing

```bash
# Run all tests
npm test

# Run tests with watch mode
npm run test:watch

# Run specific test suite
npm test -- --grep "TimestampProcessor"
```

## Security

- **Never commit your `.env` file** - It contains sensitive credentials
- The `.env` file is already in `.gitignore`
- Use appropriate GitHub PAT scopes (minimum required: `repo`)
- Review all commit actions in Discord channel logs
- This feature is for legitimate use only (documenting real work, scheduling automation)

## Known Limitations

- Commits more than 24 hours in the future are not allowed by default
- Timestamps cannot be before January 1, 1970 (Git epoch)
- The repository must be a valid git repository with a configured remote
- Network issues may cause commit failures - check your connection

## Troubleshooting

### "Repository not found" error
- Ensure `TARGET_REPO_PATH` points to a valid git repository
- The repository must have an initialized `.git` folder

### "Invalid cron expression" error
- Use valid cron syntax (5 fields: minute hour day month weekday)
- Test your expression at [crontab.guru](https://crontab.guru)

### "Configuration Error" on commit commands
- Verify `GITHUB_PAT` is set in your `.env` file
- Ensure the token has appropriate GitHub permissions

### Commits not appearing on GitHub
- Check that the remote is properly configured
- Verify you have push permissions to the repository

## Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with ❤️ by [AayushBhat07](https://github.com/AayushBhat07)