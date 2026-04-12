import os
import json
import asyncio
from datetime import datetime

import discord
from dotenv import load_dotenv

from modules.ai_handler import AIHandler
from modules.user_config_manager import UserConfigManager
from modules.cli_handler import CLIHandler
from modules.session_manager import SessionManager
from modules.banner_ui import BannerUI
from modules.button_handler import ButtonHandler

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands = discord.app_commands.CommandTree(client)

ai_handler = AIHandler()
user_config_manager = UserConfigManager()
session_manager = SessionManager()
banner_ui = BannerUI()
button_handler = ButtonHandler()
cli_handler = CLIHandler(ai_handler, user_config_manager, session_manager, banner_ui)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TARGET_REPO_PATH = os.getenv('TARGET_REPO_PATH', './repo')
TARGET_REPO_BRANCH = os.getenv('TARGET_REPO_BRANCH', 'main')
TARGET_REPO_REMOTE = os.getenv('TARGET_REPO_REMOTE', 'origin')

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')
    
    await tree.sync()
    print('✅ Commands synced')
    
    ai_handler.fetch_available_models()
    print(f'✅ AI Handler initialized (Model: {ai_handler.get_current_model()})')
    
    user_config_manager.initialize()
    print('✅ User Config Manager initialized')
    
    session_manager.initialize()
    print('✅ Session Manager initialized')
    
    asyncio.create_task(cleanup_inactive_sessions())
    print('✅ Auto-expire task started')

async def cleanup_inactive_sessions():
    while True:
        await asyncio.sleep(3600)
        expired = session_manager.cleanup_inactive_sessions()
        if expired > 0:
            print(f'✅ Cleaned up {expired} inactive sessions')

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    if not message.content.startswith('!'):
        return
    
    user_id = str(message.author.id)
    session = session_manager.get_active_session(user_id)
    
    if not session:
        session = session_manager.create_session(user_id, message.author.name, {
            'repo_path': TARGET_REPO_PATH,
            'repo_remote': TARGET_REPO_REMOTE,
            'branch': TARGET_REPO_BRANCH
        })
        
        embed = banner_ui.create_main_banner(message.author.name)
        view = banner_ui.create_feature_buttons()
        
        await message.channel.send(
            content=f'🎉 **New session started!** {message.author.name}',
            embed=embed,
            view=view
        )
        return
    
    result = await cli_handler.handle(message)
    
    if result:
        if isinstance(result, list):
            for item in result:
                await message.channel.send(embed=item)
        else:
            await message.channel.send(embed=result)

@client.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.application_command:
        return
    
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get('custom_id') if interaction.data else None
        
        if custom_id:
            result = button_handler.handle(custom_id, interaction)
            
            if result and result.get('show_banner'):
                embed = banner_ui.create_main_banner(interaction.user.name)
                view = banner_ui.create_feature_buttons()
                await interaction.response.edit_message(embed=embed, view=view)
            elif result:
                await interaction.response.send_message(
                    embed=result.get('embed'),
                    ephemeral=result.get('ephemeral', False)
                )

if not DISCORD_TOKEN:
    print('Error: DISCORD_TOKEN not found in .env')
    exit(1)

client.run(DISCORD_TOKEN)
