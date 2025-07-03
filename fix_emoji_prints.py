#!/usr/bin/env python3
"""
Script to replace emoji print statements with ASCII-safe alternatives.
"""

import os
import re
from pathlib import Path

def fix_emoji_prints():
    """Replace emoji print statements with ASCII-safe alternatives."""
    
    # Emoji replacements
    emoji_replacements = {
        "🚀": "",  # Remove rocket
        "📁": "",  # Remove folder
        "🐍": "",  # Remove snake
        "✅": "",  # Remove checkmark
        "❌": "",  # Remove X
        "⏰": "",  # Remove clock
        "💥": "",  # Remove explosion
        "📰": "",  # Remove newspaper
        "📊": "",  # Remove chart
        "📈": "",  # Remove trend
        "😨": "",  # Remove fear
        "🪙": "",  # Remove coin
        "📅": "",  # Remove calendar
        "⚠️": "",  # Remove warning
        "💾": "",  # Remove save
        "📋": "",  # Remove clipboard
    }
    
    # Get scripts directory
    scripts_dir = Path("scripts")
    
    if not scripts_dir.exists():
        print("Scripts directory not found")
        return
    
    # Process each Python file
    for py_file in scripts_dir.glob("*.py"):
        print(f"Processing {py_file}...")
        
        # Read file content
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace emojis
        original_content = content
        for emoji, replacement in emoji_replacements.items():
            content = content.replace(emoji, replacement)
        
        # Clean up double spaces that might result from emoji removal
        content = re.sub(r' +', ' ', content)
        
        # Write back if changed
        if content != original_content:
            with open(py_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Fixed emoji prints in {py_file}")
        else:
            print(f"  No changes needed in {py_file}")

if __name__ == "__main__":
    fix_emoji_prints()
    print("Emoji print statement cleanup completed!") 