#!/usr/bin/env python3
"""Fix Python 3.12 union syntax to Optional for CrewAI compatibility."""
import re
from pathlib import Path

def fix_union_types(file_path):
    """Fix Python 3.12 union syntax to Optional for CrewAI compatibility."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original = content
    
    # Check if Optional is already imported
    has_optional = 'from typing import' in content and 'Optional' in content
    
    # Pattern to match: type | None (including complex types)
    pattern = r':\s+([\w\[\], ]+)\s+\|\s+None'
    
    # Find all matches
    matches = list(re.finditer(pattern, content))
    
    if not matches:
        return False
    
    # Replace all occurrences
    content = re.sub(pattern, r': Optional[\1]', content)
    
    # Add Optional to imports if not present
    if not has_optional and 'from typing import' in content:
        # Find the typing import line
        import_pattern = r'(from typing import [^\n]+)'
        import_match = re.search(import_pattern, content)
        if import_match:
            old_import = import_match.group(1)
            if 'Optional' not in old_import:
                # Handle both single-line and multi-line imports
                if '(' in old_import:
                    new_import = old_import.replace(')', ', Optional)')
                else:
                    new_import = old_import + ', Optional'
                content = content.replace(old_import, new_import, 1)
    
    if content != original:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

# Process all Python files in schemas
schema_dir = Path('src/finwiz/schemas')
fixed_files = []

for py_file in schema_dir.rglob('*.py'):
    if '__pycache__' not in str(py_file):
        try:
            if fix_union_types(py_file):
                fixed_files.append(str(py_file))
                print(f"Fixed: {py_file}")
        except Exception as e:
            print(f"Error processing {py_file}: {e}")

print(f"\nTotal files fixed: {len(fixed_files)}")
