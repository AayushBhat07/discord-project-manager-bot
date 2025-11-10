import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from services.github_pr_service import GitHubPRService

logger = logging.getLogger(__name__)


class GitHubPollService:
    """Service to poll GitHub for recently merged PRs (simpler than webhooks!)"""
    
    def __init__(self, github_service: GitHubPRService, repos_to_watch: List[str]):
        """
        Args:
            github_service: GitHubPRService instance
            repos_to_watch: List of repo names like ["owner/repo"]
        """
        self.github_service = github_service
        self.repos_to_watch = repos_to_watch
        self.last_checked = {}  # Track last PR we processed per repo
    
    def get_recently_merged_prs(self, hours: int = 1) -> List[Dict[str, Any]]:
        """
        Check all watched repos for PRs merged in the last N hours
        
        Args:
            hours: How far back to check (default: 1 hour)
        
        Returns:
            List of PR data dictionaries for newly merged PRs
        """
        if not self.github_service.github:
            logger.error("GitHub client not initialized")
            return []
        
        newly_merged = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        for repo_name in self.repos_to_watch:
            try:
                logger.info(f"Checking {repo_name} for merged PRs...")
                
                repo = self.github_service.github.get_repo(repo_name)
                
                # Get recently closed PRs
                closed_prs = repo.get_pulls(state='closed', sort='updated', direction='desc')
                
                # Check first 10 recently closed PRs
                for pr in list(closed_prs)[:10]:
                    # Skip if not merged
                    if not pr.merged:
                        continue
                    
                    # Skip if merged too long ago
                    if pr.merged_at < cutoff_time:
                        continue
                    
                    # Skip if we already processed this PR
                    last_pr_id = self.last_checked.get(repo_name, 0)
                    if pr.number <= last_pr_id:
                        continue
                    
                    # This is a new merged PR!
                    logger.info(f"Found newly merged PR: {repo_name}#{pr.number}")
                    
                    newly_merged.append({
                        'repo_name': repo_name,
                        'pr_number': pr.number,
                        'pr_author': pr.user.login,
                        'merged_at': pr.merged_at
                    })
                    
                    # Update last checked
                    if pr.number > last_pr_id:
                        self.last_checked[repo_name] = pr.number
            
            except Exception as e:
                logger.error(f"Failed to check {repo_name}: {e}")
                continue
        
        return newly_merged
    
    def add_repo_to_watch(self, repo_name: str):
        """Add a repository to watch list"""
        if repo_name not in self.repos_to_watch:
            self.repos_to_watch.append(repo_name)
            logger.info(f"Now watching {repo_name}")
    
    def remove_repo_from_watch(self, repo_name: str):
        """Remove a repository from watch list"""
        if repo_name in self.repos_to_watch:
            self.repos_to_watch.remove(repo_name)
            logger.info(f"Stopped watching {repo_name}")
