import discord
import logging
import os
from typing import Dict, Any

from services.github_pr_service import GitHubPRService
from services.local_llm_service import LocalLLMService
from services.code_review_builder import CodeReviewBuilder
from services.user_mapping_service import UserMappingService

logger = logging.getLogger(__name__)


class GitHubWebhookHandler:
    """Handle GitHub webhook events and send code reviews via DM"""
    
    def __init__(
        self,
        bot: discord.Client,
        github_service: GitHubPRService,
        llm_service: LocalLLMService,
        review_builder: CodeReviewBuilder,
        user_mapping: UserMappingService,
        recipient_mode: str,
        specific_user_id: int = None,
        fallback_channel_id: int = None
    ):
        self.bot = bot
        self.github_service = github_service
        self.llm_service = llm_service
        self.review_builder = review_builder
        self.user_mapping = user_mapping
        self.recipient_mode = recipient_mode
        self.specific_user_id = specific_user_id
        self.fallback_channel_id = fallback_channel_id
    
    async def handle_pr_merged(
        self,
        repo_full_name: str,
        pr_number: int,
        webhook_payload: Dict[str, Any]
    ):
        """
        Handle a merged PR event
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            pr_number: PR number
            webhook_payload: Full GitHub webhook payload
        """
        try:
            logger.info(f"Processing merged PR #{pr_number} from {repo_full_name}")
            
            # Step 1: Fetch PR data from GitHub
            pr_data = self.github_service.get_pr_data(repo_full_name, pr_number)
            if not pr_data:
                logger.error("Failed to fetch PR data from GitHub")
                await self._send_error_notification("Failed to fetch PR data from GitHub")
                return
            
            # Step 2: Generate AI code review
            logger.info("Generating AI code review...")
            ai_review = self.llm_service.review_code(pr_data)
            
            # Step 3: Optional security scan
            security_notes = None
            if ai_review:  # Only run security scan if main review succeeded
                logger.info("Running security analysis...")
                security_notes = self.llm_service.security_scan(pr_data)
            
            # Step 4: Determine recipient
            recipient_user_id = await self._determine_recipient(pr_data)
            
            if not recipient_user_id:
                logger.warning(f"No recipient found for PR author {pr_data.get('author')}")
                await self._send_to_fallback_channel(pr_data, ai_review, security_notes, pr_data.get('author'))
                return
            
            # Step 5: Send DM to recipient
            await self._send_review_dm(recipient_user_id, pr_data, ai_review, security_notes)
            
        except Exception as e:
            logger.error(f"Failed to handle PR webhook: {e}", exc_info=True)
            await self._send_error_notification(f"Webhook processing failed: {str(e)}")
    
    async def _determine_recipient(self, pr_data: Dict[str, Any]) -> int:
        """Determine which Discord user should receive the review DM"""
        
        if self.recipient_mode == 'specific' and self.specific_user_id:
            # Always send to specific user
            logger.info(f"Using specific recipient mode: {self.specific_user_id}")
            return self.specific_user_id
        
        elif self.recipient_mode == 'author':
            # Send to PR author
            github_username = pr_data.get('author')
            discord_id = self.user_mapping.get_discord_id(github_username)
            logger.info(f"Author mode: {github_username} -> {discord_id}")
            return discord_id
        
        elif self.recipient_mode == 'owner':
            # Send to repo owner
            github_username = pr_data.get('repo_owner')
            discord_id = self.user_mapping.get_discord_id(github_username)
            logger.info(f"Owner mode: {github_username} -> {discord_id}")
            return discord_id
        
        else:
            logger.error(f"Unknown recipient mode: {self.recipient_mode}")
            return None
    
    async def _send_review_dm(
        self,
        user_id: int,
        pr_data: Dict[str, Any],
        ai_review: str,
        security_notes: str = None
    ):
        """Send code review via DM to a Discord user"""
        
        try:
            # Fetch Discord user
            user = await self.bot.fetch_user(user_id)
            
            # Build embed
            embed = self.review_builder.create_review_embed(pr_data, ai_review, security_notes)
            
            # Try to send DM
            try:
                await user.send(embed=embed)
                logger.info(f"✅ Successfully sent code review DM to user {user_id} ({user.name})")
            
            except discord.Forbidden:
                # User has DMs disabled
                logger.warning(f"⚠️ Cannot DM user {user_id}, DMs are disabled")
                await self._send_to_fallback_channel(
                    pr_data, ai_review, security_notes, 
                    github_username=pr_data.get('author'),
                    user_mention=user.mention
                )
            
            except discord.HTTPException as e:
                logger.error(f"❌ HTTP error sending DM to {user_id}: {e}")
                await self._send_to_fallback_channel(pr_data, ai_review, security_notes, pr_data.get('author'))
        
        except discord.NotFound:
            logger.error(f"❌ Discord user {user_id} not found")
            await self._send_to_fallback_channel(pr_data, ai_review, security_notes, pr_data.get('author'))
        
        except Exception as e:
            logger.error(f"❌ Failed to send DM: {e}", exc_info=True)
            await self._send_to_fallback_channel(pr_data, ai_review, security_notes, pr_data.get('author'))
    
    async def _send_to_fallback_channel(
        self,
        pr_data: Dict[str, Any],
        ai_review: str,
        security_notes: str,
        github_username: str,
        user_mention: str = None
    ):
        """Send code review to fallback channel when DM fails"""
        
        if not self.fallback_channel_id:
            logger.error("No fallback channel configured, review lost!")
            return
        
        try:
            channel = self.bot.get_channel(self.fallback_channel_id)
            if not channel:
                logger.error(f"Fallback channel {self.fallback_channel_id} not found")
                return
            
            # Build fallback embed
            embed = self.review_builder.create_fallback_embed(
                pr_data, ai_review, security_notes, github_username
            )
            
            # Send with mention if available
            mention_text = f"{user_mention} " if user_mention else f"@{github_username} "
            message = f"{mention_text}Code review for your PR (DM failed):"
            
            await channel.send(content=message, embed=embed)
            logger.info(f"📢 Sent code review to fallback channel for {github_username}")
        
        except Exception as e:
            logger.error(f"Failed to send to fallback channel: {e}", exc_info=True)
    
    async def _send_error_notification(self, error_message: str):
        """Send error notification to fallback channel"""
        
        if not self.fallback_channel_id:
            return
        
        try:
            channel = self.bot.get_channel(self.fallback_channel_id)
            if channel:
                embed = self.review_builder.create_error_embed(error_message)
                await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
