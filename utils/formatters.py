def format_time_ago(timestamp: str) -> str:
    """Format timestamp as relative time (e.g., '2h ago')"""
    try:
        from datetime import datetime
        
        # Parse timestamp (assuming ISO format)
        task_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.utcnow().replace(tzinfo=task_time.tzinfo)
        
        delta = now - task_time
        
        if delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours}h ago"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes}m ago"
        else:
            return "just now"
    except Exception:
        return ""


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to max length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_percentage(value: float) -> str:
    """Format percentage with 1 decimal place"""
    return f"{value:.1f}%"


def format_task_priority(priority: str) -> str:
    """Format task priority with appropriate emoji"""
    priority_map = {
        'URGENT': '🔴 URGENT',
        'HIGH': '🟠 HIGH',
        'MEDIUM': '🟡 MEDIUM',
        'LOW': '🟢 LOW',
    }
    return priority_map.get(priority.upper(), priority)
