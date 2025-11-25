import discord
from discord.ext import commands
import logging
import sys
import asyncio
import ssl
import random
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from aiohttp import web

from config import (
    DISCORD_TOKEN, REPORT_CHANNEL_ID, COMMAND_PREFIX,
    API_BASE_URL, REPORT_HOURS, TIMEZONE, ADMIN_USER_IDS,
    # Code review config
    REVIEW_RECIPIENT_MODE, SPECIFIC_DISCORD_USER_ID, FALLBACK_CHANNEL_ID,
    OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_CODE_MODEL, GITHUB_TOKEN, 
    GITHUB_REPOS_TO_WATCH, CODE_REVIEW_CHECK_INTERVAL, USER_MAPPING_FILE,
    # Conversational AI config
    ENABLE_CONVERSATIONAL_AI, CONVERSATION_HISTORY_PATH, MAX_CONVERSATION_HISTORY
)
from services.api_service import APIService
from services.report_builder import ReportBuilder
from services.user_mapping_service import UserMappingService
from services.github_pr_service import GitHubPRService
from services.github_poll_service import GitHubPollService
from services.local_llm_service import LocalLLMService
from services.code_review_builder import CodeReviewBuilder
from services.conversational_ai_service import ConversationalAIService
from services.conversation_manager import ConversationManager
from services.webapp_query_service import WebAppQueryService
from services.webapp_query_service import WebAppQueryService
from services.project_manager_service import ProjectManagerService
from utils.scheduler import ReportScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.dm_messages = True  # Enable DM messages

# Fix for macOS SSL certificate issue
try:
    import certifi
    ssl_context = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    ssl_context = ssl.create_default_context()

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)

# Initialize services
api_service = APIService(API_BASE_URL)
report_builder = ReportBuilder()
scheduler = ReportScheduler(TIMEZONE)

# Repo normalization for GitHub inputs
def _normalize_repo_list(repos):
    normalized = []
    for r in (repos or []):
        if not r:
            continue
        r = r.strip()
        if r.startswith('http'):
            try:
                parts = r.split('github.com/')[-1].split('/')
                if len(parts) >= 2:
                    normalized.append(f"{parts[0]}/{parts[1]}")
                else:
                    normalized.append(r)
            except Exception:
                normalized.append(r)
        else:
            normalized.append(r)
    return normalized

# Initialize code review services
user_mapping_service = UserMappingService(USER_MAPPING_FILE)
github_pr_service = GitHubPRService(GITHUB_TOKEN)
normalized_repos = _normalize_repo_list(GITHUB_REPOS_TO_WATCH)
github_poll_service = GitHubPollService(github_pr_service, normalized_repos)
llm_service = LocalLLMService(OLLAMA_BASE_URL, OLLAMA_CODE_MODEL)
code_review_builder = CodeReviewBuilder()

# Initialize conversational AI services
conversational_ai = ConversationalAIService(OLLAMA_BASE_URL, OLLAMA_MODEL)
conversation_manager = ConversationManager(CONVERSATION_HISTORY_PATH, MAX_CONVERSATION_HISTORY)
webapp_query = WebAppQueryService(api_service, github_service=github_pr_service, repos_to_watch=normalized_repos)
project_manager = ProjectManagerService()

# Path to enabled projects file
ENABLED_PROJECTS_FILE = os.path.join(os.path.dirname(__file__), 'enabled_projects.json')


def load_enabled_projects() -> List[str]:
    """Load list of enabled project IDs from file"""
    try:
        if os.path.exists(ENABLED_PROJECTS_FILE):
            with open(ENABLED_PROJECTS_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Failed to load enabled projects: {e}")
        return []


def save_enabled_projects(project_ids: List[str]) -> None:
    """Save list of enabled project IDs to file"""
    try:
        with open(ENABLED_PROJECTS_FILE, 'w') as f:
            json.dump(project_ids, f, indent=2)
        logger.info(f"Saved {len(project_ids)} enabled projects")
    except Exception as e:
        logger.error(f"Failed to save enabled projects: {e}")


# Cool rotating status messages
STATUS_MESSAGES = [
    (discord.ActivityType.watching, "👀 your team crush deadlines"),
    (discord.ActivityType.watching, "📊 projects like a hawk"),
    (discord.ActivityType.playing, "🎮 Project Manager 2024"),
    (discord.ActivityType.listening, "🎧 your feature requests"),
    (discord.ActivityType.competing, "🏆 for best bot award"),
    (discord.ActivityType.watching, "⚡ commits fly by"),
    (discord.ActivityType.watching, "🔥 productivity levels rise"),
]


async def rotate_status():
    """Rotate bot status every 30 seconds"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            activity_type, name = random.choice(STATUS_MESSAGES)
            await bot.change_presence(
                activity=discord.Activity(type=activity_type, name=name),
                status=discord.Status.online
            )
            await asyncio.sleep(30)  # Change every 30 seconds
        except Exception as e:
            logger.error(f"Error rotating status: {e}")
            await asyncio.sleep(30)


@bot.event
async def on_ready():
    """Event handler for when bot is ready"""
    
    logger.info(f'Bot connected as {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Connected to {len(bot.guilds)} guilds')
    
    # Start rotating status
    bot.loop.create_task(rotate_status())
    logger.info("Status rotation started")
    
    # Schedule automated reports
    scheduler.schedule_reports(send_scheduled_reports, REPORT_HOURS)
    scheduler.start()
    
    # Start GitHub polling for code reviews (MUCH SIMPLER!)
    if GITHUB_TOKEN and GITHUB_REPOS_TO_WATCH:
        bot.loop.create_task(poll_github_for_reviews())
        logger.info(f"✅ GitHub polling started for repos: {', '.join(normalized_repos)}")
        logger.info(f"   Checking every {CODE_REVIEW_CHECK_INTERVAL} seconds")
    else:
        logger.warning("⚠️ GitHub polling disabled (missing GITHUB_TOKEN or GITHUB_REPOS_TO_WATCH)")
    
    # Test Ollama connection
    if llm_service.test_connection():
        logger.info(f"✅ Connected to Ollama at {OLLAMA_BASE_URL}")
    else:
        logger.warning(f"⚠️ Could not connect to Ollama at {OLLAMA_BASE_URL}")
    
    logger.info(f"Bot is ready! Next report in: {scheduler.get_next_run_time()}")


@bot.event
async def on_command_error(ctx, error):
    """Global error handler for commands"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: {error.param.name}")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You don't have permission to run this command.")
    else:
        logger.error(f"Command error: {error}", exc_info=True)
        await ctx.send("❌ An error occurred while processing your command.")


