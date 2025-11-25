import json
import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ProjectManagerService:
    """Service for managing local projects and tasks"""

    def __init__(self, data_file: str = 'data/local_projects.json'):
        self.data_file = data_file
        self.projects = []
        self.config = {}
        self._load_data()

    def _load_data(self):
        """Load projects from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.projects = data.get('projects', [])
                    self.config = data.get('config', {})
            else:
                self.projects = []
                self.config = {}
                self._save_data()
        except Exception as e:
            logger.error(f"Failed to load local projects: {e}")
            self.projects = []

    def _save_data(self):
        """Save projects to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump({'projects': self.projects, 'config': self.config}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save local projects: {e}")

    def set_config(self, key: str, value: str):
        """Set a configuration value"""
        self.config[key] = value
        self._save_data()

    def get_config(self, key: str) -> Optional[str]:
        """Get a configuration value"""
        return self.config.get(key)

    def create_project(self, name: str, description: str = "") -> Dict:
        """Create a new project"""
        project = {
            'id': str(uuid.uuid4()),
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'tasks': []
        }
        self.projects.append(project)
        self._save_data()
        return project

    def get_projects(self) -> List[Dict]:
        """Get all projects"""
        return self.projects

    def get_project_by_name(self, name: str) -> Optional[Dict]:
        """Get a project by name (case-insensitive)"""
        for project in self.projects:
            if project['name'].lower() == name.lower():
                return project
        return None

    def add_task(self, project_id: str, title: str, assignee_id: str = None, due_date: str = None) -> Optional[Dict]:
        """Add a task to a project"""
        for project in self.projects:
            if project['id'] == project_id:
                task = {
                    'id': str(uuid.uuid4()),
                    'title': title,
                    'status': 'todo',
                    'assignee_id': assignee_id,
                    'due_date': due_date,
                    'created_at': datetime.now().isoformat()
                }
                project['tasks'].append(task)
                self._save_data()
                return task
        return None

    def get_tasks(self, project_id: str) -> List[Dict]:
        """Get tasks for a project"""
        for project in self.projects:
            if project['id'] == project_id:
                return project['tasks']
        return []

    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        if status not in ['todo', 'in_progress', 'done']:
            return False
        
        for project in self.projects:
            for task in project['tasks']:
                if task['id'] == task_id:
                    task['status'] = status
                    self._save_data()
                    return True
        return False

    def assign_task(self, task_id: str, assignee_id: str) -> bool:
        """Assign a task to a user"""
        for project in self.projects:
            for task in project['tasks']:
                if task['id'] == task_id:
                    task['assignee_id'] = assignee_id
                    self._save_data()
                    return True
        return False
