import discord

class BannerUI:
    def create_main_banner(self, username):
        embed = discord.Embed(
            title='🎉 Welcome to Project Manager Bot!',
            description=f'Hello {username}! I\'m here to help you manage your Git commits and project automation.',
            color=0x00ccff
        )
        embed.add_field(
            name='📝 What I can do',
            value='• Schedule commits with cron expressions\n'
                  '• Create backdated commits\n'
                  '• Generate pattern commits (hearts, stars, etc.)\n'
                  '• Chat with AI for help',
            inline=False
        )
        embed.add_field(
            name='🚀 Quick Start',
            value='1. Type `!help` for all commands\n'
                  '2. Type `|How do I schedule commits?` for AI help\n'
                  '3. Use `!setup github <pat> <repo>` to configure',
            inline=False
        )
        embed.set_footer(text='Your session is active for 30 days')
        return embed

    def create_features_list_embed(self):
        embed = discord.Embed(
            title='📚 Command Reference',
            description='Here are all available commands:',
            color=0x0099ff
        )
        embed.add_field(
            name='📋 General',
            value='`!help` - Show this help\n'
                 '`!start` - Start a new session\n'
                 '`!mystats` - View your statistics\n'
                 '`!showoptions` - Show main menu',
            inline=False
        )
        embed.add_field(
            name='🤖 AI Commands',
            value='`|message` - Chat with AI assistant\n'
                 '`!clearhistory` - Clear AI chat history\n'
                 '`!aistatus` - Check AI rate limits',
            inline=False
        )
        embed.add_field(
            name='📡 GitHub Setup',
            value='`!setup github <pat> <repo> [branch]` - Configure GitHub\n'
                 '`!mygithub` - View your GitHub config',
            inline=False
        )
        embed.add_field(
            name='⏰ Scheduling',
            value='`!schedule <cron> "<message>"` - Schedule commits\n'
                 '`!commits` - List your scheduled jobs\n'
                 '`!cancel <job-id>` - Cancel a job',
            inline=False
        )
        return embed

    def create_detailed_help_embed(self):
        embed = discord.Embed(
            title='📖 Detailed Command Guide',
            color=0x00ccff
        )
        embed.add_field(
            name='!schedule',
            value='Schedule recurring commits with cron expressions.\n'
                 'Example: `!schedule "0 9 * * 1" "Weekly report"`\n'
                 'This schedules every Monday at 9 AM.',
            inline=False
        )
        embed.add_field(
            name='!pastcommit',
            value='Create a backdated commit.\n'
                 'Example: `!pastcommit 2024-01-15 14:30 "Fixed bug"`',
            inline=False
        )
        embed.add_field(
            name='!pattern',
            value='Generate pattern commits.\n'
                 'Example: `!pattern heart "love"`',
            inline=False
        )
        return embed

    def create_success_embed(self, title, description, fields=None):
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x00ff00
        )
        if fields:
            for field in fields:
                embed.add_field(
                    name=field.get('name', ''),
                    value=field.get('value', ''),
                    inline=field.get('inline', True)
                )
        return embed

    def create_error_embed(self, title, description):
        return discord.Embed(
            title=f'❌ {title}',
            description=description,
            color=0xff0000
        )

    def create_info_embed(self, title, description):
        return discord.Embed(
            title=title,
            description=description,
            color=0xffaa00
        )

    def create_feature_buttons(self):
        view = discord.ui.View()
        
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label='📋 Commands',
            custom_id='btn_help'
        ))
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label='🤖 AI Chat',
            custom_id='btn_ai'
        ))
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.success,
            label='⏰ Schedule',
            custom_id='btn_schedule'
        ))
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label='📡 GitHub',
            custom_id='btn_github'
        ))
        
        return view
