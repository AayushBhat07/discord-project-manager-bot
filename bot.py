import discord
from discord.ext import commands
import logging
import sys
import asyncio
import ssl
from typing import Optional
from datetime import datetime

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


@bot.event
async def on_ready():
    """Event handler for when bot is ready"""
    logger.info(f'Bot connected as {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Connected to {len(bot.guilds)} guilds')
    
    # Schedule automated reports
    scheduler.schedule_reports(send_scheduled_reports, REPORT_HOURS)
    scheduler.start()
    
    logger.info(f"Bot is ready! Next report in: {scheduler.get_next_run_time()}")
    
    # Send welcome message to report channel
    channel = bot.get_channel(REPORT_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🤖 Project Manager Bot Online",
            description="Your automated project reporting assistant is now active!",
            color=0x00FF00,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📊 Automated Reports",
            value=f"Reports will be sent every 12 hours at **{', '.join([f'{h}:00' for h in REPORT_HOURS])} IST**",
            inline=False
        )
        
        embed.add_field(
            name="⏰ Next Report",
            value=f"In **{scheduler.get_next_run_time()}**",
            inline=True
        )
        
        embed.add_field(
            name="📋 Commands",
            value="Type `!help` to see all available commands",
            inline=True
        )
        
        embed.set_footer(text="Monitoring your projects 24/7")
        
        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")


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
    """Send automated reports to Discord channel"""
    logger.info("Starting scheduled report generation")
    
    channel = bot.get_channel(REPORT_CHANNEL_ID)
    if not channel:
        logger.error(f"Report channel {REPORT_CHANNEL_ID} not found")
        return
    
    try:
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
        
        # Generate report for each project
        for project in projects:
            try:
                await send_project_report(channel, project, hours=12)
            except Exception as e:
                logger.error(f"Failed to generate report for project {project.get('id')}: {e}", exc_info=True)
                error_embed = report_builder.build_error_embed(
                    f"Failed to generate report for project: {project.get('name', 'Unknown')}\nError: {str(e)}"
                )
                await channel.send(embed=error_embed)
        
        logger.info(f"Completed scheduled reports for {len(projects)} projects")
        
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
    """Show tasks assigned to the user"""
    discord_id = str(ctx.author.id)
    
    try:
        # Fetch all recent tasks
        tasks = api_service.get_recent_tasks(hours=24 * 7)  # Last week
        
        # Handle case where API returns non-list data
        if not isinstance(tasks, list):
            await ctx.send("❌ Invalid response from API. Please check backend configuration.")
            logger.error(f"API returned non-list data: {type(tasks)}")
            return
        
        # Filter tasks assigned to this user
        my_tasks_list = [
            task for task in tasks 
            if task.get('assignee', {}).get('discordId') == discord_id
        ]
        
        if not my_tasks_list:
            await ctx.send(
                "📝 You have no tasks assigned.\n"
                "If this is incorrect, make sure your Discord account is linked using `!link <email>`"
            )
            return
        
        # Build embed
        embed = discord.Embed(
            title=f"📝 Your Tasks",
            description=f"Tasks assigned to {ctx.author.mention}",
            color=0x0099FF
        )
        
        pending = [t for t in my_tasks_list if t.get('status') != 'completed']
        completed = [t for t in my_tasks_list if t.get('status') == 'completed']
        
        if pending:
            pending_text = "\n".join([
                f"• **{t.get('title')}** - {t.get('status')}"
                for t in pending[:10]
            ])
            embed.add_field(name="⏳ Pending", value=pending_text, inline=False)
        
        if completed:
            completed_text = "\n".join([
                f"• {t.get('title')}"
                for t in completed[:5]
            ])
            embed.add_field(name="✅ Recently Completed", value=completed_text, inline=False)
        
        await ctx.send(embed=embed)
        logger.info(f"MyTasks command executed by {ctx.author}")
        
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
