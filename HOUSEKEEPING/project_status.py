#!/usr/bin/env python3
"""
Project status checker - shows current state and todos
"""
import subprocess
import os
from pathlib import Path
from datetime import datetime

def check_git_status():
    """Get current git status"""
    try:
        # Branch info
        branch = subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip()
        
        # Uncommitted changes
        status = subprocess.check_output(['git', 'status', '--short'], text=True)
        
        # Last commit
        last_commit = subprocess.check_output(
            ['git', 'log', '-1', '--oneline'], 
            text=True
        ).strip()
        
        # Count commits ahead/behind
        try:
            ahead_behind = subprocess.check_output(
                ['git', 'rev-list', '--count', '--left-right', 'HEAD...origin/' + branch],
                text=True
            ).strip()
            ahead, behind = ahead_behind.split('\t')
        except:
            ahead, behind = "?", "?"
        
        return {
            'branch': branch,
            'changes': status,
            'last_commit': last_commit,
            'ahead': ahead,
            'behind': behind
        }
    except Exception as e:
        return {'error': str(e)}

def check_todos():
    """Find TODO comments in code"""
    todos = []
    try:
        # Use git grep to find TODOs in tracked files
        result = subprocess.check_output(
            ['git', 'grep', '-n', '-i', 'TODO'], 
            text=True
        )
        todos = result.strip().split('\n') if result else []
    except:
        pass
    
    return todos

def check_recent_sessions():
    """Check recent session logs"""
    sessions_dir = Path("sessions")
    recent_sessions = []
    
    if sessions_dir.exists():
        session_files = sorted(sessions_dir.glob("session_*.md"), reverse=True)[:5]
        for f in session_files:
            recent_sessions.append(f.name)
    
    return recent_sessions

def read_context_summary():
    """Get the latest update from CONTEXT.md"""
    context_file = Path("CONTEXT.md")
    if context_file.exists():
        content = context_file.read_text()
        # Extract first section (latest update)
        lines = content.split('\n')
        summary = []
        for line in lines[:20]:  # First 20 lines should contain latest update
            if line.startswith('---'):
                break
            summary.append(line)
        return '\n'.join(summary)
    return "No CONTEXT.md found"

def main():
    print("📊 PROJECT STATUS REPORT")
    print("=" * 50)
    
    # Git status
    git_info = check_git_status()
    if 'error' not in git_info:
        print(f"\n🌿 Git Status")
        print(f"Branch: {git_info['branch']}")
        print(f"Last commit: {git_info['last_commit']}")
        print(f"Ahead/Behind origin: {git_info['ahead']}/{git_info['behind']}")
        
        if git_info['changes']:
            print(f"\n📝 Uncommitted changes:")
            print(git_info['changes'])
        else:
            print("\n✅ Working directory clean")
    
    # TODOs
    todos = check_todos()
    if todos:
        print(f"\n📌 TODOs found ({len(todos)}):")
        for todo in todos[:10]:  # Show first 10
            print(f"  {todo}")
        if len(todos) > 10:
            print(f"  ... and {len(todos) - 10} more")
    
    # Recent sessions
    sessions = check_recent_sessions()
    if sessions:
        print(f"\n📅 Recent Sessions:")
        for session in sessions:
            print(f"  - {session}")
    
    # Context summary
    print(f"\n📋 Latest Context Update:")
    print("-" * 30)
    print(read_context_summary())
    
    print("\n" + "=" * 50)
    print("💡 Run 'python update_context.py' for quick update")
    print("🎬 Run 'python wrap_up.py' for full session wrap-up")

if __name__ == "__main__":
    main()