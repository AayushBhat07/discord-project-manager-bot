import os
from dotenv import load_dotenv

load_dotenv()

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
REPORT_CHANNEL_ID = int(os.getenv('REPORT_CHANNEL_ID', '0'))
COMMAND_PREFIX = '!'

# Web App API Configuration
API_BASE_URL = os.getenv('WEBAPP_API_URL', 'https://benevolent-kookabura-514.convex.site')

# Scheduling Configuration
REPORT_HOURS = [int(h) for h in os.getenv('REPORT_HOURS', '8,20').split(',')]
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')

# Admin Configuration
ADMIN_USER_IDS = [int(uid) for uid in os.getenv('ADMIN_USER_IDS', '').split(',') if uid]

# API Endpoints
ENDPOINTS = {
    'projects': f'{API_BASE_URL}/discord/projects',
    'recent_tasks': f'{API_BASE_URL}/discord/tasks/recent',
    'stats': f'{API_BASE_URL}/discord/stats',
    'incomplete': f'{API_BASE_URL}/discord/incomplete',
    'commits': f'{API_BASE_URL}/discord/commits',
    'link': f'{API_BASE_URL}/discord/link',
}

# Discord Embed Colors
COLORS = {
    'success': 0x00FF00,
    'warning': 0xFFFF00,
    'error': 0xFF0000,
    'info': 0x00FFFF,
    'primary': 0x0099FF,
}

# Emojis
EMOJIS = {
    'completed': '✅',
    'pending': '⏳',
    'top_performer': '🏆',
    'urgent': '⚠️',
    'commits': '🔧',
    'team': '👥',
    'stats': '📊',
    'project': '📋',
}
