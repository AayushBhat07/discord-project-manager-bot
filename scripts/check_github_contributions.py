#!/usr/bin/env python3
"""
GitHub Contribution Checker
Diagnoses why commits aren't showing in GitHub contribution graph
"""

import subprocess
import sys
from datetime import datetime

def check_git_config():
    """Check git configuration"""
    print("=== Git Configuration ===")
    
    # Get current user name and email
    name = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True).stdout.strip()
    email = subprocess.run(['git', 'config', 'user.email'], capture_output=True, text=True).stdout.strip()
    
    print(f"Git User Name: {name}")
    print(f"Git User Email: {email}")
    print()
    
    print("⚠️  IMPORTANT: This email must match an email in your GitHub account!")
    print("   Check: https://github.com/settings/emails")
    print()
    
    return email

def check_recent_commits(email):
    """Check recent commits"""
    print("=== Recent Commits ===")
    
    result = subprocess.run(
        ['git', 'log', '--all', '--pretty=format:%H|%ae|%ad|%s', '--date=iso', '-n', '5'],
        capture_output=True,
        text=True
    )
    
    for line in result.stdout.strip().split('\n'):
        if line:
            commit_hash, author_email, date, message = line.split('|', 3)
            matches = "✓" if author_email == email else "✗"
            print(f"{matches} {commit_hash[:7]} | {date} | {message[:50]}")
    print()

def check_remote():
    """Check remote repository"""
    print("=== Remote Repository ===")
    
    result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
    print(result.stdout)
    
    # Check if it's a fork
    remote_url = subprocess.run(['git', 'config', 'remote.origin.url'], capture_output=True, text=True).stdout.strip()
    
    if 'github.com' in remote_url:
        print("Repository type: GitHub")
        if remote_url.startswith('https://'):
            repo_path = remote_url.replace('https://github.com/', '').replace('.git', '')
        else:
            repo_path = remote_url.split('github.com/')[-1].replace('.git', '')
        
        print(f"Repository: {repo_path}")
        print()
        
        print("⚠️  NOTE: Contributions don't count if:")
        print("   1. Repository is a fork (unless it's your own fork)")
        print("   2. Commits are not in the default branch or merged PR")
        print("   3. Email doesn't match GitHub account")
        print()

def check_timezone():
    """Check timezone issues"""
    print("=== Timezone Check ===")
    
    # Get latest commit date
    result = subprocess.run(
        ['git', 'log', '-1', '--pretty=format:%ad', '--date=iso'],
        capture_output=True,
        text=True
    )
    
    commit_date = result.stdout.strip()
    print(f"Latest commit date: {commit_date}")
    print(f"Current local time: {datetime.now().isoformat()}")
    print()
    
    print("⚠️  GitHub uses UTC for contributions. If your commit time is:")
    print("   - In the future (UTC): Won't show until that time")
    print("   - From yesterday (UTC): Shows on yesterday's date")
    print()

def main():
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║        GitHub Contribution Graph Diagnostic Tool              ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    email = check_git_config()
    check_recent_commits(email)
    check_remote()
    check_timezone()
    
    print("=== Recommendations ===")
    print()
    print("1. Verify email matches GitHub:")
    print("   → Go to https://github.com/settings/emails")
    print("   → Make sure this email is listed:", email)
    print()
    print("2. Check repository type:")
    print("   → If it's a fork, contributions only count if you're the fork owner")
    print()
    print("3. Wait for sync:")
    print("   → GitHub can take up to 24 hours to show contributions")
    print()
    print("4. Push to default branch:")
    print("   → Merge features-dev into main for contributions to count")
    print("   → git checkout main")
    print("   → git merge features-dev")
    print("   → git push origin main")
    print()

if __name__ == "__main__":
    main()
