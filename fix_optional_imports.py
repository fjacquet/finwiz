#!/usr/bin/env python3
"""Add missing Optional imports to schema files."""
import re
from pathlib import Path

def add_optional_import(file_path):
    """Add Optional import if it's used but not imported."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if Optional is used but not imported
    has_optional_usage = 'Optional[' in content
    has_optional_import = 'from typing import' in content and 'Optional' in content
    
    if has_optional_usage and not has_optional_import:
        # Find the typing import line
        import_pattern = r'(from typing import [^\n]+)'
        import_match = re.search(import_pattern, content)
        if import_match:
            old_import = import_match.group(1)
            # Handle both single-line and multi-line imports
            if '(' in old_import:
                new_import = old_import.replace(')', ', Optional)')
            else:
                new_import = old_import + ', Optional'
            content = content.replace(old_import, new_import, 1)
            
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
            if add_optional_import(py_file):
                fixed_files.append(str(py_file))
                print(f"Added Optional import to: {py_file}")
        except Exception as e:
            print(f"Error processing {py_file}: {e}")

print(f"\nTotal files fixed: {len(fixed_files)}")