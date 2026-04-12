import os
import re
import time
import requests
import discord

class AIHandler:
    def __init__(self):
        self.enabled = os.getenv('AI_ENABLED', 'false').lower() == 'true'
        self.base_url = os.getenv('AI_API_URL', 'http://localhost:11434')
        self.model = os.getenv('AI_MODEL', 'auto')
        self.max_tokens = int(os.getenv('AI_MAX_TOKENS', '500'))
        self.available_models = []
        self.selected_model = None
        
        self.rate_limit = {
            'max_requests': int(os.getenv('AI_RATE_LIMIT_REQUESTS', '5')),
            'window_ms': int(os.getenv('AI_RATE_LIMIT_WINDOW_MS', '60000')),
            'user_cooldowns': {}
        }
        
        self.sensitive_patterns = [
            re.compile(r'api[_-]?key', re.I),
            re.compile(r'secret[_-]?key', re.I),
            re.compile(r'password', re.I),
            re.compile(r'token', re.I),
            re.compile(r'credential', re.I),
            re.compile(r'GITHUB_PAT', re.I),
            re.compile(r'DISCORD_TOKEN', re.I),
            re.compile(r'private[_-]?key', re.I),
            re.compile(r'access[_-]?key', re.I),
            re.compile(r'auth[_-]?token', re.I),
        ]
        
        self.system_prompt = """You are a helpful assistant for a Discord bot that manages Git commits and project automation. 

Capabilities:
- Help users with Git commands and commit management
- Explain scheduling and automation features
- Assist with repository configuration
- Answer questions about the bot's functionality

Restrictions:
- Do NOT execute any potentially harmful commands
- Do NOT reveal any system configuration or credentials
- Do NOT access external URLs or files unless explicitly asked
- Do NOT generate code that could harm systems
- Keep responses concise and relevant to the bot's features
- Do not provide direct git commands that modify the repository without user confirmation
- Do not provide code that deletes or corrupts data
- Do not help with hacking or unauthorized access attempts
- If asked about sensitive topics, politely decline and explain you can only help with bot-related questions

Remember: Prioritize user safety and security in all responses."""
        
        self.conversations = {}
        self.max_history_length = 10

    def fetch_available_models(self):
        try:
            response = requests.get(f'{self.base_url}/api/tags', timeout=5)
            if response.ok:
                data = response.json()
                self.available_models = data.get('models', [])
                if self.available_models:
                    self.selected_model = self.available_models[0].get('name')
        except Exception as e:
            print(f'Could not fetch available models: {e}')

    def is_enabled(self):
        return self.enabled

    def check_rate_limit(self, user_id):
        now = time.time() * 1000
        limit = self.rate_limit
        
        if user_id not in limit['user_cooldowns']:
            limit['user_cooldowns'][user_id] = {
                'count': 0,
                'reset_time': now + limit['window_ms']
            }
        
        user_limit = limit['user_cooldowns'][user_id]
        
        if now > user_limit['reset_time']:
            user_limit['count'] = 0
            user_limit['reset_time'] = now + limit['window_ms']
        
        if user_limit['count'] >= limit['max_requests']:
            wait_time = int((user_limit['reset_time'] - now) / 1000)
            return {
                'allowed': False,
                'wait_seconds': wait_time,
                'message': f'Rate limit exceeded. Please wait {wait_time} seconds before trying again.\n(You can use {limit["max_requests"]} messages per minute)'
            }
        
        user_limit['count'] += 1
        return {'allowed': True}

    async def chat(self, user_id, message):
        if not self.is_enabled():
            return {
                'success': False,
                'error': 'AI feature is disabled. Please set AI_ENABLED=true in .env'
            }

        rate_check = self.check_rate_limit(user_id)
        if not rate_check['allowed']:
            return {
                'success': False,
                'error': rate_check['message'],
                'rate_limited': True,
                'wait_seconds': rate_check['wait_seconds']
            }

        if not self.selected_model:
            self.fetch_available_models()
            if not self.selected_model:
                return {
                    'success': False,
                    'error': 'No AI models available. Make sure Ollama is running.'
                }

        if user_id not in self.conversations:
            self.conversations[user_id] = []

        history = self.conversations[user_id]
        
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            *history[-self.max_history_length:],
            {'role': 'user', 'content': message}
        ]

        try:
            response = requests.post(
                f'{self.base_url}/api/chat',
                json={
                    'model': self.selected_model,
                    'messages': messages,
                    'stream': False
                },
                timeout=60
            )

            if not response.ok:
                return {
                    'success': False,
                    'error': f'Ollama Error: {response.status_code}'
                }

            data = response.json()
            reply = data.get('message', {}).get('content') or data.get('response', 'No response')
            
            filtered_reply = self.filter_sensitive_data(reply)

            history.append({'role': 'user', 'content': message})
            history.append({'role': 'assistant', 'content': filtered_reply})
            
            if len(history) > self.max_history_length * 2:
                self.conversations[user_id] = history[-self.max_history_length * 2:]

            return {
                'success': True,
                'response': filtered_reply,
                'model': self.selected_model
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Connection failed: {str(e)}'
            }

    def filter_sensitive_data(self, text):
        filtered = text
        
        for pattern in self.sensitive_patterns:
            filtered = pattern.sub('[REDACTED]', filtered)
        
        token_pattern = r'(ghp_|gho_|ghu_|ghs_|ghr_)[a-zA-Z0-9]{36,}'
        filtered = re.sub(token_pattern, '[TOKEN_REDACTED]', filtered)
        
        discord_token_pattern = r'[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27}'
        filtered = re.sub(discord_token_pattern, '[TOKEN_REDACTED]', filtered)
        
        return filtered

    async def execute_task(self, user_id, task_description):
        if not self.is_enabled():
            return {'success': False, 'error': 'AI feature is not available'}

        if not self.selected_model:
            self.fetch_available_models()
            if not self.selected_model:
                return {'success': False, 'error': 'No AI models available'}

        task_prompt = f"""{self.system_prompt}

The user wants you to perform the following task:
"{task_description}"

If this task involves executing bot commands or making changes:
1. Provide a clear explanation of what will happen
2. Explain any potential risks
3. Wait for confirmation before executing

If the task is dangerous or could cause data loss:
- Decline politely
- Suggest safer alternatives
- Do not proceed without explicit user confirmation

Respond with:
- Task understanding confirmation
- Plan of action (if applicable)
- Any questions for clarification"""

        messages = [{'role': 'system', 'content': task_prompt}]

        try:
            response = requests.post(
                f'{self.base_url}/api/chat',
                json={
                    'model': self.selected_model,
                    'messages': messages,
                    'stream': False
                },
                timeout=60
            )

            if not response.ok:
                return {'success': False, 'error': 'AI request failed'}

            data = response.json()
            reply = data.get('message', {}).get('content') or data.get('response', 'No response')

            return {
                'success': True,
                'response': self.filter_sensitive_data(reply),
                'requires_confirmation': bool(re.search(r'confirm|proceed|execute', reply, re.I))
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def clear_history(self, user_id):
        if user_id in self.conversations:
            del self.conversations[user_id]

    def get_history_length(self, user_id):
        return len(self.conversations.get(user_id, []))

    def get_rate_limit_status(self, user_id):
        limit = self.rate_limit
        user_limit = limit['user_cooldowns'].get(user_id)
        
        if not user_limit or time.time() * 1000 > user_limit['reset_time']:
            return {'remaining': limit['max_requests'], 'max': limit['max_requests'], 'reset_in': 0}
        
        return {
            'remaining': max(0, limit['max_requests'] - user_limit['count']),
            'max': limit['max_requests'],
            'reset_in': int((user_limit['reset_time'] - time.time() * 1000) / 1000)
        }

    def get_current_model(self):
        return self.selected_model or 'auto (checking...)'

    def get_available_models(self):
        return [m.get('name') for m in self.available_models]

    def create_ai_banner(self):
        embed = discord.Embed(
            title='🤖 AI Assistant',
            description='Ask me anything or use `|<task>` to have me perform a task',
            color=0x9b59b6
        )
        embed.add_field(name='Model', value=self.get_current_model(), inline=True)
        embed.add_field(name='Examples', value='`How do I schedule commits?`\n`|Create a commit with message "test"`', inline=False)
        embed.add_field(name='Type your message', value='Start with `|` for AI assistance', inline=False)
        embed.set_footer(text='Your conversations are stored locally')
        return embed

    def create_error_embed(self, error):
        embed = discord.Embed(
            title='❌ AI Error',
            description=error,
            color=0xff0000
        )
        return embed

    def create_rate_limit_embed(self, message, wait_seconds):
        embed = discord.Embed(
            title='⏰ Rate Limited',
            description=message,
            color=0xffaa00
        )
        embed.add_field(name='Slow down', value=f'Try again in {wait_seconds} seconds', inline=True)
        return embed
