import os
import json
from datetime import datetime

class UserConfigManager:
    def __init__(self):
        self.store_path = os.path.join('store', 'user_configs.json')
        self.user_configs = {}
        self.session_inactivity_days = int(os.getenv('SESSION_INACTIVITY_DAYS', '7'))

    def initialize(self):
        os.makedirs('store', exist_ok=True)
        self.load()

    def load(self):
        try:
            if os.path.exists(self.store_path):
                with open(self.store_path, 'r') as f:
                    self.user_configs = json.load(f)
        except Exception:
            self.user_configs = {}

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
            with open(self.store_path, 'w') as f:
                json.dump(self.user_configs, f, indent=2)
        except Exception as e:
            print(f'Failed to save user configs: {e}')

    def create_user_config(self, user_id, username):
        self.user_configs[user_id] = {
            'username': username,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'github': {
                'pat': None,
                'repo_path': None,
                'repo_url': None,
                'branch': 'main',
                'remote': 'origin'
            },
            'discord': {
                'dm_enabled': True
            },
            'preferences': {
                'default_commit_message': '',
                'timezone': 'UTC'
            }
        }
        self.save()
        return self.user_configs[user_id]

    def get_user_config(self, user_id):
        return self.user_configs.get(user_id)

    def update_user_config(self, user_id, updates):
        if user_id not in self.user_configs:
            return None
        
        self.user_configs[user_id] = {
            **self.user_configs[user_id],
            **updates,
            'updated_at': datetime.now().isoformat()
        }
        self.save()
        return self.user_configs[user_id]

    def update_last_activity(self, user_id):
        if user_id in self.user_configs:
            self.user_configs[user_id]['last_activity'] = datetime.now().isoformat()
            self.save()

    def set_github_pat(self, user_id, pat):
        if user_id not in self.user_configs:
            return {'success': False, 'error': 'User config not found'}
        self.user_configs[user_id]['github']['pat'] = pat
        self.user_configs[user_id]['updated_at'] = datetime.now().isoformat()
        self.save()
        return {'success': True}

    def get_github_pat(self, user_id):
        return self.user_configs.get(user_id, {}).get('github', {}).get('pat')

    def set_repo_config(self, user_id, repo_path, branch='main', remote='origin'):
        if user_id not in self.user_configs:
            return {'success': False, 'error': 'User config not found'}
        self.user_configs[user_id]['github']['repo_path'] = repo_path
        self.user_configs[user_id]['github']['branch'] = branch
        self.user_configs[user_id]['github']['remote'] = remote
        self.user_configs[user_id]['updated_at'] = datetime.now().isoformat()
        self.save()
        return {'success': True}

    def get_repo_config(self, user_id):
        return self.user_configs.get(user_id, {}).get('github')

    def has_github_setup(self, user_id):
        config = self.user_configs.get(user_id, {}).get('github')
        return bool(config and config.get('pat') and config.get('repo_path'))

    def get_inactive_users(self, days=None):
        if days is None:
            days = self.session_inactivity_days
        
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        inactive = []
        
        for user_id, config in self.user_configs.items():
            last_activity = config.get('last_activity')
            if last_activity:
                try:
                    activity_time = datetime.fromisoformat(last_activity).timestamp()
                    if activity_time < cutoff:
                        inactive.append(user_id)
                except ValueError:
                    pass
        
        return inactive

    def delete_user_config(self, user_id):
        if user_id in self.user_configs:
            del self.user_configs[user_id]
            self.save()
            return True
        return False

    def list_users(self):
        return [
            {
                'user_id': user_id,
                'username': config.get('username'),
                'has_github': self.has_github_setup(user_id),
                'updated_at': config.get('updated_at'),
                'last_activity': config.get('last_activity')
            }
            for user_id, config in self.user_configs.items()
        ]

    def get_all_scheduled_jobs(self):
        from modules.scheduler_service import SchedulerService
        return SchedulerService.list_all_jobs()