@bot.event
async def on_message(message):
    """🤖 Handle all messages - route DMs to conversational AI"""
    
    # Ignore bot's own messages
    if message.author == bot.user:
        return
    
    # Route DMs to conversational AI (if not a command)
    if isinstance(message.channel, discord.DMChannel) and ENABLE_CONVERSATIONAL_AI:
        if not message.content.startswith(COMMAND_PREFIX):
            await handle_conversation(message)
            return
    
    # Process commands normally
    await bot.process_commands(message)


async def handle_conversation(message):
    """💬 Handle conversational AI in DMs"""
    user_id = str(message.author.id)
    user_question = message.content.strip()
    
    # Show typing indicator
    async with message.channel.typing():
        try:
            # Get conversation history and context
            history = conversation_manager.get_history(user_id)
            context = conversation_manager.get_context(user_id)
            
            # First message? Send welcome
            if not history:
                welcome = (
                    "🪄 Yo! I'm your friendly PM gremlin.\n\n"
                    "I snack on tasks, sip commits, and spit out status updates.\n\n"
                    "Ask me stuff like:\n"
                    "• How's the mobile app going?\n"
                    "• What's John working on?\n"
                    "• Are we on track for Friday?\n\n"
                    "Hit me with your toughest question. I dare you. 😎"
                )
                await message.reply(welcome)
                conversation_manager.add_message(user_id, 'assistant', welcome)
                return
            
            # Analyze question and fetch relevant data
            logger.info(f"Processing question from {message.author}: {user_question}")
            context_data = webapp_query.analyze_question_and_fetch_data(user_question, context)
            
            # Generate AI response
            ai_response = conversational_ai.chat(
                user_question=user_question,
                context_data=context_data,
                conversation_history=history
            )
            
            if not ai_response:
                # Friendly fallback with suggestion
                ai_response = (
                    "🤖 My brain just hiccuped. Give me 5 seconds and try again!\n"
                    "If this keeps happening, make sure Ollama is running (`ollama serve`) "
                    "and the model is pulled (`ollama pull " + OLLAMA_MODEL + "`)."
                )
            
            # Send response
            await message.reply(ai_response)
            
            # Update conversation history
            conversation_manager.add_message(user_id, 'user', user_question)
            conversation_manager.add_message(user_id, 'assistant', ai_response)
            
            # Extract and update context from question
            await update_context_from_question(user_id, user_question, context_data)
            
            logger.info(f"Successfully responded to {message.author}")
        
        except Exception as e:
            logger.error(f"Conversation handling failed: {e}", exc_info=True)
            error_msg = (
                "❌ Oops! Something went wrong. Try rephrasing your question or use `!reset` to start fresh."
            )
            await message.reply(error_msg)


async def update_context_from_question(user_id: str, question: str, data: Dict[str, Any]):
    """Update conversation context based on question and data"""
    question_lower = question.lower()
    
    # Extract project name if mentioned
    if 'projects' in data and data['projects']:
        # User likely asking about first project in results
        project_name = data['projects'][0].get('name')
        conversation_manager.update_context(user_id, project=project_name, topic='project_status')
    
    # Extract user name if mentioned
    common_names = ['john', 'jane', 'bob', 'alice', 'sarah', 'mike', 'tom']
    for name in common_names:
        if name in question_lower:
            conversation_manager.update_context(user_id, user=name.capitalize())
            break


