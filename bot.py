import discord
from discord.ext import commands
import logging
import sys
import asyncio
import ssl
import random
import json
import os
from typing import Optional, List
from datetime import datetime
from aiohttp import web

from config import (
    DISCORD_TOKEN, REPORT_CHANNEL_ID, COMMAND_PREFIX,
    API_BASE_URL, REPORT_HOURS, TIMEZONE, ADMIN_USER_IDS
)
from services.api_service import APIService
from services.report_builder import ReportBuilder
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


async def send_scheduled_reports():
    """Send automated reports to Discord channel (only for enabled projects)"""
    logger.info("Starting scheduled report generation")
    
    channel = bot.get_channel(REPORT_CHANNEL_ID)
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
