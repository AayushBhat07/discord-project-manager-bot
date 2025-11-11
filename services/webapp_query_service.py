import logging
import time
from typing import Dict, Any, Optional
from services.api_service import APIService

logger = logging.getLogger(__name__)


class WebAppQueryService:
    """Service to fetch and cache data from web app API and GitHub"""
    
    def __init__(self, api_service: APIService, cache_ttl: int = 300, github_service=None, repos_to_watch=None):
        self.api_service = api_service
        self.cache_ttl = cache_ttl  # 5 minutes default
        self.cache: Dict[str, Any] = {}
        self.github_service = github_service
        self.repos_to_watch = repos_to_watch or []
    
    def analyze_question_and_fetch_data(self, question: str, context: Any) -> Dict[str, Any]:
        """
        Analyze user question and fetch relevant data
        
        Args:
            question: User's natural language question
            context: ConversationContext object
        
        Returns:
            Dictionary with relevant data from API
        """
        question_lower = question.lower()
        data = {}
        
        # Detect what data is needed based on keywords
        needs_projects = any(word in question_lower for word in [
            'project', 'status', 'progress', 'how is', 'going', 'doing'
        ])
        
        needs_tasks = any(word in question_lower for word in [
            'task', 'todo', 'pending', 'deadline', 'due', 'working on'
        ])
        
        needs_team = any(word in question_lower for word in [
            'team', 'who', 'john', 'working on', 'assigned'
        ])
        
        needs_stats = any(word in question_lower for word in [
            'how many', 'statistics', 'stats', 'summary', 'overview'
        ])
        
        # Fetch projects
        if needs_projects or context.current_project:
            projects = self._get_cached('projects', self._fetch_projects)
            if projects:
                data['projects'] = projects
                
                # Filter to specific project if in context
                if context.current_project:
                    data['projects'] = [
                        p for p in projects 
                        if p.get('name', '').lower() == context.current_project.lower()
                    ]
        
        # Fetch tasks
        if needs_tasks:
            tasks = self._get_cached('tasks', self._fetch_tasks)
            if tasks:
                data['tasks'] = tasks
                
                # Filter by context if available
                if context.current_project:
                    data['tasks'] = [
                        t for t in tasks
                        if t.get('projectName', '').lower() == context.current_project.lower()
                    ]
        
        # Fetch team/user data
        if needs_team:
            # Get tasks to see who's working on what
            tasks = self._get_cached('tasks', self._fetch_tasks)
            if tasks:
                data['tasks'] = tasks
        
        # GitHub data if question references repos/PRs/commits
        needs_github = any(word in question_lower for word in [
            'github', 'repo', 'repository', 'pull request', 'pr', 'commit', 'merge'
        ])
        
        if needs_github and self.github_service and getattr(self.github_service, 'github', None):
            github_data = self._get_cached('github', self._fetch_github_summary)
            if github_data:
                data.update(github_data)
        
        logger.info(f"Fetched data for question. Keys: {list(data.keys())}")
        return data
    
    def _get_cached(self, key: str, fetch_func) -> Optional[Any]:
        """Get data from cache or fetch if expired"""
        now = time.time()
        
        if key in self.cache:
            cached_data, timestamp = self.cache[key]
            if now - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for {key}")
                return cached_data
        
        # Fetch fresh data
        logger.debug(f"Cache miss for {key}, fetching...")
        data = fetch_func()
        
        if data is not None:
            self.cache[key] = (data, now)
        
        return data
    
    def _fetch_projects(self):
        """Fetch projects from API"""
        try:
            return self.api_service.get_active_projects()
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            return None
    
    def _fetch_tasks(self):
        """Fetch recent tasks from API"""
        try:
            return self.api_service.get_recent_tasks(hours=24 * 7)  # Last week
        except Exception as e:
            logger.error(f"Failed to fetch tasks: {e}")
            return None
    
    def _fetch_github_summary(self):
        """Fetch GitHub repo info, recent PRs and commits for watched repos"""
        try:
            repos_info = []
            recent_prs = []
            recent_commits = []
            
            gh = getattr(self.github_service, 'github', None)
            if not gh:
                return None
            
            for full_name in (self.repos_to_watch or [])[:3]:
                try:
                    repo = gh.get_repo(full_name)
                    repos_info.append({
                        'name': repo.name,
                        'full_name': repo.full_name,
                        'description': repo.description,
                        'owner': repo.owner.login,
                        'url': repo.html_url,
                        'language': repo.language,
                        'stars': repo.stargazers_count,
                        'forks': repo.forks_count,
                    })
                    # Recent PRs
                    for pr in repo.get_pulls(state='open')[:5]:
                        recent_prs.append({
                            'number': pr.number,
                            'title': pr.title,
                            'author': pr.user.login,
                            'state': pr.state,
                            'repo': full_name,
                        })
                    # Recent commits (last 10)
                    for c in repo.get_commits()[:10]:
                        recent_commits.append({
                            'repo': full_name,
                            'message': (c.commit.message or '').split('\n')[0],
                            'author': getattr(getattr(c.commit, 'author', None), 'name', '') or (getattr(c.author, 'login', None) or 'unknown'),
                        })
                except Exception as e:
                    logger.warning(f"Failed to fetch GitHub data for {full_name}: {e}")
                    continue
            
            return {
                'github_repos': repos_info,
                'github_prs': recent_prs,
                'github_commits': recent_commits,
            }
        except Exception as e:
            logger.error(f"Failed to fetch GitHub summary: {e}")
            return None
