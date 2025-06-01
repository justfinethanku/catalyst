#!/usr/bin/env python3
"""
Quick context update without full wrap-up
"""
import subprocess
from datetime import datetime
from pathlib import Path

def quick_update():
    """Add a quick update to CONTEXT.md"""
    
    # Get current changes
    try:
        status = subprocess.check_output(['git', 'status', '--short'], text=True)
    except:
        status = "Unable to get git status"
    
    # Read current context
    context_file = Path("CONTEXT.md")
    existing = ""
    if context_file.exists():
        existing = context_file.read_text()
    
    # Create update template
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    update = f"""
## Quick Update - {timestamp}

### Current State
[Claude: Describe current state of the project]

### Recent Changes
```
{status}
```

### Notes
[Claude: Add any relevant notes or reminders]

---

"""
    
    print("📝 Updating CONTEXT.md...")
    print(f"\nCurrent git status:\n{status}")
    
    # Show what should be added
    print(f"\nSuggested addition to CONTEXT.md:")
    print(update)
    
    print("\n⚡ ACTION REQUIRED: NOW WRITE the above content to CONTEXT.md")
    print("Fill in the [Claude: ...] placeholders with actual details from this session")
    print("Prepend this update to the existing CONTEXT.md content")

def main():
    quick_update()
    print("\n✅ Context update complete. Remember to commit when ready.")

if __name__ == "__main__":
    main()