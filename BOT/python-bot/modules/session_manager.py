import os
import json
import uuid
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self):
        self.store_path = os.path.join('store', 'sessions.json')
        self.sessions = {}
        self.retention_days = int(os.getenv('SESSION_RETENTION_DAYS', '30'))
        self.inactivity_days = int(os.getenv('SESSION_INACTIVITY_DAYS', '7'))
        self.sessions_data = {}

    def initialize(self):
        os.makedirs('store', exist_ok=True)
        self.load()

    def load(self):
        try:
            if os.path.exists(self.store_path):
                with open(self.store_path, 'r') as f:
                    self.sessions_data = json.load(f)
        except Exception:
            self.sessions_data = {}

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
            with open(self.store_path, 'w') as f:
                json.dump(self.sessions_data, f, indent=2)
        except Exception as e:
            print(f'Failed to save sessions: {e}')

    def create_session(self, user_id, username, config=None):
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        self.sessions_data[session_id] = {
            'id': session_id,
            'user_id': user_id,
            'username': username,
            'start_time': now,
            'last_activity': now,
            'config': config or {},
            'commits': []
        }
        self.save()
        return self.sessions_data[session_id]

    def get_active_session(self, user_id):
        now = datetime.now()
        cutoff = now - timedelta(days=self.retention_days)
        
        for session in self.sessions_data.values():
            if session.get('user_id') == user_id:
                try:
                    start_time = datetime.fromisoformat(session.get('start_time', now.isoformat()))
                    if start_time > cutoff:
                        return session
                except ValueError:
                    pass
        return None

    def update_session_activity(self, session_id):
        if session_id in self.sessions_data:
            self.sessions_data[session_id]['last_activity'] = datetime.now().isoformat()
            self.save()

    def add_commit_to_session(self, session_id, commit_info):
        if session_id in self.sessions_data:
            self.sessions_data[session_id]['commits'].append({
                **commit_info,
                'timestamp': datetime.now().isoformat()
            })
            self.save()

    def get_session_stats(self, user_id):
        sessions = [s for s in self.sessions_data.values() if s.get('user_id') == user_id]
        
        total_commits = 0
        for session in sessions:
            total_commits += len(session.get('commits', []))
        
        active = self.get_active_session(user_id)
        
        return {
            'total_sessions': len(sessions),
            'active_sessions': 1 if active else 0,
            'total_commits': total_commits
        }

    def clean_expired_sessions(self):
        now = datetime.now()
        cutoff = now - timedelta(days=self.retention_days)
        expired = []
        
        for session_id, session in list(self.sessions_data.items()):
            try:
                start_time = datetime.fromisoformat(session.get('start_time', now.isoformat()))
                if start_time < cutoff:
                    expired.append(session_id)
            except ValueError:
                expired.append(session_id)
        
        for session_id in expired:
            del self.sessions_data[session_id]
        
        if expired:
            self.save()
        
        return len(expired)

    def cleanup_inactive_sessions(self):
        now = datetime.now()
        cutoff = now - timedelta(days=self.inactivity_days)
        inactive = []
        
        for session_id, session in list(self.sessions_data.items()):
            try:
                last_activity = datetime.fromisoformat(session.get('last_activity', now.isoformat()))
                if last_activity < cutoff:
                    inactive.append(session_id)
            except ValueError:
                inactive.append(session_id)
        
        for session_id in inactive:
            del self.sessions_data[session_id]
        
        if inactive:
            self.save()
        
        return len(inactive)
