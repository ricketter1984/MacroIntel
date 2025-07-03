#!/usr/bin/env python3
"""
Script to fix indentation issues caused by emoji removal.
"""

import re
from pathlib import Path

def fix_indentation():
    """Fix indentation issues in Python files."""
    
    scripts_dir = Path("scripts")
    
    for py_file in scripts_dir.glob("*.py"):
        print(f"Fixing indentation in {py_file}...")
        
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix function definitions that lost their colons
        content = re.sub(r'def (\w+)\(\):\s*\n\s*"""', r'def \1():\n    """', content)
        
        # Fix try blocks
        content = re.sub(r'try:\s*\n\s*from', r'try:\n        from', content)
        
        # Fix if/else blocks
        content = re.sub(r'if (\w+):\s*\n\s*print', r'if \1:\n            print', content)
        content = re.sub(r'else:\s*\n\s*print', r'else:\n            print', content)
        
        # Fix except blocks
        content = re.sub(r'except (\w+) as (\w+):\s*\n\s*print', r'except \1 as \2:\n        print', content)
        
        # Fix return statements
        content = re.sub(r'return {\s*\n\s*"', r'return {\n            "', content)
        
        # Fix with statements
        content = re.sub(r'with open\(([^)]+)\) as (\w+):\s*\n\s*(\w+)', r'with open(\1) as \2:\n            \3', content)
        
        # Fix main function
        content = re.sub(r'def main\(\):\s*\n\s*"""', r'def main():\n    """', content)
        
        # Fix if __name__ block
        content = re.sub(r'if __name__ == "__main__":\s*\n\s*(\w+)', r'if __name__ == "__main__":\n    \1', content)
        
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  Fixed {py_file}")

if __name__ == "__main__":
    fix_indentation()
    print("Indentation fixes completed!") 