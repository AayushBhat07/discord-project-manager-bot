import re
from typing import List, Dict, Any


class DiffAnalyzer:
    """Utility to analyze and parse code diffs"""
    
    @staticmethod
    def parse_patch(patch: str) -> Dict[str, Any]:
        """
        Parse a git patch/diff string
        
        Args:
            patch: Git diff patch string
        
        Returns:
            Dictionary with parsed diff information
        """
        if not patch:
            return {'additions': [], 'deletions': [], 'context': []}
        
        additions = []
        deletions = []
        context = []
        
        for line in patch.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                additions.append(line[1:].strip())
            elif line.startswith('-') and not line.startswith('---'):
                deletions.append(line[1:].strip())
            elif line.startswith(' '):
                context.append(line[1:].strip())
        
        return {
            'additions': additions,
            'deletions': deletions,
            'context': context,
            'total_changes': len(additions) + len(deletions)
        }
    
    @staticmethod
    def extract_functions(patch: str, language: str = 'python') -> List[str]:
        """Extract function definitions from a patch"""
        functions = []
        
        if language == 'python':
            pattern = r'def\s+(\w+)\s*\('
        elif language in ['javascript', 'typescript']:
            pattern = r'(function\s+\w+|const\s+\w+\s*=\s*\([^)]*\)\s*=>)'
        elif language == 'java':
            pattern = r'(public|private|protected)\s+\w+\s+(\w+)\s*\('
        else:
            return functions
        
        for line in patch.split('\n'):
            if line.startswith('+'):
                matches = re.findall(pattern, line)
                functions.extend(matches)
        
        return functions
    
    @staticmethod
    def categorize_changes(files: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Categorize file changes by type"""
        categories = {
            'backend': [],
            'frontend': [],
            'config': [],
            'tests': [],
            'docs': [],
            'other': []
        }
        
        for file_diff in files:
            filename = file_diff.get('filename', '').lower()
            
            if any(ext in filename for ext in ['.py', '.java', '.go', '.rb', '.php']):
                if 'test' in filename:
                    categories['tests'].append(filename)
                else:
                    categories['backend'].append(filename)
            
            elif any(ext in filename for ext in ['.js', '.jsx', '.ts', '.tsx', '.vue', '.html', '.css']):
                if 'test' in filename or 'spec' in filename:
                    categories['tests'].append(filename)
                else:
                    categories['frontend'].append(filename)
            
            elif any(ext in filename for ext in ['.json', '.yaml', '.yml', '.toml', '.ini', '.env']):
                categories['config'].append(filename)
            
            elif any(ext in filename for ext in ['.md', '.txt', '.rst']):
                categories['docs'].append(filename)
            
            else:
                categories['other'].append(filename)
        
        return categories
    
    @staticmethod
    def estimate_complexity(pr_data: Dict[str, Any]) -> str:
        """Estimate PR complexity based on changes"""
        files_changed = pr_data.get('files_changed', 0)
        additions = pr_data.get('additions', 0)
        deletions = pr_data.get('deletions', 0)
        total_changes = additions + deletions
        
        if files_changed > 20 or total_changes > 1000:
            return 'Very Complex'
        elif files_changed > 10 or total_changes > 500:
            return 'Complex'
        elif files_changed > 5 or total_changes > 200:
            return 'Moderate'
        else:
            return 'Simple'
