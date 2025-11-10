import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationContext:
    """Tracks conversation context for a user"""
    
    def __init__(self):
        self.current_project: Optional[str] = None
        self.current_task: Optional[str] = None
        self.current_user: Optional[str] = None
        self.topic: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'current_project': self.current_project,
            'current_task': self.current_task,
            'current_user': self.current_user,
            'topic': self.topic
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        ctx = cls()
        ctx.current_project = data.get('current_project')
        ctx.current_task = data.get('current_task')
        ctx.current_user = data.get('current_user')
        ctx.topic = data.get('topic')
        return ctx


class ConversationManager:
    """Manages conversation history and context for users"""
    
    def __init__(self, history_file: str, max_history: int = 10):
        self.history_file = history_file
        self.max_history = max_history
        self.conversations: Dict[str, Dict[str, Any]] = {}
        
        # Load existing conversations
        self._load_conversations()
    
    def _load_conversations(self):
        """Load conversation history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    
                    # Convert to proper format
                    for user_id, conv_data in data.items():
                        self.conversations[user_id] = {
                            'messages': conv_data.get('messages', []),
                            'context': ConversationContext.from_dict(conv_data.get('context', {})),
                            'last_updated': conv_data.get('last_updated')
                        }
                    
                    logger.info(f"Loaded {len(self.conversations)} conversation histories")
            else:
                logger.info("No existing conversation history found")
        
        except Exception as e:
            logger.error(f"Failed to load conversations: {e}")
            self.conversations = {}
    
    def _save_conversations(self):
        """Save conversation history to file"""
        try:
            # Convert to JSON-serializable format
            data = {}
            for user_id, conv_data in self.conversations.items():
                data[user_id] = {
                    'messages': conv_data['messages'],
                    'context': conv_data['context'].to_dict(),
                    'last_updated': conv_data['last_updated']
                }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self.conversations)} conversation histories")
        
        except Exception as e:
            logger.error(f"Failed to save conversations: {e}")
    
    def get_history(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a user"""
        if user_id not in self.conversations:
            return []
        
        return self.conversations[user_id]['messages']
    
    def get_context(self, user_id: str) -> ConversationContext:
        """Get conversation context for a user"""
        if user_id not in self.conversations:
            self._init_user_conversation(user_id)
        
        return self.conversations[user_id]['context']
    
    def add_message(self, user_id: str, role: str, content: str):
        """Add a message to conversation history"""
        if user_id not in self.conversations:
            self._init_user_conversation(user_id)
        
        # Add message
        self.conversations[user_id]['messages'].append({
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Trim history if too long
        if len(self.conversations[user_id]['messages']) > self.max_history * 2:
            self.conversations[user_id]['messages'] = \
                self.conversations[user_id]['messages'][-self.max_history * 2:]
        
        # Update timestamp
        self.conversations[user_id]['last_updated'] = datetime.utcnow().isoformat()
        
        # Save to disk
        self._save_conversations()
    
    def update_context(self, user_id: str, **kwargs):
        """Update conversation context"""
        if user_id not in self.conversations:
            self._init_user_conversation(user_id)
        
        context = self.conversations[user_id]['context']
        
        if 'project' in kwargs:
            context.current_project = kwargs['project']
        if 'task' in kwargs:
            context.current_task = kwargs['task']
        if 'user' in kwargs:
            context.current_user = kwargs['user']
        if 'topic' in kwargs:
            context.topic = kwargs['topic']
        
        self._save_conversations()
    
    def reset_conversation(self, user_id: str):
        """Clear conversation history and context for a user"""
        if user_id in self.conversations:
            del self.conversations[user_id]
            self._save_conversations()
            logger.info(f"Reset conversation for user {user_id}")
    
    def _init_user_conversation(self, user_id: str):
        """Initialize conversation data for a new user"""
        self.conversations[user_id] = {
            'messages': [],
            'context': ConversationContext(),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def get_context_summary(self, user_id: str) -> str:
        """Get a human-readable summary of current context"""
        context = self.get_context(user_id)
        
        parts = []
        if context.current_project:
            parts.append(f"📁 Discussing: {context.current_project}")
        if context.current_task:
            parts.append(f"📋 Task: {context.current_task}")
        if context.current_user:
            parts.append(f"👤 User: {context.current_user}")
        if context.topic:
            parts.append(f"💬 Topic: {context.topic}")
        
        if parts:
            return "Current context:\n" + "\n".join(parts)
        else:
            return "No active context. Start a conversation!"
