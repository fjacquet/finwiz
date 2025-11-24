#!/usr/bin/env python3
"""
Automatically fix all Jekyll/Liquid syntax errors by wrapping Jinja2 templates with {% raw %} tags.
"""

import re
import sys
from pathlib import Path

# ANSI color codes
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def fix_file(file_path: Path) -> bool:
    """
    Fix a markdown file by wrapping unprotected Jinja2 syntax with {% raw %} tags.

    Returns:
        True if file was modified, False otherwise

    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    original_content = content
    lines = content.split("\n")

    in_raw_block = False
    in_code_block = False
    code_block_lang = None
    code_block_start_line = None
    modified = False

    # Patterns
    jinja_pattern = re.compile(r"{%|{{|\|format\(|is defined")
    raw_start = re.compile(r"{%\s*raw\s*%}")
    raw_end = re.compile(r"{%\s*endraw\s*%}")
    code_block_start = re.compile(r"^```(\w+)?")
    code_block_end = re.compile(r"^```\s*$")

    i = 0
    while i < len(lines):
        line = lines[i]

        # Track raw blocks
        if raw_start.search(line):
            in_raw_block = True
            i += 1
            continue
        if raw_end.search(line):
            in_raw_block = False
            i += 1
            continue

        # Track code blocks
        code_start_match = code_block_start.match(line.strip())
        if code_start_match and not in_code_block:
            in_code_block = True
            code_block_lang = code_start_match.group(1) or ""
            code_block_start_line = i
            i += 1
            continue

        if code_block_end.match(line.strip()) and in_code_block:
            # Check if this code block needs wrapping
            if not in_raw_block and code_block_lang in ("html", "jinja", "jinja2", "liquid", ""):
                # Check if any line in this block has Jinja2 syntax
                has_jinja = False
                for j in range(code_block_start_line + 1, i):
                    if jinja_pattern.search(lines[j]):
                        has_jinja = True
                        break

                if has_jinja:
                    # Wrap this code block with {% raw %} tags
                    lines.insert(code_block_start_line, "{% raw %}")
                    i += 1  # Adjust index for inserted line
                    lines.insert(i + 1, "{% endraw %}")
                    i += 1  # Adjust index for inserted line
                    modified = True
                    print(f"  {YELLOW}→{NC} Wrapped code block at line {code_block_start_line + 1}")

            in_code_block = False
            code_block_lang = None
            code_block_start_line = None
            i += 1
            continue

        i += 1

    if modified:
        # Write back to file
        new_content = "\n".join(lines)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    return False


def main():
    """Main function to fix all markdown files."""
    print(f"{BLUE}🔧 Fixing Jekyll/Liquid syntax errors in documentation...{NC}\n")

    docs_dir = Path("docs")
    if not docs_dir.exists():
        print(f"{RED}❌ docs/ directory not found{NC}")
        sys.exit(1)

    # Find all markdown files
    md_files = list(docs_dir.rglob("*.md"))

    if not md_files:
        print(f"{YELLOW}⚠️  No markdown files found in docs/{NC}")
        sys.exit(0)

    print(f"Scanning {len(md_files)} markdown files...\n")

    files_modified = []

    for md_file in sorted(md_files):
        try:
            rel_path = md_file.relative_to(Path.cwd())
        except ValueError:
            rel_path = md_file

        if fix_file(md_file):
            files_modified.append(rel_path)
            print(f"{GREEN}✅ Fixed: {rel_path}{NC}\n")

    # Report results
    print()
    if not files_modified:
        print(f"{GREEN}✅ No files needed fixing!{NC}")
        return 0

    print(f"{GREEN}✅ Fixed {len(files_modified)} file(s):{NC}")
    for file_path in files_modified:
        print(f"   - {file_path}")

    print(f"\n{BLUE}📝 Next steps:{NC}")
    print("   1. Review the changes: git diff")
    print("   2. Run validation: python scripts/check_jekyll_syntax.py")
    print("   3. Commit the fixes: git add docs/ && git commit -m 'docs: Fix Jekyll/Liquid syntax errors'")

    return 0


if __name__ == "__main__":
    sys.exit(main())
