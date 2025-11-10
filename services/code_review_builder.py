import discord
from typing import Dict, Any, Optional
from datetime import datetime


class CodeReviewBuilder:
    """Build formatted Discord embeds for code reviews"""
    
    def create_review_embed(
        self,
        pr_data: Dict[str, Any],
        ai_review: Optional[str],
        security_notes: Optional[str] = None
    ) -> discord.Embed:
        """
        Create a comprehensive code review embed for DM
        
        Args:
            pr_data: Pull request data from GitHub
            ai_review: AI-generated code review
            security_notes: Optional security analysis
        
        Returns:
            Discord Embed object
        """
        # Determine color based on security findings
        if security_notes and ('CRITICAL' in security_notes or 'HIGH' in security_notes):
            color = 0xFF0000  # Red for security issues
        elif ai_review and 'reject' in ai_review.lower():
            color = 0xFF9900  # Orange for rejection
        else:
            color = 0x00FF00  # Green for approval
        
        embed = discord.Embed(
            title=f"🤖 Code Review: PR #{pr_data.get('number')}",
            description=f"**{pr_data.get('title')}**",
            color=color,
            url=pr_data.get('html_url'),
            timestamp=datetime.utcnow()
        )
        
        # Repository info
        embed.add_field(
            name="📦 Repository",
            value=f"`{pr_data.get('repo_name')}`",
            inline=True
        )
        
        # Author
        embed.add_field(
            name="👤 Author",
            value=f"`{pr_data.get('author')}`",
            inline=True
        )
        
        # Status
        status_emoji = "✅" if pr_data.get('merged') else "⏳"
        embed.add_field(
            name="📊 Status",
            value=f"{status_emoji} {'Merged' if pr_data.get('merged') else 'Open'}",
            inline=True
        )
        
        # Statistics
        stats_text = (
            f"📁 **Files:** {pr_data.get('files_changed', 0)}\n"
            f"➕ **Added:** {pr_data.get('additions', 0)} lines\n"
            f"➖ **Removed:** {pr_data.get('deletions', 0)} lines\n"
            f"💾 **Commits:** {pr_data.get('commits', 0)}"
        )
        embed.add_field(
            name="📈 Changes",
            value=stats_text,
            inline=False
        )
        
        # PR Description (truncated)
        description = pr_data.get('description', 'No description')
        if len(description) > 200:
            description = description[:200] + "..."
        embed.add_field(
            name="📝 Description",
            value=description,
            inline=False
        )
        
        # AI Review
        if ai_review:
            # Truncate if too long for Discord
            review_text = ai_review
            if len(review_text) > 1024:
                review_text = review_text[:1021] + "..."
            
            embed.add_field(
                name="🔍 AI Code Review",
                value=review_text,
                inline=False
            )
        else:
            embed.add_field(
                name="🔍 AI Code Review",
                value="⚠️ Review generation failed",
                inline=False
            )
        
        # Security Analysis
        if security_notes:
            security_text = security_notes
            if len(security_text) > 1024:
                security_text = security_text[:1021] + "..."
            
            embed.add_field(
                name="🔒 Security Analysis",
                value=security_text,
                inline=False
            )
        
        # Changed files (limited)
        if pr_data.get('diffs'):
            files_list = []
            for file_diff in pr_data['diffs'][:10]:  # Show max 10 files
                filename = file_diff.get('filename', 'unknown')
                status = file_diff.get('status', '')
                status_emoji = {'added': '➕', 'modified': '📝', 'removed': '➖'}.get(status, '📄')
                files_list.append(f"{status_emoji} `{filename}`")
            
            files_text = '\n'.join(files_list)
            if len(pr_data['diffs']) > 10:
                files_text += f"\n... and {len(pr_data['diffs']) - 10} more files"
            
            embed.add_field(
                name="📂 Changed Files",
                value=files_text,
                inline=False
            )
        
        # Footer with privacy notice
        embed.set_footer(
            text="🔐 This review was sent privately • Not visible to others",
            icon_url="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
        )
        
        return embed
    
    def create_fallback_embed(
        self,
        pr_data: Dict[str, Any],
        ai_review: Optional[str],
        security_notes: Optional[str],
        github_username: str
    ) -> discord.Embed:
        """Create embed for fallback channel when DM fails"""
        embed = self.create_review_embed(pr_data, ai_review, security_notes)
        
        # Update footer to indicate this is a fallback
        embed.set_footer(
            text=f"⚠️ Could not DM user {github_username} • Posted here instead"
        )
        
        return embed
    
    def create_error_embed(self, error_message: str) -> discord.Embed:
        """Create an error notification embed"""
        embed = discord.Embed(
            title="❌ Code Review Failed",
            description=error_message,
            color=0xFF0000,
            timestamp=datetime.utcnow()
        )
        return embed
    
    def create_mapping_added_embed(self, github_username: str, discord_user_id: int) -> discord.Embed:
        """Create confirmation embed for adding user mapping"""
        embed = discord.Embed(
            title="✅ User Mapping Added",
            description=f"Successfully mapped GitHub user to Discord user",
            color=0x00FF00
        )
        embed.add_field(
            name="GitHub Username",
            value=f"`{github_username}`",
            inline=True
        )
        embed.add_field(
            name="Discord User ID",
            value=f"`{discord_user_id}`",
            inline=True
        )
        return embed
