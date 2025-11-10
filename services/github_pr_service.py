from github import Github
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class GitHubPRService:
    """Service to fetch pull request data from GitHub"""
    
    def __init__(self, github_token: str):
        self.github = Github(github_token) if github_token else None
        if not self.github:
            logger.warning("GitHub token not provided. PR fetching will not work.")
    
    def get_pr_data(self, repo_full_name: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        Fetch complete pull request data
        
        Args:
            repo_full_name: Repository in format "owner/repo"
            pr_number: PR number
        
        Returns:
            Dictionary with PR data and code diffs
        """
        if not self.github:
            logger.error("GitHub client not initialized")
            return None
        
        try:
            logger.info(f"Fetching PR #{pr_number} from {repo_full_name}")
            
            repo = self.github.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            
            # Get PR metadata
            pr_data = {
                'number': pr.number,
                'title': pr.title,
                'description': pr.body or 'No description provided',
                'author': pr.user.login,
                'repo_name': repo_full_name,
                'repo_owner': repo.owner.login,
                'state': pr.state,
                'merged': pr.merged,
                'merged_at': pr.merged_at.isoformat() if pr.merged_at else None,
                'html_url': pr.html_url,
                'files_changed': pr.changed_files,
                'additions': pr.additions,
                'deletions': pr.deletions,
                'commits': pr.commits,
                'diffs': []
            }
            
            # Get file changes
            files = pr.get_files()
            for file in files:
                # Filter out certain file types
                if self._should_skip_file(file.filename):
                    continue
                
                file_data = {
                    'filename': file.filename,
                    'status': file.status,  # added, modified, removed
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'changes': file.changes,
                    'patch': file.patch if file.patch else 'Binary file or no changes'
                }
                
                # Truncate very large patches
                if file_data['patch'] and len(file_data['patch']) > 5000:
                    file_data['patch'] = file_data['patch'][:5000] + "\n\n... (truncated)"
                
                pr_data['diffs'].append(file_data)
            
            # Limit to first 20 files
            if len(pr_data['diffs']) > 20:
                logger.warning(f"PR has {len(pr_data['diffs'])} files, limiting to 20")
                pr_data['diffs'] = pr_data['diffs'][:20]
            
            logger.info(f"Successfully fetched PR data: {pr_data['files_changed']} files, "
                       f"+{pr_data['additions']}/-{pr_data['deletions']} lines")
            
            return pr_data
            
        except Exception as e:
            logger.error(f"Failed to fetch PR data: {e}", exc_info=True)
            return None
    
    def _should_skip_file(self, filename: str) -> bool:
        """Check if a file should be skipped from review"""
        skip_patterns = [
            'package-lock.json',
            'yarn.lock',
            'pnpm-lock.yaml',
            '.min.js',
            '.min.css',
            'dist/',
            'build/',
            '.map',
            'node_modules/',
            '__pycache__/',
            '.pyc',
            '.png',
            '.jpg',
            '.jpeg',
            '.gif',
            '.svg',
            '.ico',
            '.pdf',
            '.zip',
            '.tar',
            '.gz'
        ]
        
        filename_lower = filename.lower()
        return any(pattern in filename_lower for pattern in skip_patterns)
    
    def get_repo_info(self, repo_full_name: str) -> Optional[Dict[str, Any]]:
        """Get basic repository information"""
        if not self.github:
            return None
        
        try:
            repo = self.github.get_repo(repo_full_name)
            return {
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'owner': repo.owner.login,
                'url': repo.html_url,
                'language': repo.language,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count
            }
        except Exception as e:
            logger.error(f"Failed to fetch repo info: {e}")
            return None
