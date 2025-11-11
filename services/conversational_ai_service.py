import logging
from typing import List, Dict, Any, Optional
import ollama

logger = logging.getLogger(__name__)


class ConversationalAIService:
    """Service for conversational AI using local Ollama"""
    
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model
        self.client = ollama.Client(host=base_url)
        
        self.system_prompt = """You are PM Bot, a helpful project management assistant for Discord.

Your role:
- Answer questions about projects, tasks, team members, and deadlines
- Provide concise, actionable insights
- Be friendly and conversational
- Suggest next steps when helpful

Response guidelines:
- Keep responses under 400 words (fits Discord DM nicely)
- Use bullet points for lists
- Use emojis sparingly (1-2 per message)
- If data is missing, say "I don't have that information yet"
- End with a follow-up question to keep conversation going

Always base your answers on the provided data. Don't make up information."""
    
    def chat(
        self,
        user_question: str,
        context_data: Dict[str, Any],
        conversation_history: List[Dict[str, str]]
    ) -> Optional[str]:
        """
        Generate AI response to user question
        
        Args:
            user_question: User's natural language question
            context_data: Relevant data from web app (projects, tasks, etc.)
            conversation_history: Recent conversation messages
        
        Returns:
            AI-generated response or None if failed
        """
        try:
            # Build context from data
            data_context = self._format_context_data(context_data)
            
            # Trim overly long questions
            if len(user_question) > 2000:
                user_question = user_question[:2000] + "\n... (truncated)"
            
            # Build conversation history
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add recent conversation history
            for msg in conversation_history[-10:]:  # Last 10 messages
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"][:4000]  # Prevent oversized context
                })
            
            # Add current question with data context
            user_message = f"{user_question}\n\n--- Available Data ---\n{data_context}"
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            logger.info(f"Sending chat request to {self.model}")
            
            # Retry up to 3 times on transient failures
            last_error = None
            for attempt in range(3):
                try:
                    response = self.client.chat(
                        model=self.model,
                        messages=messages,
                        options={
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "num_predict": 500,
                        }
                    )
                    ai_response = response['message']['content']
                    logger.info(f"Received AI response ({len(ai_response)} chars)")
                    return ai_response
                except Exception as e:
                    last_error = e
                    logger.warning(f"Ollama chat failed (attempt {attempt+1}/3): {e}")
                    # Reinitialize client and backoff
                    try:
                        self.client = ollama.Client(host=self.base_url)
                    except Exception:
                        pass
                
            logger.error(f"Failed to generate AI response after retries: {last_error}")
            return None
        
        except Exception as e:
            logger.error(f"Failed to generate AI response: {e}", exc_info=True)
            return None
    def _format_context_data(self, context_data: Dict[str, Any]) -> str:
        """Format context data into readable text for AI"""
        
        if not context_data:
            return "No data available."
        
        parts = []
        
        # Projects
        if 'projects' in context_data and context_data['projects']:
            parts.append("📊 PROJECTS:")
            for project in context_data['projects'][:5]:  # Limit to 5
                name = project.get('name', 'Unknown')
                status = project.get('status', 'unknown')
                parts.append(f"  • {name} - Status: {status}")
        
        # Tasks
        if 'tasks' in context_data and context_data['tasks']:
            parts.append("\n📋 TASKS:")
            for task in context_data['tasks'][:10]:  # Limit to 10
                title = task.get('title', 'Untitled')
                status = task.get('status', 'unknown')
                priority = task.get('priority', 'medium')
                assignee = (task.get('assignee') or {}).get('name', 'Unassigned')
                parts.append(f"  • [{priority}] {title} - {status} (Assigned: {assignee})")
        
        # User stats
        if 'user_stats' in context_data and context_data['user_stats']:
            parts.append("\n👥 TEAM ACTIVITY:")
            for stat in context_data['user_stats'][:5]:
                name = stat.get('userName', 'Unknown')
                completed = stat.get('completed', 0)
                parts.append(f"  • {name}: {completed} tasks completed")
        
        # Stats summary
        if 'stats' in context_data:
            stats = context_data['stats']
            parts.append("\n📈 SUMMARY:")
            parts.append(f"  • Total tasks: {stats.get('totalTasks', 0)}")
            parts.append(f"  • Completed: {stats.get('completedTasks', 0)}")
            parts.append(f"  • In progress: {stats.get('inProgressTasks', 0)}")
        
        # GitHub repo overview
        if 'github_repos' in context_data and context_data['github_repos']:
            parts.append("\n🐙 GITHUB REPOS:")
            for repo in context_data['github_repos'][:3]:
                parts.append(f"  • {repo.get('full_name')} ⭐{repo.get('stars', 0)} 🔱{repo.get('forks', 0)}")
        
        # GitHub recent PRs
        if 'github_prs' in context_data and context_data['github_prs']:
            parts.append("\n🔀 RECENT PRs:")
            for pr in context_data['github_prs'][:5]:
                parts.append(f"  • #{pr.get('number')} {pr.get('title')} by {pr.get('author')} [{pr.get('state')}]")
        
        # GitHub recent commits
        if 'github_commits' in context_data and context_data['github_commits']:
            parts.append("\n🧩 RECENT COMMITS:")
            for c in context_data['github_commits'][:5]:
                parts.append(f"  • {c.get('repo')} - {c.get('message')[:80]} ({c.get('author')})")
        
        return "\n".join(parts) if parts else "No specific data available."
    
    def test_connection(self) -> bool:
        """Test if Ollama is accessible"""
        try:
            self.client.list()
            return True
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
            return False
