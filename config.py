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

# Code Review Configuration
REVIEW_RECIPIENT_MODE = os.getenv('REVIEW_RECIPIENT_MODE', 'specific')  # author, owner, specific
SPECIFIC_DISCORD_USER_ID = int(os.getenv('SPECIFIC_DISCORD_USER_ID', '0')) if os.getenv('SPECIFIC_DISCORD_USER_ID') else None
FALLBACK_CHANNEL_ID = int(os.getenv('FALLBACK_CHANNEL_ID', '0')) if os.getenv('FALLBACK_CHANNEL_ID') else None

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')  # Smaller model for chat
OLLAMA_CODE_MODEL = os.getenv('OLLAMA_CODE_MODEL', 'qwen2.5-coder:14b')  # Larger for code review

# GitHub Configuration (SIMPLIFIED - No webhook needed!)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_REPOS_TO_WATCH = os.getenv('GITHUB_REPOS_TO_WATCH', '').split(',') if os.getenv('GITHUB_REPOS_TO_WATCH') else []
CODE_REVIEW_CHECK_INTERVAL = int(os.getenv('CODE_REVIEW_CHECK_INTERVAL', '300'))  # Check every 5 minutes

# Conversational AI Configuration
ENABLE_CONVERSATIONAL_AI = os.getenv('ENABLE_CONVERSATIONAL_AI', 'true').lower() == 'true'
CONVERSATION_HISTORY_PATH = os.getenv('CONVERSATION_HISTORY_PATH', 'data/conversation_history.json')
MAX_CONVERSATION_HISTORY = int(os.getenv('MAX_CONVERSATION_HISTORY', '10'))

# User Mapping
USER_MAPPING_FILE = os.getenv('USER_MAPPING_FILE', 'user_mappings.json')

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
