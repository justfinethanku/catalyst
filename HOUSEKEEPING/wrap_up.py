#!/usr/bin/env python3
"""
Session wrap-up script - updates all project documentation and commits
"""
import subprocess
import os
from datetime import datetime
from pathlib import Path

def get_git_changes():
    """Get list of changed files and their diffs"""
    try:
        # Get changed files
        changed = subprocess.check_output(['git', 'status', '--porcelain'], text=True)
        # Get actual diffs
        diffs = subprocess.check_output(['git', 'diff'], text=True)
        return changed, diffs
    except:
        return "", ""

def update_context_md():
    """Update CONTEXT.md with session summary"""
    changed, diffs = get_git_changes()
    
    context_file = Path("CONTEXT.md")
    
    # Read existing content
    existing = ""
    if context_file.exists():
        existing = context_file.read_text()
    
    # Generate update
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    update = f"""

## Session Update - {timestamp}

### Files Modified
```
{changed if changed else "No changes detected"}
```

### Key Changes
- [Claude should summarize the main changes here based on the diffs]
- [Include any problems solved]
- [Note any decisions made]

### Next Steps
- [Claude should identify what needs to be done next]

---
"""
    
    # Prepend new content
    new_content = update + existing
    
    print(f"Updating CONTEXT.md with session summary...")
    print(f"\nChanged files:\n{changed}")
    print("\n[Claude: Please analyze these changes and update the summary above with actual details]")
    
    return new_content

def create_session_log():
    """Create detailed session log in sessions/ folder"""
    Path("sessions").mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_file = Path(f"sessions/session_{timestamp}.md")
    
    changed, diffs = get_git_changes()
    
    content = f"""# Session Log - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Changes Made
```
{changed}
```

## Detailed Diffs
```diff
{diffs if diffs else "No uncommitted changes"}
```

## Session Notes
[Claude: Add detailed notes about what was accomplished this session]

## Problems Encountered
[Claude: Document any issues or blockers]

## Solutions Implemented
[Claude: Describe solutions and approaches used]
"""
    
    print(f"\nCreating session log: {session_file}")
    return session_file, content

def commit_and_push():
    """Commit all changes and push"""
    try:
        # Add all tracked files that were modified
        subprocess.run(['git', 'add', '-u'], check=True)
        
        # Add specific documentation files
        doc_files = ['CONTEXT.md', 'README.md', 'architecture.md', 'sessions/']
        for f in doc_files:
            if Path(f).exists():
                subprocess.run(['git', 'add', f], check=True)
        
        # Generate commit message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_msg = f"Session wrap-up: {timestamp}"
        
        # Commit
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        
        # Push
        print("\nPushing to remote...")
        subprocess.run(['git', 'push'], check=True)
        
        print("✅ Changes committed and pushed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git operation failed: {e}")
        print("You may need to handle this manually")

def main():
    print("🎬 Starting session wrap-up...\n")
    
    # Update CONTEXT.md
    context_content = update_context_md()
    
    # Create session log
    session_file, session_content = create_session_log()
    
    print("\n" + "="*50)
    print("⚡ ACTION REQUIRED - UPDATE THESE FILES NOW:")
    print("="*50)
    print("1. CONTEXT.md - Write the session summary with actual changes")
    print("2. README.md - Update if functionality changed")
    print("3. architecture.md - Update if structure changed")
    print(f"4. {session_file} - Create this file with detailed session notes")
    print("="*50)
    print("Fill in all [Claude: ...] placeholders with real information")
    print("After updating all files, I'll commit and push everything.")
    print("="*50 + "\n")
    
    # Note: Claude Code should actually write these files after seeing this output
    
if __name__ == "__main__":
    main()