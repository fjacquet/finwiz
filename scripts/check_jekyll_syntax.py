#!/usr/bin/env python3
"""
Check for Jekyll/Liquid syntax errors in documentation.
Finds Jinja2 template syntax that isn't properly wrapped with {% raw %} tags.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def check_file(file_path: Path) -> List[Tuple[int, str]]:
    """
    Check a markdown file for unprotected Jinja2 syntax.
    
    Returns:
        List of (line_number, line_content) tuples for errors found
    """
    errors = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    in_raw_block = False
    in_code_block = False
    code_block_lang = None
    
    # Patterns to detect Jinja2 syntax
    jinja_pattern = re.compile(r'{%|{{|\|format\(|is defined')
    raw_start = re.compile(r'{%\s*raw\s*%}')
    raw_end = re.compile(r'{%\s*endraw\s*%}')
    code_block_start = re.compile(r'^```(\w+)?')
    code_block_end = re.compile(r'^```\s*$')
    
    for i, line in enumerate(lines, 1):
        # Track raw blocks
        if raw_start.search(line):
            in_raw_block = True
            continue
        if raw_end.search(line):
            in_raw_block = False
            continue
        
        # Track code blocks
        code_start_match = code_block_start.match(line.strip())
        if code_start_match:
            if not in_code_block:
                in_code_block = True
                code_block_lang = code_start_match.group(1) or ''
            continue
        
        if code_block_end.match(line.strip()) and in_code_block:
            in_code_block = False
            code_block_lang = None
            continue
        
        # Check for Jinja2 syntax in code blocks that aren't protected
        if in_code_block and not in_raw_block:
            # Only check HTML/Jinja code blocks
            if code_block_lang in ('html', 'jinja', 'jinja2', ''):
                if jinja_pattern.search(line):
                    # Ignore lines that are just raw/endraw tags
                    if not (raw_start.search(line) or raw_end.search(line)):
                        errors.append((i, line.rstrip()))
    
    return errors


def main():
    """Main function to check all markdown files."""
    print(f"{BLUE}🔍 Checking for Jekyll/Liquid syntax errors in documentation...{NC}\n")
    
    docs_dir = Path('docs')
    if not docs_dir.exists():
        print(f"{RED}❌ docs/ directory not found{NC}")
        sys.exit(1)
    
    # Find all markdown files
    md_files = list(docs_dir.rglob('*.md'))
    
    if not md_files:
        print(f"{YELLOW}⚠️  No markdown files found in docs/{NC}")
        sys.exit(0)
    
    print(f"Scanning {len(md_files)} markdown files...\n")
    
    files_with_errors = {}
    
    for md_file in sorted(md_files):
        errors = check_file(md_file)
        if errors:
            files_with_errors[md_file] = errors
    
    # Report results
    if not files_with_errors:
        print(f"{GREEN}✅ No Jekyll/Liquid syntax errors found!{NC}")
        print(f"\nAll Jinja2 template syntax is properly wrapped with {YELLOW}{{%% raw %%}}{NC} tags.")
        return 0
    
    # Print errors
    print(f"{RED}❌ Found Jekyll/Liquid syntax errors in {len(files_with_errors)} file(s):{NC}\n")
    
    for file_path, errors in files_with_errors.items():
        try:
            rel_path = file_path.relative_to(Path.cwd())
        except ValueError:
            rel_path = file_path
        print(f"{RED}📄 {rel_path}{NC}")
        
        for line_num, line_content in errors:
            # Highlight Jinja2 syntax in the line
            highlighted = re.sub(
                r'({%.*?%}|{{.*?}})',
                f'{YELLOW}\\1{NC}',
                line_content.strip()
            )
            print(f"   Line {line_num}: {highlighted}")
        
        print()
    
    # Print fix instructions
    print(f"{BLUE}📝 To fix these errors:{NC}")
    print(f"   1. Wrap Jinja2 template code blocks with {YELLOW}{{%% raw %%}}{NC} and {YELLOW}{{%% endraw %%}}{NC} tags")
    print(f"   2. Example:")
    print(f"      {YELLOW}{{%% raw %%}}{NC}")
    print(f"      ```html")
    print(f"      {YELLOW}{{%% extends \"base.html\" %%}}{NC}")
    print(f"      {YELLOW}{{%% block content %%}}...{{%% endblock %%}}{NC}")
    print(f"      ```")
    print(f"      {YELLOW}{{%% endraw %%}}{NC}")
    print()
    
    return 1


if __name__ == '__main__':
    sys.exit(main())