async def send_scheduled_reports():
    """Send automated reports to Discord channel (only for enabled projects)"""
    logger.info("Starting scheduled report generation")
    
    # Check for configured channel ID first
    configured_channel_id = project_manager.get_config('report_channel_id')
    channel_id = int(configured_channel_id) if configured_channel_id else REPORT_CHANNEL_ID
    
    channel = bot.get_channel(channel_id)
    if not channel:
        logger.error(f"Report channel {REPORT_CHANNEL_ID} not found")
        return
    
    try:
        # Load enabled projects
        enabled_project_ids = load_enabled_projects()
        
        if not enabled_project_ids:
            logger.info("No projects enabled for scheduled reports. Use !enable <project_name> to enable.")
            return
        
        # Fetch all active projects
        projects = api_service.get_active_projects()
        
        if not projects:
            embed = report_builder.build_info_embed(
                "📊 Scheduled Report",
                "No active projects found."
            )
            await channel.send(embed=embed)
            logger.info("No active projects to report")
            return
        
        # Filter only enabled projects
        enabled_projects = [
            p for p in projects
            if (p.get('_id') or p.get('id')) in enabled_project_ids
        ]
        
        if not enabled_projects:
            logger.warning(f"No enabled projects found. Enabled IDs: {enabled_project_ids}")
            return
        
        logger.info(f"Sending reports for {len(enabled_projects)} enabled projects")
        
        # Generate report for each enabled project
        for project in enabled_projects:
            try:
                await send_project_report(channel, project, hours=12)
            except Exception as e:
                logger.error(f"Failed to generate report for project {project.get('id')}: {e}", exc_info=True)
                error_embed = report_builder.build_error_embed(
                    f"Failed to generate report for project: {project.get('name', 'Unknown')}\nError: {str(e)}"
                )
                await channel.send(embed=error_embed)
        
        logger.info(f"Completed scheduled reports for {len(enabled_projects)} projects")
        
    except Exception as e:
        logger.error(f"Failed to send scheduled reports: {e}", exc_info=True)
        error_embed = report_builder.build_error_embed(
            f"Failed to fetch projects from API: {str(e)}"
        )
        await channel.send(embed=error_embed)


async def poll_github_for_reviews():
    """🔄 Periodically check GitHub for new merged PRs and send code reviews via DM"""
    await bot.wait_until_ready()
    
    logger.info("🔍 GitHub polling loop started")
    
    while not bot.is_closed():
        try:
            # Check for newly merged PRs
            merged_prs = github_poll_service.get_recently_merged_prs(hours=1)
            
            if merged_prs:
                logger.info(f"🆕 Found {len(merged_prs)} new merged PRs!")
                
                for pr_info in merged_prs:
                    try:
                        # Fetch full PR data
                        pr_data = github_pr_service.get_pr_data(
                            pr_info['repo_name'],
                            pr_info['pr_number']
                        )
                        
                        if not pr_data:
                            logger.error(f"Failed to fetch PR data for {pr_info['repo_name']}#{pr_info['pr_number']}")
                            continue
                        
                        # Generate AI review
                        logger.info(f"🤖 Generating AI review for PR #{pr_data['number']}...")
                        ai_review = llm_service.review_code(pr_data)
                        
                        # Optional security scan
                        security_notes = None
                        if ai_review:
                            logger.info("🔒 Running security scan...")
                            security_notes = llm_service.security_scan(pr_data)
                        
                        # Determine recipient
                        recipient_id = await determine_review_recipient(pr_data)
                        
                        if recipient_id:
                            await send_code_review_dm(recipient_id, pr_data, ai_review, security_notes)
                        else:
                            await send_review_to_fallback(pr_data, ai_review, security_notes, pr_data.get('author'))
                    
                    except Exception as e:
                        logger.error(f"Failed to process PR {pr_info}: {e}", exc_info=True)
            
            # Wait before next check
            await asyncio.sleep(CODE_REVIEW_CHECK_INTERVAL)
        
        except Exception as e:
            logger.error(f"Error in GitHub polling loop: {e}", exc_info=True)
            await asyncio.sleep(CODE_REVIEW_CHECK_INTERVAL)


async def determine_review_recipient(pr_data: dict) -> Optional[int]:
    """Determine which Discord user should receive the code review DM"""
    
    if REVIEW_RECIPIENT_MODE == 'specific' and SPECIFIC_DISCORD_USER_ID:
        return SPECIFIC_DISCORD_USER_ID
    
    elif REVIEW_RECIPIENT_MODE == 'author':
        github_username = pr_data.get('author')
        return user_mapping_service.get_discord_id(github_username)
    
    elif REVIEW_RECIPIENT_MODE == 'owner':
        github_username = pr_data.get('repo_owner')
        return user_mapping_service.get_discord_id(github_username)
    
    return None


async def send_code_review_dm(user_id: int, pr_data: dict, ai_review: str, security_notes: str = None):
    """Send code review DM to a Discord user"""
    
    try:
        user = await bot.fetch_user(user_id)
        embed = code_review_builder.create_review_embed(pr_data, ai_review, security_notes)
        
        try:
            await user.send(embed=embed)
            logger.info(f"✅ Sent code review DM to {user.name} ({user_id})")
        
        except discord.Forbidden:
            logger.warning(f"⚠️ Cannot DM user {user_id} - Using fallback channel")
            await send_review_to_fallback(pr_data, ai_review, security_notes, pr_data.get('author'), user.mention)
    
    except Exception as e:
        logger.error(f"Failed to send DM to {user_id}: {e}")
        await send_review_to_fallback(pr_data, ai_review, security_notes, pr_data.get('author'))


