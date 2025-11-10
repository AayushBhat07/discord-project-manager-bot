import logging
import time
from typing import Dict, Any, Optional
from services.api_service import APIService

logger = logging.getLogger(__name__)


class WebAppQueryService:
    """Service to fetch and cache data from web app API"""
    
    def __init__(self, api_service: APIService, cache_ttl: int = 300):
        self.api_service = api_service
        self.cache_ttl = cache_ttl  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
    
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
        
        # Fetch stats
        if needs_stats:
            # Get all data for comprehensive stats
            data['projects'] = self._get_cached('projects', self._fetch_projects)
            data['tasks'] = self._get_cached('tasks', self._fetch_tasks)
        
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
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        logger.info("Cleared data cache")
