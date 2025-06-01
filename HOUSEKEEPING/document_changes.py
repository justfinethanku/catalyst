#!/usr/bin/env python3
"""
Document specific changes or features
"""
import subprocess
from pathlib import Path
from datetime import datetime

def get_file_changes(filepath):
    """Get diff for a specific file"""
    try:
        diff = subprocess.check_output(['git', 'diff', filepath], text=True)
        if not diff:
            diff = subprocess.check_output(['git', 'diff', '--cached', filepath], text=True)
        return diff
    except:
        return None

def analyze_changes():
    """Analyze recent changes for documentation"""
    try:
        # Get list of modified files
        changed_files = subprocess.check_output(
            ['git', 'diff', '--name-only'], 
            text=True
        ).strip().split('\n')
        
        # Also check staged files
        staged_files = subprocess.check_output(
            ['git', 'diff', '--cached', '--name-only'], 
            text=True
        ).strip().split('\n')
        
        all_files = list(set(changed_files + staged_files))
        all_files = [f for f in all_files if f]  # Remove empty strings
        
        return all_files
    except:
        return []

def create_documentation_template(files):
    """Create a documentation template"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    template = f"""# Documentation Update - {timestamp}

## Overview
[Claude: Provide a brief overview of the changes]

## Changes by Component

"""
    
    # Group files by directory
    by_component = {}
    for f in files:
        component = Path(f).parts[0] if '/' in f else 'root'
        if component not in by_component:
            by_component[component] = []
        by_component[component].append(f)
    
    for component, component_files in by_component.items():
        template += f"### {component}\n"
        for f in component_files:
            template += f"- `{f}`: [Describe changes]\n"
        template += "\n"
    
    template += """## Technical Details
[Claude: Add any technical details that would help understand the implementation]

## API Changes
[Claude: Document any API changes if applicable]

## Testing Notes
[Claude: Add notes about testing requirements or considerations]

## Migration Guide
[Claude: If breaking changes, explain how to migrate]
"""
    
    return template

def main():
    print("📚 Document Changes Helper")
    print("=" * 50)
    
    # Get changed files
    files = analyze_changes()
    
    if not files:
        print("No changes detected to document.")
        return
    
    print(f"\n📝 Files with changes ({len(files)}):")
    for f in files:
        print(f"  - {f}")
    
    # Create documentation template
    template = create_documentation_template(files)
    
    # Suggest where to save
    doc_dir = Path("HOUSEKEEPING/DOCS")
    doc_dir.mkdir(exist_ok=True)
    doc_file = doc_dir / f"changes_{datetime.now().strftime('%Y%m%d')}.md"
    
    print(f"\n📄 Documentation template generated:")
    print("-" * 50)
    print(template)
    print("-" * 50)
    
    print(f"\n💡 ACTION REQUIRED:")
    print(f"1. CREATE {doc_file} with the above template")
    print(f"2. FILL IN all [Claude: ...] sections with actual change descriptions")
    print(f"3. UPDATE README.md if there are user-facing changes")
    print(f"4. UPDATE architecture.md if there are structural changes")
    print("\n⚡ EXECUTE THESE ACTIONS NOW - Don't just show the template!")

if __name__ == "__main__":
    main()