"""
Add user reminder preferences
"""

    
    def set_user_preference(self, user_id: str, preference: str, value: any):
        """Set user reminder preference"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        
        self.user_preferences[user_id][preference] = value
        logger.info(f"Updated preference for user {user_id}: {preference} = {value}")
    
    def get_user_preference(self, user_id: str, preference: str, default=None):
        """Get user reminder preference"""
        return self.user_preferences.get(user_id, {}).get(preference, default)
