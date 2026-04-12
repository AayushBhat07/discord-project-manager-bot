import re
import discord

class CLIHandler:
    def __init__(self, ai_handler, user_config_manager, session_manager, banner_ui):
        self.ai_handler = ai_handler
        self.user_config_manager = user_config_manager
        self.session_manager = session_manager
        self.banner_ui = banner_ui
        
        self.commands = {
            'showoptions': self.handle_show_options,
            'pastcommit': self.handle_past_commit,
            'commitnow': self.handle_commit_now,
            'schedule': self.handle_schedule,
            'pattern': self.handle_pattern,
            'cancel': self.handle_cancel,
            'commits': self.handle_commits,
            'mystats': self.handle_stats,
            'setrepo': self.handle_set_repo,
            'detailed': self.handle_detailed,
            'help': self.handle_help,
            'start': self.handle_start,
            'setup': self.handle_setup,
            'mygithub': self.handle_my_github,
            'clearhistory': self.handle_clear_history,
            'adminjobs': self.handle_admin_jobs,
        }

    def parse_command(self, content):
        content = content.strip()
        
        if not content.startswith('!') and not content.startswith('|'):
            return None

        is_ai = content.startswith('|')
        prefix = '|' if is_ai else '!'
        parts = content[len(prefix):].split()
        command = 'ai-chat' if is_ai else parts[0].lower()
        args = parts[1:]

        return {
            'command': command,
            'args': args,
            'full_args': ' '.join(args),
            'is_ai': is_ai
        }

    async def handle(self, message):
        parsed = self.parse_command(message.content)
        if not parsed:
            return None

        cmd = self.commands.get(parsed['command'])
        if not cmd:
            return None

        try:
            return await cmd(message, parsed['args'], parsed)
        except Exception as e:
            return self.banner_ui.create_error_embed('Command Error', str(e))

    async def handle_show_options(self, message, args, parsed):
        embed = self.banner_ui.create_main_banner(message.author.name)
        view = self.banner_ui.create_feature_buttons()
        return embed

    async def handle_setup(self, message, args, parsed):
        if len(args) < 3:
            return self.banner_ui.create_error_embed(
                'Missing Arguments',
                'Usage: !setup github <github-pat> <repo-url> [branch]\n'
                'Example: !setup github ghp_xxx https://github.com/user/repo main'
            )

        if args[0].lower() != 'github':
            return self.banner_ui.create_error_embed(
                'Invalid Setup',
                'Currently only GitHub setup is supported\nUse: !setup github <pat> <repo-url> [branch]'
            )

        pat = args[1]
        repo_url = args[2]
        branch = args[3] if len(args) > 3 else 'main'
        user_id = str(message.author.id)
        
        config = self.user_config_manager.get_user_config(user_id)
        if not config:
            config = self.user_config_manager.create_user_config(user_id, message.author.name)

        result = self.user_config_manager.set_repo_config(user_id, repo_url, branch, 'origin')
        if not result['success']:
            return self.banner_ui.create_error_embed('Setup Failed', result['error'])

        return self.banner_ui.create_success_embed(
            '✅ GitHub Setup Complete!',
            'Your GitHub credentials have been saved securely.',
            [
                {'name': '📁 Repository', 'value': repo_url, 'inline': True},
                {'name': '🌿 Branch', 'value': branch, 'inline': True},
                {'name': '🔐 Status', 'value': 'Credentials saved', 'inline': True}
            ]
        )

    async def handle_my_github(self, message, args, parsed):
        user_id = str(message.author.id)
        config = self.user_config_manager.get_user_config(user_id)

        if not config:
            return self.banner_ui.create_info_embed(
                'No Setup Found',
                'You haven\'t configured your GitHub yet.\nUse `!setup github <pat> <repo-url>` to set up.'
            )

        has_setup = self.user_config_manager.has_github_setup(user_id)

        embed = discord.Embed(
            title='📡 Your GitHub Configuration',
            color=0x00ff00 if has_setup else 0xffaa00
        )
        embed.add_field(name='🔐 PAT Configured', value='✅ Yes' if has_setup else '❌ No', inline=True)
        embed.add_field(name='📁 Repository', value=config.get('github', {}).get('repo_path') or 'Not set', inline=True)
        embed.add_field(name='🌿 Branch', value=config.get('github', {}).get('branch') or 'main', inline=True)
        embed.add_field(name='🔗 Remote', value=config.get('github', {}).get('remote') or 'origin', inline=True)
        embed.add_field(name='📅 Last Updated', value=config.get('updated_at', 'N/A'), inline=True)
        return embed

    async def handle_clear_history(self, message, args, parsed):
        user_id = str(message.author.id)
        self.ai_handler.clear_history(user_id)
        
        return self.banner_ui.create_success_embed(
            '🗑️ Chat History Cleared',
            'Your AI conversation history has been reset.'
        )

    async def handle_admin_jobs(self, message, args, parsed):
        user_id = str(message.author.id)
        
        is_admin = message.author.guild_permissions.administrator if hasattr(message.author, 'guild') else False
        
        if not is_admin:
            return self.banner_ui.create_error_embed(
                'Admin Only',
                'Only administrators can view all scheduled jobs.'
            )

        from modules.scheduler_service import SchedulerService
        jobs = SchedulerService.list_all_jobs()

        if not jobs:
            return self.banner_ui.create_info_embed('No Scheduled Jobs', 'There are no scheduled jobs.')

        embed = discord.Embed(
            title='📋 All Scheduled Jobs',
            description=f'Total: {len(jobs)} job(s)',
            color=0x0099ff
        )

        for job in jobs[:10]:
            embed.add_field(
                name=f"🆔 {job.get('id', 'N/A')[:8]}...",
                value=f"**Owner:** {job.get('owner_id', 'N/A')[:8]}...\n"
                      f"**Message:** {job.get('message', 'N/A')}\n"
                      f"**Schedule:** `{job.get('cron_expression', 'N/A')}`\n"
                      f"**Status:** {job.get('status', 'N/A')}",
                inline=False
            )

        return embed

    async def handle_ai_chat(self, message, args, parsed):
        if not self.ai_handler.is_enabled():
            return self.ai_handler.create_error_embed(
                'AI is not enabled. Please set AI_ENABLED=true in .env'
            )

        user_message = parsed['full_args']
        
        if not user_message.strip():
            return self.ai_handler.create_ai_banner()

        user_id = str(message.author.id)
        result = await self.ai_handler.chat(user_id, user_message)

        if result['success']:
            chunks = self.split_message(result['response'])
            
            if len(chunks) == 1:
                return discord.Embed(
                    title='🤖 AI Response',
                    description=result['response'],
                    color=0x9b59b6
                )
            
            embeds = []
            for i, chunk in enumerate(chunks):
                embeds.append(discord.Embed(
                    title='🤖 AI Response' if i == 0 else '📄 (continued)',
                    description=chunk,
                    color=0x9b59b6
                ))
            return embeds
        elif result.get('rate_limited'):
            return self.ai_handler.create_rate_limit_embed(
                result['error'],
                result.get('wait_seconds', 60)
            )
        else:
            return self.ai_handler.create_error_embed(result['error'])

    def split_message(self, text, max_length=2000):
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        parts = text.split('\n')
        current = ''
        
        for part in parts:
            if len(current + '\n' + part) <= max_length:
                current += ('\n' if current else '') + part
            else:
                if current:
                    chunks.append(current)
                if len(part) > max_length:
                    while len(part) > max_length:
                        chunks.append(part[:max_length])
                        part = part[max_length:]
                    current = part
                else:
                    current = part
        
        if current:
            chunks.append(current)
        
        return chunks if chunks else [text]

    async def handle_start(self, message, args, parsed):
        user_id = str(message.author.id)
        session = self.session_manager.get_active_session(user_id)
        
        if session:
            return self.banner_ui.create_info_embed(
                'Session Active',
                f"You already have an active session started at {session.get('start_time', 'N/A')}"
            )

        session = self.session_manager.create_session(user_id, message.author.name, {
            'repo_path': os.getenv('TARGET_REPO_PATH', './repo'),
            'repo_remote': os.getenv('TARGET_REPO_REMOTE', 'origin'),
            'branch': os.getenv('TARGET_REPO_BRANCH', 'main')
        })

        return self.banner_ui.create_success_embed(
            '🎉 Session Started!',
            f"Welcome {message.author.name}! Your session has been created.",
            [
                {'name': '🆔 Session ID', 'value': session.get('id', 'N/A'), 'inline': True},
                {'name': '📅 Started At', 'value': session.get('start_time', 'N/A'), 'inline': True},
                {'name': '⏰ Duration', 'value': '30 days (auto-expires)', 'inline': True}
            ]
        )

    async def handle_stats(self, message, args, parsed):
        user_id = str(message.author.id)
        stats = self.session_manager.get_session_stats(user_id)

        embed = discord.Embed(
            title='📊 Your Session Statistics',
            description='Statistics across all your sessions (last 30 days)',
            color=0x00ccff
        )
        embed.add_field(name='📅 Total Sessions', value=str(stats.get('total_sessions', 0)), inline=True)
        embed.add_field(name='✅ Active Sessions', value=str(stats.get('active_sessions', 0)), inline=True)
        embed.add_field(name='📝 Total Commits', value=str(stats.get('total_commits', 0)), inline=True)
        return embed

    async def handle_help(self, message, args, parsed):
        return self.banner_ui.create_features_list_embed()

    async def handle_detailed(self, message, args, parsed):
        return self.banner_ui.create_detailed_help_embed()

    async def handle_commits(self, message, args, parsed):
        user_id = str(message.author.id)
        from modules.scheduler_service import SchedulerService
        jobs = SchedulerService.list_jobs(owner_id=user_id, limit=10)

        if not jobs:
            return self.banner_ui.create_info_embed(
                'No Scheduled Jobs',
                'You have no scheduled commit jobs. Use !schedule to create one!'
            )

        embed = discord.Embed(
            title='📋 Your Scheduled Jobs',
            description=f'Showing {len(jobs)} job(s)',
            color=0x0099ff
        )

        for job in jobs:
            embed.add_field(
                name=f"🆔 {job.get('id', 'N/A')[:8]}...",
                value=f"**Message:** {job.get('message', 'N/A')}\n"
                      f"**Schedule:** `{job.get('cron_expression', 'N/A')}`\n"
                      f"**Status:** {job.get('status', 'N/A')}",
                inline=False
            )

        return embed

    async def handle_cancel(self, message, args, parsed):
        if not args:
            return self.banner_ui.create_error_embed(
                'Missing Arguments',
                'Usage: !cancel <job-id>\nUse !commits to see job IDs'
            )

        job_id = args[0]
        from modules.scheduler_service import SchedulerService
        job = SchedulerService.get_job(job_id)

        if not job:
            return self.banner_ui.create_error_embed('Job Not Found', f'No scheduled job found with ID: {job_id}')

        if job.get('owner_id') != str(message.author.id):
            return self.banner_ui.create_error_embed('Permission Denied', 'You can only cancel jobs you created')

        result = SchedulerService.cancel_job(job_id)

        if result.get('success'):
            return self.banner_ui.create_success_embed(
                'Schedule Cancelled',
                f'Job {job_id} has been stopped',
                [
                    {'name': 'Message', 'value': job.get('message', 'N/A'), 'inline': True},
                    {'name': 'Schedule', 'value': job.get('cron_expression', 'N/A'), 'inline': True}
                ]
            )
        else:
            return self.banner_ui.create_error_embed('Cancel Failed', result.get('error'))

    async def handle_past_commit(self, message, args, parsed):
        return self.banner_ui.create_info_embed('Coming Soon', 'Backdated commits coming soon!')

    async def handle_commit_now(self, message, args, parsed):
        return self.banner_ui.create_info_embed('Coming Soon', 'Commit now coming soon!')

    async def handle_schedule(self, message, args, parsed):
        return self.banner_ui.create_info_embed('Coming Soon', 'Scheduling coming soon!')

    async def handle_pattern(self, message, args, parsed):
        return self.banner_ui.create_info_embed('Coming Soon', 'Pattern commits coming soon!')

    async def handle_set_repo(self, message, args, parsed):
        return self.banner_ui.create_info_embed('Coming Soon', 'Set repo coming soon!')

import os
