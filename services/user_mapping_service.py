import json
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class UserMappingService:
    """Service to map GitHub usernames to Discord user IDs"""
    
    def __init__(self, mapping_file: str):
        self.mapping_file = mapping_file
        self.mappings = self._load_mappings()
    
    def _load_mappings(self) -> dict:
        """Load user mappings from JSON file"""
        try:
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r') as f:
                    mappings = json.load(f)
                    logger.info(f"Loaded {len(mappings)} user mappings")
                    return mappings
            else:
                logger.warning(f"User mapping file not found: {self.mapping_file}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load user mappings: {e}")
            return {}
    
    def _save_mappings(self) -> None:
        """Save user mappings to JSON file"""
        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(self.mappings, f, indent=2)
            logger.info(f"Saved {len(self.mappings)} user mappings")
        except Exception as e:
            logger.error(f"Failed to save user mappings: {e}")
    
    def get_discord_id(self, github_username: str) -> Optional[int]:
        """Get Discord user ID for a GitHub username"""
        discord_id_str = self.mappings.get(github_username)
        if discord_id_str:
            try:
                return int(discord_id_str)
            except ValueError:
                logger.error(f"Invalid Discord ID for {github_username}: {discord_id_str}")
                return None
        return None
    
    def add_mapping(self, github_username: str, discord_user_id: int) -> bool:
        """Add or update a GitHub to Discord mapping"""
        try:
            self.mappings[github_username] = str(discord_user_id)
            self._save_mappings()
            logger.info(f"Added mapping: {github_username} -> {discord_user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add mapping: {e}")
            return False
    
    def remove_mapping(self, github_username: str) -> bool:
        """Remove a GitHub to Discord mapping"""
        if github_username in self.mappings:
            del self.mappings[github_username]
            self._save_mappings()
            logger.info(f"Removed mapping for {github_username}")
            return True
        return False
    
    def get_all_mappings(self) -> dict:
        """Get all current mappings"""
        return self.mappings.copy()
    
    def reload_mappings(self) -> None:
        """Reload mappings from file"""
        self.mappings = self._load_mappings()