async def send_review_to_fallback(pr_data: dict, ai_review: str, security_notes: str, github_username: str, user_mention: str = None):
    """Send code review to fallback channel when DM fails"""
    
    if not FALLBACK_CHANNEL_ID:
        logger.error("No fallback channel configured!")
        return
    
    try:
        channel = bot.get_channel(FALLBACK_CHANNEL_ID)
        if channel:
            embed = code_review_builder.create_fallback_embed(pr_data, ai_review, security_notes, github_username)
            mention = user_mention if user_mention else f"@{github_username}"
            await channel.send(content=f"{mention} Code review (DM failed):", embed=embed)
            logger.info(f"📢 Sent review to fallback channel for {github_username}")
    
    except Exception as e:
        logger.error(f"Failed to send to fallback channel: {e}")


async def send_project_report(channel, project: dict, hours: int = 12):
    """
    Send a report for a specific project
    
    Args:
        channel: Discord channel to send report to
        project: Project data dictionary
        hours: Number of hours to look back for stats
    """
    # Use _id field for project ID, fallback to id
    project_id = project.get('_id') or project.get('id')
    project_name = project.get('name', 'Unknown')
    
    logger.info(f"Generating report for project: {project_name}")
    
    if not project_id:
        logger.error(f"Project {project_name} has no ID")
        raise ValueError("Project ID is required")
    
    try:
        # Fetch all required data
        user_stats = api_service.get_user_stats(project_id, hours)
        incomplete_tasks = api_service.get_incomplete_tasks(project_id)
        recent_tasks = api_service.get_recent_tasks(hours)
        commits = api_service.get_recent_commits(project_id, hours)
        
        # Filter tasks for this project
        completed_tasks = [
            task for task in recent_tasks 
            if task.get('projectId') == project_id and task.get('status') == 'completed'
        ]
        
        # Build and send embed
        embed = report_builder.build_project_report(
            project=project,
            completed_tasks=completed_tasks,
            pending_tasks=incomplete_tasks,
            user_stats=user_stats,
            commits=commits,
            hours=hours
        )
        
        await channel.send(embed=embed)
        logger.info(f"Successfully sent report for project: {project_name}")
        
    except Exception as e:
        logger.error(f"Error generating report for {project_name}: {e}", exc_info=True)
        raise


@bot.command(name='help')
async def help_command(ctx):
    """Show available commands"""
    embed = report_builder.build_help_embed()
    await ctx.send(embed=embed)
    logger.info(f"Help command executed by {ctx.author}")


@bot.command(name='report')
async def manual_report(ctx):
    """Manually trigger a report (Admin only)"""
    # Check if user is admin
    if ADMIN_USER_IDS and ctx.author.id not in ADMIN_USER_IDS:
        await ctx.send("❌ You don't have permission to run this command.")
        logger.warning(f"Unauthorized report attempt by {ctx.author}")
        return
    
    await ctx.send("📊 Generating reports...")
    logger.info(f"Manual report triggered by {ctx.author}")
    
    try:
        await send_scheduled_reports()
        await ctx.send("✅ Reports sent successfully!")
    except Exception as e:
        logger.error(f"Manual report failed: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to generate reports: {str(e)}")


@bot.command(name='status')
async def project_status(ctx, *, project_name: Optional[str] = None):
    """Show current status of a project"""
    try:
        projects = api_service.get_active_projects()
        
        # Handle case where API returns non-list data
        if not isinstance(projects, list):
            await ctx.send("❌ Invalid response from API. Please check backend configuration.")
            logger.error(f"API returned non-list data: {type(projects)}")
            return
        
        if not projects:
            await ctx.send("❌ No active projects found.")
            return
        
        # If no project name provided, list all projects
        if not project_name:
            project_list = "\n".join([
                f"• **{p.get('name', 'Unknown')}**{' (Team: ' + p.get('teamCode') + ')' if p.get('teamCode') else ''}"
                for p in projects
            ])
            embed = report_builder.build_info_embed(
                "📋 Active Projects",
                f"Available projects:\n{project_list}\n\nUse `!status <project_name>` to get details."
            )
            await ctx.send(embed=embed)
            return
        
        # Find matching project
        project = next(
            (p for p in projects if p.get('name', '').lower() == project_name.lower()),
            None
        )
        
        if not project:
            await ctx.send(f"❌ Project '{project_name}' not found.")
            return
        
        # Send project report
        await send_project_report(ctx.channel, project, hours=12)
        logger.info(f"Status command executed by {ctx.author} for project {project_name}")
        
    except Exception as e:
        logger.error(f"Status command failed: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to fetch project status: {str(e)}")


