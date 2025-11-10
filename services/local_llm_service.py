import ollama
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class LocalLLMService:
    """Service to interact with local Ollama AI for code reviews"""
    
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model
        self.client = ollama.Client(host=base_url)
    
    def test_connection(self) -> bool:
        """Test if Ollama is running and accessible"""
        try:
            self.client.list()
            logger.info(f"Successfully connected to Ollama at {self.base_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    def review_code(self, pr_data: Dict[str, Any]) -> Optional[str]:
        """
        Send code changes to AI for review
        
        Args:
            pr_data: Dictionary containing PR information and code diffs
        
        Returns:
            AI-generated code review as a string
        """
        try:
            prompt = self._build_review_prompt(pr_data)
            
            logger.info(f"Sending code review request to {self.model}")
            
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.3,  # More focused responses
                    'top_p': 0.9,
                }
            )
            
            review = response['response']
            logger.info(f"Received code review ({len(review)} chars)")
            return review
            
        except Exception as e:
            logger.error(f"Failed to generate code review: {e}", exc_info=True)
            return None
    
    def security_scan(self, pr_data: Dict[str, Any]) -> Optional[str]:
        """
        Perform security-focused analysis of code changes
        
        Args:
            pr_data: Dictionary containing PR information and code diffs
        
        Returns:
            Security analysis as a string
        """
        try:
            prompt = self._build_security_prompt(pr_data)
            
            logger.info(f"Sending security scan request to {self.model}")
            
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.2,  # Very focused for security
                }
            )
            
            security_notes = response['response']
            logger.info(f"Received security analysis ({len(security_notes)} chars)")
            return security_notes
            
        except Exception as e:
            logger.error(f"Failed to generate security analysis: {e}", exc_info=True)
            return None
    
    def _build_review_prompt(self, pr_data: Dict[str, Any]) -> str:
        """Build the AI prompt for code review"""
        prompt = f"""You are an expert code reviewer. Review the following pull request and provide constructive feedback.

**Pull Request Information:**
- Title: {pr_data.get('title', 'N/A')}
- Description: {pr_data.get('description', 'N/A')}
- Files Changed: {pr_data.get('files_changed', 0)}
- Lines Added: +{pr_data.get('additions', 0)}
- Lines Removed: -{pr_data.get('deletions', 0)}

**Code Changes:**
"""
        
        # Add file diffs
        for file_diff in pr_data.get('diffs', [])[:20]:  # Limit to 20 files
            prompt += f"\n--- File: {file_diff.get('filename', 'unknown')} ---\n"
            prompt += f"{file_diff.get('patch', 'No diff available')}\n"
        
        prompt += """

**Please provide:**
1. **Summary**: Brief overview of what this PR does
2. **Code Quality**: Comment on code structure, readability, and best practices
3. **Potential Issues**: Any bugs, edge cases, or problems you spot
4. **Suggestions**: Improvements or optimizations
5. **Overall Assessment**: Approve, needs changes, or reject

Keep your review concise and actionable. Focus on the most important points.
"""
        
        return prompt
    
    def _build_security_prompt(self, pr_data: Dict[str, Any]) -> str:
        """Build the AI prompt for security analysis"""
        prompt = f"""You are a security expert analyzing code changes for vulnerabilities.

**Pull Request:** {pr_data.get('title', 'N/A')}

**Code Changes:**
"""
        
        for file_diff in pr_data.get('diffs', [])[:20]:
            prompt += f"\n--- {file_diff.get('filename', 'unknown')} ---\n"
            prompt += f"{file_diff.get('patch', '')}\n"
        
        prompt += """

**Security Analysis Required:**
1. **Vulnerabilities**: SQL injection, XSS, CSRF, authentication issues, etc.
2. **Data Exposure**: Sensitive data in logs, hardcoded secrets, insecure storage
3. **Access Control**: Authorization bypasses, privilege escalation
4. **Dependencies**: Vulnerable libraries or packages
5. **Best Practices**: Security misconfigurations

Rate severity as: CRITICAL, HIGH, MEDIUM, LOW, or NONE
Be specific about line numbers and exact issues found.
"""
        
        return prompt
