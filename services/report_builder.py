import discord
import logging
from typing import List, Dict, Optional
from datetime import datetime
from config import COLORS, EMOJIS

logger = logging.getLogger(__name__)


class ReportBuilder:
    """Builds Discord embeds for project reports"""
    
    @staticmethod
    def build_project_report(
        project: Dict,
        completed_tasks: List[Dict],
        pending_tasks: List[Dict],
        user_stats: List[Dict],
        commits: List[Dict],
        hours: int = 12
    ) -> discord.Embed:
        """Build a comprehensive project status report embed"""
        
        project_name = project.get('name', 'Unknown Project')
        
        # Calculate statistics
        total_completed = len(completed_tasks)
        total_pending = len(pending_tasks)
        total_tasks = total_completed + total_pending
        completion_rate = (total_completed / total_tasks * 100) if total_tasks > 0 else 0
        
        # Create embed
        embed = discord.Embed(
            title=f"╔═══ PROJECT STATUS REPORT ═══╗",
            description=f"**{EMOJIS['project']} PROJECT: {project_name}**\n{'━' * 30}",
            color=COLORS['primary'],
            timestamp=datetime.utcnow()
        )
        
        # Task Summary
        summary = (
            f"{EMOJIS['completed']} **COMPLETED TASKS (Last {hours}h):** {total_completed}\n"
            f"{EMOJIS['pending']} **PENDING TASKS:** {total_pending}\n"
            f"{EMOJIS['stats']} **Completion Rate:** {completion_rate:.1f}%"
        )
        embed.add_field(name="", value=summary, inline=False)
        embed.add_field(name="", value=f"{'━' * 30}", inline=False)
        
        # Team Performance
        if user_stats:
            team_performance = ReportBuilder._format_team_performance(user_stats)
            embed.add_field(
                name=f"{EMOJIS['team']} TEAM PERFORMANCE",
                value=team_performance,
                inline=False
            )
            embed.add_field(name="", value=f"{'━' * 30}", inline=False)
        
        # Pending Tasks
        if pending_tasks:
            pending_text = ReportBuilder._format_pending_tasks(pending_tasks)
            embed.add_field(
                name=f"{EMOJIS['urgent']} PENDING TASKS (Needs Attention)",
                value=pending_text,
                inline=False
            )
            embed.add_field(name="", value=f"{'━' * 30}", inline=False)
        
        # GitHub Activity
        if commits:
            commit_summary = ReportBuilder._format_commits(commits)
            embed.add_field(
                name=f"{EMOJIS['commits']} GITHUB ACTIVITY ({len(commits)} commits)",
                value=commit_summary,
                inline=False
            )
            embed.add_field(name="", value=f"{'━' * 30}", inline=False)
        
        # Footer
        embed.set_footer(text=f"⏰ Next report in {hours} hours")
        
        return embed
    
    @staticmethod
    def _format_team_performance(user_stats: List[Dict]) -> str:
        """Format team performance section"""
        # Sort by tasks completed (descending)
        sorted_stats = sorted(user_stats, key=lambda x: x.get('completed', 0), reverse=True)
        
        lines = []
        for i, stat in enumerate(sorted_stats[:5]):  # Top 5 users
            username = stat.get('username', 'Unknown')
            completed = stat.get('completed', 0)
            emoji = EMOJIS['top_performer'] if i == 0 else EMOJIS['completed']
            lines.append(f"{emoji} **{username}** {completed} tasks completed")
        
        return '\n'.join(lines) if lines else "No activity in this period"
    
    @staticmethod
    def _format_pending_tasks(pending_tasks: List[Dict]) -> str:
        """Format pending tasks section with mentions"""
        lines = []
        
        for task in pending_tasks[:10]:  # Show max 10 tasks
            title = task.get('title', 'Untitled task')
            priority = task.get('priority', 'NORMAL').upper()
            assignee = task.get('assignee', {})
            discord_id = assignee.get('discordId')
            username = assignee.get('username', 'Unassigned')
            
            # Priority emoji
            priority_emoji = EMOJIS['urgent'] if priority in ['HIGH', 'URGENT'] else '•'
            
            # Mention user if Discord ID is available
            if discord_id:
                user_mention = f"<@{discord_id}>"
            else:
                user_mention = username
            
            priority_text = f"[{priority}]" if priority in ['HIGH', 'URGENT'] else ""
            lines.append(f"{priority_emoji} **{title}** {priority_text} - {user_mention}")
        
        if len(pending_tasks) > 10:
            lines.append(f"\n_...and {len(pending_tasks) - 10} more tasks_")
        
        return '\n'.join(lines) if lines else "No pending tasks"
    
    @staticmethod
    def _format_commits(commits: List[Dict]) -> str:
        """Format GitHub commits section"""
        # Calculate total changes
        total_additions = sum(c.get('additions', 0) for c in commits)
        total_deletions = sum(c.get('deletions', 0) for c in commits)
        
        lines = [f"**+{total_additions} lines | -{total_deletions} lines**\n"]
        lines.append("Recent commits:")
        
        for commit in commits[:3]:  # Show last 3 commits
            sha = commit.get('sha', 'unknown')[:7]
            author = commit.get('author', 'Unknown')
            message = commit.get('message', 'No message')
            timestamp = commit.get('timestamp', '')
            
            # Truncate message if too long
            if len(message) > 50:
                message = message[:47] + "..."
            
            lines.append(f"• `{sha}` @{author} \"{message}\" ({timestamp})")
        
        if len(commits) > 3:
            lines.append(f"\n_...and {len(commits) - 3} more commits_")
        
        return '\n'.join(lines)
    
    @staticmethod
    def build_error_embed(error_message: str) -> discord.Embed:
        """Build an error notification embed"""
        embed = discord.Embed(
            title="❌ Error",
            description=error_message,
            color=COLORS['error'],
            timestamp=datetime.utcnow()
        )
        return embed
    
    @staticmethod
    def build_success_embed(message: str) -> discord.Embed:
        """Build a success notification embed"""
        embed = discord.Embed(
            title="✅ Success",
            description=message,
            color=COLORS['success'],
            timestamp=datetime.utcnow()
        )
        return embed
    
    @staticmethod
    def build_info_embed(title: str, message: str) -> discord.Embed:
        """Build an info notification embed"""
        embed = discord.Embed(
            title=title,
            description=message,
            color=COLORS['info'],
            timestamp=datetime.utcnow()
        )
        return embed
    
    @staticmethod
    def build_help_embed() -> discord.Embed:
        """Build help command embed"""
        embed = discord.Embed(
            title="🤖 Discord Bot Commands",
            description="Available commands for project management bot",
            color=COLORS['primary']
        )
        
        commands = [
            ("!status [project_name]", "Show current status of a project"),
            ("!mytasks", "Show tasks assigned to you (requires linking)"),
            ("!report", "Trigger a manual report (Admin only)"),
            ("!link <email>", "Link your Discord account to web app account"),
            ("!help", "Show this help message"),
        ]
        
        for cmd, desc in commands:
            embed.add_field(name=cmd, value=desc, inline=False)
        
        embed.set_footer(text="Use !link to connect your Discord account for personalized features")
        
        return embed