@bot.command(name='mytasks')
async def my_tasks(ctx):
    """Show tasks assigned to the user with detailed information"""
    discord_id = str(ctx.author.id)
    
    try:
        # Fetch all recent tasks
        tasks = api_service.get_recent_tasks(hours=24 * 7)  # Last week
        
        # Handle case where API returns non-list data
        if not isinstance(tasks, list):
            await ctx.send("❌ Invalid response from API. Please check backend configuration.")
            logger.error(f"API returned non-list data: {type(tasks)}")
            return
        
        # Filter tasks assigned to this user (handle None assignees)
        my_tasks_list = [
            task for task in tasks 
            if task.get('assignee') and task.get('assignee').get('discordId') == discord_id
        ]
        
        if not my_tasks_list:
            await ctx.send(
                "📝 You have no tasks assigned.\n"
                "If this is incorrect, make sure your Discord account is linked using `!link <email>`"
            )
            return
        
        # Priority emoji and order
        priority_emoji = {
            'urgent': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        
        # Group tasks by priority
        priority_order = ['urgent', 'high', 'medium', 'low']
        tasks_by_priority = {p: [] for p in priority_order}
        
        for task in my_tasks_list:
            priority = task.get('priority', 'medium')
            if priority in tasks_by_priority:
                tasks_by_priority[priority].append(task)
            else:
                tasks_by_priority['medium'].append(task)  # Default to medium
        
        # Build embed
        embed = discord.Embed(
            title="📋 Your Assigned Tasks",
            description=f"Tasks for {ctx.author.mention}",
            color=0x0099FF
        )
        
        # Helper function to format task
        def format_task(task):
            title = task.get('title', 'Untitled')
            
            # Format due date
            due_date_str = "No due date"
            if task.get('dueDate'):
                try:
                    from datetime import datetime as dt
                    timestamp = task['dueDate'] / 1000  # Convert ms to seconds
                    due_date = dt.fromtimestamp(timestamp)
                    due_date_str = due_date.strftime('%b %d, %Y')
                except:
                    due_date_str = "Invalid date"
            
            # Format labels
            labels = task.get('labels', [])
            if labels and isinstance(labels, list) and len(labels) > 0:
                labels_str = ", ".join(labels)
            else:
                labels_str = "None"
            
            # Format project
            project_name = task.get('projectName', 'Unknown Project')
            
            return (
                f"• **{title}**\n"
                f"  📅 Due: {due_date_str}\n"
                f"  🏷️ Labels: {labels_str}\n"
                f"  📁 Project: {project_name}"
            )
        
        # Add tasks grouped by priority
        task_count = 0
        for priority in priority_order:
            priority_tasks = tasks_by_priority[priority]
            if priority_tasks:
                emoji = priority_emoji[priority]
                priority_name = priority.upper()
                
                tasks_text = "\n\n".join([format_task(t) for t in priority_tasks[:5]])
                
                embed.add_field(
                    name=f"{emoji} {priority_name}",
                    value=tasks_text,
                    inline=False
                )
                
                task_count += len(priority_tasks)
                
                # Add "more tasks" note if there are more than 5
                if len(priority_tasks) > 5:
                    embed.add_field(
                        name="",
                        value=f"_...and {len(priority_tasks) - 5} more {priority} tasks_",
                        inline=False
                    )
        
        # Add footer with total count
        embed.set_footer(text=f"Total: {task_count} task{'s' if task_count != 1 else ''}")
        
        await ctx.send(embed=embed)
        logger.info(f"MyTasks command executed by {ctx.author} - {task_count} tasks")
        
    except Exception as e:
        logger.error(f"MyTasks command failed: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to fetch your tasks: {str(e)}")


@bot.command(name='link')
async def link_account(ctx, email: str):
    """Link Discord account to web app account"""
    discord_id = str(ctx.author.id)
    
    try:
        result = api_service.link_discord_user(discord_id, email)
        
        embed = report_builder.build_success_embed(
            f"Successfully linked your Discord account to {email}!\n"
            f"You can now use `!mytasks` to see your assigned tasks."
        )
        await ctx.send(embed=embed)
        logger.info(f"Account linked: {ctx.author} -> {email}")
        
    except Exception as e:
        logger.error(f"Link command failed: {e}", exc_info=True)
        await ctx.send(
            f"❌ Failed to link account: {str(e)}\n"
            f"Make sure the email is registered in the web app."
        )


@bot.command(name='ping')
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency: {latency}ms")


@bot.command(name='enable')
async def enable_reports(ctx, *, project_name: str):
    """📢 Enable scheduled reports for a specific project"""
    try:
        # Fetch all projects
        projects = api_service.get_active_projects()
        
        if not isinstance(projects, list):
            await ctx.send("❌ Invalid response from API. Please check backend configuration.")
            return
        
        # Find matching project (case-insensitive)
        project = next(
            (p for p in projects if p.get('name', '').lower() == project_name.lower()),
            None
        )
        
        if not project:
            await ctx.send(
                f"❌ Project '{project_name}' not found.\n"
                f"Use `!status` to see available projects."
            )
            return
        
        project_id = project.get('_id') or project.get('id')
        if not project_id:
            await ctx.send("❌ Project has no ID.")
            return
        
        # Load current enabled projects
        enabled = load_enabled_projects()
        
        # Check if already enabled
        if project_id in enabled:
            await ctx.send(f"ℹ️ Reports for **{project.get('name')}** are already enabled!")
            return
        
        # Add to enabled list
        enabled.append(project_id)
        save_enabled_projects(enabled)
        
        
        embed = discord.Embed(
            title="✅ Reports Enabled",
            description=f"Scheduled reports are now **enabled** for:\n📊 **{project.get('name')}**",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        logger.info(f"Enabled reports for {project.get('name')} by {ctx.author}")
        
    except Exception as e:
        logger.error(f"Enable command failed: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to enable reports: {str(e)}")


# --- Local Project Management Commands ---

@bot.command(name='p_create')
async def create_local_project(ctx, name: str, *, description: str = ""):
    """Create a new local project"""
    try:
        project = project_manager.create_project(name, description)
        await ctx.send(f"✅ Project **{project['name']}** created successfully!")
        logger.info(f"Local project created: {name} by {ctx.author}")
    except Exception as e:
        logger.error(f"Failed to create local project: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to create project: {str(e)}")


@bot.command(name='p_list')
async def list_local_projects(ctx):
    """List all local projects"""
    try:
        projects = project_manager.get_projects()
        if not projects:
            await ctx.send("📝 No local projects found. Create one with `!p_create <name>`")
            return

        embed = discord.Embed(
            title="📂 Local Projects",
            color=0x0099FF
        )
        
        for p in projects:
            task_count = len(p.get('tasks', []))
            embed.add_field(
                name=p['name'],
                value=f"{p.get('description', 'No description')}\nTasks: {task_count}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Failed to list local projects: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to list projects: {str(e)}")


@bot.command(name='t_add')
async def add_local_task(ctx, project_name: str, title: str, due_date: str = None):
    """Add a task to a local project"""
    try:
        project = project_manager.get_project_by_name(project_name)
        if not project:
            await ctx.send(f"❌ Project '{project_name}' not found.")
            return

        task = project_manager.add_task(project['id'], title, str(ctx.author.id), due_date)
        if task:
            await ctx.send(f"✅ Task **{task['title']}** added to **{project['name']}**!")
        else:
            await ctx.send("❌ Failed to add task.")
            
    except Exception as e:
        logger.error(f"Failed to add local task: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to add task: {str(e)}")


@bot.command(name='t_list')
async def list_local_tasks(ctx, project_name: str):
    """List tasks for a local project"""
    try:
        project = project_manager.get_project_by_name(project_name)
        if not project:
            await ctx.send(f"❌ Project '{project_name}' not found.")
            return

        tasks = project_manager.get_tasks(project['id'])
        if not tasks:
            await ctx.send(f"📝 No tasks found for **{project['name']}**.")
            return

        embed = discord.Embed(
            title=f"📋 Tasks for {project['name']}",
            color=0x0099FF
        )

        status_emoji = {
            'todo': '⬜',
            'in_progress': '🔄',
            'done': '✅'
        }

        for task in tasks:
            status = task.get('status', 'todo')
            emoji = status_emoji.get(status, '❓')
            assignee = f"<@{task['assignee_id']}>" if task.get('assignee_id') else "Unassigned"
            
            embed.add_field(
                name=f"{emoji} {task['title']}",
                value=f"ID: `{task['id']}`\nStatus: {status}\nAssignee: {assignee}",
                inline=False
            )

        await ctx.send(embed=embed)

    except Exception as e:
        logger.error(f"Failed to list local tasks: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to list tasks: {str(e)}")


@bot.command(name='t_status')
async def update_task_status(ctx, task_id: str, status: str):
    """Update task status (todo, in_progress, done)"""
    try:
        if project_manager.update_task_status(task_id, status):
            await ctx.send(f"✅ Task `{task_id}` status updated to **{status}**!")
        else:
            await ctx.send(f"❌ Failed to update task. Check ID and status (todo, in_progress, done).")
    except Exception as e:
        logger.error(f"Failed to update task status: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to update task: {str(e)}")


@bot.command(name='t_assign')
async def assign_local_task(ctx, task_id: str, user: discord.User):
    """Assign a task to a user"""
    try:
        if project_manager.assign_task(task_id, str(user.id)):
            await ctx.send(f"✅ Task `{task_id}` assigned to {user.mention}!")
        else:
            await ctx.send(f"❌ Failed to assign task. Check ID.")
    except Exception as e:
        logger.error(f"Failed to assign task: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to assign task: {str(e)}")


@bot.command(name='set_channel')
async def set_report_channel(ctx, channel_id: str):
    """Set the channel for reports (Admin only)"""
    # Check if user is admin
    if ADMIN_USER_IDS and ctx.author.id not in ADMIN_USER_IDS:
        await ctx.send("❌ You don't have permission to run this command.")
        return

    try:
        # Validate channel ID
        try:
            c_id = int(channel_id)
            channel = bot.get_channel(c_id)
            if not channel:
                await ctx.send(f"❌ Bot cannot find channel with ID {channel_id}. Make sure I'm in that server!")
                return
        except ValueError:
            await ctx.send("❌ Invalid channel ID. Please provide a number.")
            return

        project_manager.set_config('report_channel_id', str(c_id))
        await ctx.send(f"✅ Report channel set to {channel.mention} (ID: {c_id})")
        logger.info(f"Report channel set to {c_id} by {ctx.author}")
        
    except Exception as e:
        logger.error(f"Failed to set channel: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to set channel: {str(e)}")

        embed.add_field(
            name="🔔 Report Schedule",
            value=f"Reports will be sent at **8 AM** and **8 PM IST** daily.",
            inline=False
        )
        embed.set_footer(text="Use !disable <project_name> to turn off reports")
        
        await ctx.send(embed=embed)
        logger.info(f"Enabled reports for project: {project.get('name')} ({project_id})")
        
    except Exception as e:
        logger.error(f"Enable command failed: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to enable reports: {str(e)}")


@bot.command(name='disable')
async def disable_reports(ctx, *, project_name: str):
    """🔕 Disable scheduled reports for a specific project"""
    try:
        # Fetch all projects
        projects = api_service.get_active_projects()
        
        if not isinstance(projects, list):
            await ctx.send("❌ Invalid response from API. Please check backend configuration.")
            return
        
        # Find matching project
        project = next(
            (p for p in projects if p.get('name', '').lower() == project_name.lower()),
            None
        )
        
        if not project:
            await ctx.send(
                f"❌ Project '{project_name}' not found.\n"
                f"Use `!status` to see available projects."
            )
            return
        
        project_id = project.get('_id') or project.get('id')
        if not project_id:
            await ctx.send("❌ Project has no ID.")
            return
        
        # Load current enabled projects
        enabled = load_enabled_projects()
        
        # Check if already disabled
        if project_id not in enabled:
            await ctx.send(f"ℹ️ Reports for **{project.get('name')}** are already disabled!")
            return
        
        # Remove from enabled list
        enabled.remove(project_id)
        save_enabled_projects(enabled)
        
        embed = discord.Embed(
            title="🔕 Reports Disabled",
            description=f"Scheduled reports are now **disabled** for:\n📊 **{project.get('name')}**",
            color=0xFF9900
        )
        embed.set_footer(text="Use !enable <project_name> to turn on reports")
        
        await ctx.send(embed=embed)
        logger.info(f"Disabled reports for project: {project.get('name')} ({project_id})")
        
    except Exception as e:
        logger.error(f"Disable command failed: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to disable reports: {str(e)}")


@bot.command(name='enabled')
async def list_enabled(ctx):
    """📊 List all projects with scheduled reports enabled"""
    try:
        # Load enabled project IDs
        enabled_ids = load_enabled_projects()
        
        if not enabled_ids:
            await ctx.send(
                "📄 No projects have scheduled reports enabled.\n"
                "Use `!enable <project_name>` to enable reports for a project."
            )
            return
        
        # Fetch all projects to get names
        projects = api_service.get_active_projects()
        
        if not isinstance(projects, list):
            await ctx.send("❌ Failed to fetch project list.")
            return
        
        # Filter enabled projects
        enabled_projects = [
            p for p in projects
            if (p.get('_id') or p.get('id')) in enabled_ids
        ]
        
        if not enabled_projects:
            await ctx.send("❌ No matching projects found for enabled IDs.")
            return
        
        # Build embed
        project_list = "\n".join([
            f"• **{p.get('name', 'Unknown')}**{' (Team: ' + p.get('teamCode') + ')' if p.get('teamCode') else ''}"
            for p in enabled_projects
        ])
        
        embed = discord.Embed(
            title="📢 Enabled Scheduled Reports",
            description=f"Reports active for **{len(enabled_projects)}** project(s):\n\n{project_list}",
            color=0x0099FF
        )
        embed.add_field(
            name="🔔 Schedule",
            value="Reports sent daily at **8 AM** and **8 PM IST**",
            inline=False
        )
        embed.set_footer(text="Use !enable / !disable <project_name> to manage")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Enabled command failed: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to list enabled projects: {str(e)}")


@bot.command(name='map-user')
async def map_user(ctx, github_username: str, discord_user: discord.User):
    """🔗 Map a GitHub username to a Discord user for code reviews
    
    Usage: !map-user <github_username> @DiscordUser
    Example: !map-user john_github @JohnDoe
    """
    try:
        # Add mapping
        success = user_mapping_service.add_mapping(github_username, discord_user.id)
        
        if success:
            embed = code_review_builder.create_mapping_added_embed(github_username, discord_user.id)
            embed.add_field(
                name="Discord User",
                value=discord_user.mention,
                inline=False
            )
            await ctx.send(embed=embed)
            logger.info(f"User mapping added by {ctx.author}: {github_username} -> {discord_user.id}")
        else:
            await ctx.send("❌ Failed to add user mapping.")
    
    except Exception as e:
        logger.error(f"Map-user command failed: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to add mapping: {str(e)}")


@bot.command(name='unmap-user')
async def unmap_user(ctx, github_username: str):
    """🔓 Remove a GitHub to Discord user mapping
    
    Usage: !unmap-user <github_username>
    """
    try:
        success = user_mapping_service.remove_mapping(github_username)
        
        if success:
            embed = discord.Embed(
                title="✅ User Mapping Removed",
                description=f"Removed mapping for GitHub user `{github_username}`",
                color=0x00FF00
            )
            await ctx.send(embed=embed)
            logger.info(f"User mapping removed by {ctx.author}: {github_username}")
        else:
            await ctx.send(f"❌ No mapping found for `{github_username}`.")
    
    except Exception as e:
        logger.error(f"Unmap-user command failed: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to remove mapping: {str(e)}")


@bot.command(name='list-mappings')
async def list_mappings(ctx):
    """📋 List all GitHub to Discord user mappings"""
    try:
        mappings = user_mapping_service.get_all_mappings()
        
        if not mappings:
            await ctx.send("📄 No user mappings configured yet.\nUse `!map-user <github_username> @DiscordUser` to add one.")
            return
        
        embed = discord.Embed(
            title="🔗 GitHub → Discord User Mappings",
            description=f"Total mappings: **{len(mappings)}**",
            color=0x0099FF
        )
        
        # Show mappings
        mapping_text = "\n".join([
            f"• `{github}` → `{discord_id}`"
            for github, discord_id in list(mappings.items())[:20]  # Limit to 20
        ])
        
        if len(mappings) > 20:
            mapping_text += f"\n... and {len(mappings) - 20} more"
        
        embed.add_field(
            name="Mappings",
            value=mapping_text,
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    except Exception as e:
        logger.error(f"List-mappings command failed: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to list mappings: {str(e)}")


@bot.command(name='reset')
async def reset_conversation(ctx):
    """🔄 Reset your conversation history with the AI"""
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("⚠️ This command only works in DMs!")
        return
    
    try:
        user_id = str(ctx.author.id)
        conversation_manager.reset_conversation(user_id)
        
        embed = discord.Embed(
            title="🔄 Conversation Reset",
            description="Your conversation history has been cleared!\n\nStart fresh by asking me anything about your projects.",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        logger.info(f"Reset conversation for {ctx.author}")
    
    except Exception as e:
        logger.error(f"Reset command failed: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to reset conversation: {str(e)}")


@bot.command(name='context')
async def show_context(ctx):
    """🧠 Show what the AI remembers about your conversation"""
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("⚠️ This command only works in DMs!")
        return
    
    try:
        user_id = str(ctx.author.id)
        context_summary = conversation_manager.get_context_summary(user_id)
        
        embed = discord.Embed(
            title="🧠 Conversation Context",
            description=context_summary,
            color=0x0099FF
        )
        
        history = conversation_manager.get_history(user_id)
        if history:
            embed.add_field(
                name="💬 Messages",
                value=f"{len(history)} messages in history",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    except Exception as e:
        logger.error(f"Context command failed: {e}", exc_info=True)
        await ctx.send(f"❌ Failed to show context: {str(e)}")


@bot.command(name='help-chat')
async def help_chat(ctx):
    """🎓 Show example questions for the conversational AI"""
    embed = discord.Embed(
        title="🤖 Chat with PM Bot",
        description="Just DM me naturally! No commands needed.",
        color=0x0099FF
    )
    
    embed.add_field(
        name="📊 Project Status",
        value=(
            "• How's the mobile app going?\n"
            "• What's the progress on Project X?\n"
            "• Show me pending tasks"
        ),
        inline=False
    )
    
    embed.add_field(
        name="👥 Team Questions",
        value=(
            "• What's John working on?\n"
            "• Who's assigned to the mobile app?\n"
            "• Show me Sarah's tasks"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📅 Deadlines",
        value=(
            "• What's due this week?\n"
            "• Are we on track for Friday?\n"
            "• Any overdue tasks?"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🛠️ Utilities",
        value=(
            "`!reset` - Clear conversation history\n"
            "`!context` - Show what I remember\n"
            "`!help-chat` - Show this help"
        ),
        inline=False
    )
    
    embed.set_footer(text="👉 Just send me a DM and start chatting!")
    
    await ctx.send(embed=embed)


# Health check endpoint for keeping Render awake
async def health_check(request):
    """Simple health check endpoint - returns minimal response"""
    return web.Response(text="", status=200)


async def start_health_server():
    """Start a simple web server for health checks"""
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    
    # Disable access logs to prevent output during health checks
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()


def main():
    """Main entry point"""
    if not DISCORD_TOKEN:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables")
        print("❌ Error: DISCORD_BOT_TOKEN not set in .env file")
        sys.exit(1)
    
    if not REPORT_CHANNEL_ID:
        logger.error("REPORT_CHANNEL_ID not found in environment variables")
        print("❌ Error: REPORT_CHANNEL_ID not set in .env file")
        sys.exit(1)
    
    try:
        logger.info("Starting Discord bot...")
        
        # Start health check server in background
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(start_health_server())
        
        # Run bot
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        scheduler.stop()
        logger.info("Bot shut down")


if __name__ == "__main__":
    main()
