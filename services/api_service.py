import requests
import logging
from typing import List, Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class APIService:
    """Service for interacting with the web app API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timeout = 10
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get_active_projects(self) -> List[Dict]:
        """Fetch all active projects"""
        try:
            logger.info("Fetching active projects from API")
            response = self.session.get(
                f"{self.base_url}/api/discord/projects",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # Handle response structure with nested "projects" field
            if isinstance(data, dict) and 'projects' in data:
                projects = data['projects']
                logger.info(f"Successfully fetched {len(projects)} projects")
                return projects
            elif isinstance(data, list):
                # Fallback: handle if API returns array directly
                logger.info(f"Successfully fetched {len(data)} projects")
                return data
            else:
                logger.error(f"Unexpected API response structure: {data}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch projects: {e}")
            raise
    
    def get_recent_tasks(self, hours: int = 12) -> List[Dict]:
        """Fetch tasks updated in last N hours"""
        try:
            logger.info(f"Fetching tasks from last {hours} hours")
            response = self.session.post(
                f"{self.base_url}/api/discord/tasks/recent",
                json={"hours": hours},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched {len(data)} recent tasks")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch recent tasks: {e}")
            raise
    
    def get_user_stats(self, project_id: str, hours: int = 12) -> List[Dict]:
        """Fetch user completion statistics"""
        try:
            logger.info(f"Fetching user stats for project {project_id}")
            response = self.session.post(
                f"{self.base_url}/api/discord/stats",
                json={"projectId": project_id, "hours": hours},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched stats for {len(data)} users")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch user stats: {e}")
            raise
    
    def get_incomplete_tasks(self, project_id: str) -> List[Dict]:
        """Fetch pending/overdue tasks"""
        try:
            logger.info(f"Fetching incomplete tasks for project {project_id}")
            response = self.session.post(
                f"{self.base_url}/api/discord/incomplete",
                json={"projectId": project_id},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched {len(data)} incomplete tasks")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch incomplete tasks: {e}")
            raise
    
    def get_recent_commits(self, project_id: str, hours: int = 12) -> List[Dict]:
        """Fetch recent GitHub commits"""
        try:
            logger.info(f"Fetching commits for project {project_id}")
            response = self.session.post(
                f"{self.base_url}/api/discord/commits",
                json={"projectId": project_id, "hours": hours},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched {len(data)} commits")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch commits: {e}")
            raise
    
    def link_discord_user(self, discord_id: str, email: str) -> Dict:
        """Link Discord user to web app user"""
        try:
            logger.info(f"Linking Discord user {discord_id} to email {email}")
            response = self.session.post(
                f"{self.base_url}/api/discord/link",
                json={"discordId": discord_id, "email": email},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Successfully linked Discord user")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to link Discord user: {e}")
            raise
