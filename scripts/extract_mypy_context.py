#!/usr/bin/env python3
"""
Extract mypy errors with minimal context for targeted AI fixes.

Creates batches of errors that can be processed by parallel agents
with minimal context to avoid saturating the context window.

Usage:
    python scripts/extract_mypy_context.py --batch-size 20
"""

import argparse
import json
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MypyError:
    """A single mypy error with context."""
    file: str
    line: int
    column: int
    error_code: str
    message: str
    context_before: list[str]
    error_line: str
    context_after: list[str]


def run_mypy() -> str:
    """Run mypy and capture output."""
    result = subprocess.run(
        ['uv', 'run', 'mypy', 'src/finwiz', '--ignore-missing-imports', '--show-column-numbers'],
        capture_output=True,
        text=True
    )
    return result.stdout + result.stderr


def parse_mypy_output(output: str) -> list[dict]:
    """Parse mypy output into structured errors."""
    errors = []
    # Pattern: file.py:line: error: message [error-code]
    # Also handles optional column: file.py:line:col: error: message [error-code]
    pattern = r'^(.+?):(\d+)(?::(\d+))?: error: (.+?) \[([^\]]+)\]$'

    for line in output.split('\n'):
        match = re.match(pattern, line)
        if match:
            errors.append({
                'file': match.group(1),
                'line': int(match.group(2)),
                'column': int(match.group(3)) if match.group(3) else 0,
                'message': match.group(4),
                'error_code': match.group(5),
            })

    return errors


def extract_context(file_path: str, line_num: int, context_lines: int = 3) -> dict:
    """Extract lines around an error."""
    try:
        with open(file_path, encoding='utf-8') as f:
            lines = f.readlines()

        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)

        return {
            'context_before': [l.rstrip() for l in lines[start:line_num-1]],
            'error_line': lines[line_num-1].rstrip() if line_num <= len(lines) else '',
            'context_after': [l.rstrip() for l in lines[line_num:end]],
        }
    except Exception as e:
        return {
            'context_before': [],
            'error_line': f'<could not read: {e}>',
            'context_after': [],
        }


def create_fix_prompt(errors: list[MypyError], file_path: str) -> str:
    """Create a focused prompt for an AI agent to fix errors."""
    prompt = f"""Fix the following mypy type errors in {file_path}.

For each error, provide ONLY the corrected line(s). Use the format:
LINE <number>: <corrected code>

Errors to fix:
"""
    for err in errors:
        prompt += f"""
--- Error at line {err.line} [{err.error_code}] ---
Message: {err.message}
Context:
```python
"""
        for i, line in enumerate(err.context_before, start=err.line - len(err.context_before)):
            prompt += f"{i:4d}: {line}\n"
        prompt += f"{err.line:4d}: {err.error_line}  # <-- FIX THIS LINE\n"
        for i, line in enumerate(err.context_after, start=err.line + 1):
            prompt += f"{i:4d}: {line}\n"
        prompt += "```\n"

    prompt += """
IMPORTANT:
- Only output the fixed lines, nothing else
- Use modern Python 3.10+ type hints (X | None instead of Optional[X])
- Add type annotations where missing
- Fix type mismatches by using proper types or casts
"""
    return prompt


def create_batches(errors: list[dict], batch_size: int) -> list[list[dict]]:
    """Group errors into batches by file, respecting batch size."""
    # Group by file first
    by_file = defaultdict(list)
    for err in errors:
        by_file[err['file']].append(err)

    batches = []
    current_batch = []
    current_size = 0

    for file_path, file_errors in sorted(by_file.items()):
        if current_size + len(file_errors) > batch_size and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_size = 0

        # Add file errors (keep file together if possible)
        if len(file_errors) <= batch_size:
            current_batch.extend(file_errors)
            current_size += len(file_errors)
        else:
            # File has too many errors, split it
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_size = 0

            for i in range(0, len(file_errors), batch_size):
                batches.append(file_errors[i:i + batch_size])

    if current_batch:
        batches.append(current_batch)

    return batches


def main():
    parser = argparse.ArgumentParser(description='Extract mypy errors with context')
    parser.add_argument('--batch-size', type=int, default=20,
                        help='Number of errors per batch (default: 20)')
    parser.add_argument('--output-dir', type=Path, default=Path('scripts/mypy_batches'),
                        help='Output directory for batches')
    parser.add_argument('--context-lines', type=int, default=3,
                        help='Lines of context around each error')
    parser.add_argument('--error-types', nargs='+', default=None,
                        help='Only include specific error types (e.g., arg-type call-arg)')
    args = parser.parse_args()

    print("Running mypy...")
    output = run_mypy()

    print("Parsing errors...")
    errors = parse_mypy_output(output)
    print(f"Found {len(errors)} errors")

    # Filter by error type if specified
    if args.error_types:
        errors = [e for e in errors if e['error_code'] in args.error_types]
        print(f"Filtered to {len(errors)} errors of types: {args.error_types}")

    # Add context to each error
    print("Extracting context...")
    for err in errors:
        context = extract_context(err['file'], err['line'], args.context_lines)
        err.update(context)

    # Create batches
    batches = create_batches(errors, args.batch_size)
    print(f"Created {len(batches)} batches")

    # Output batches
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Summary file
    summary = {
        'total_errors': len(errors),
        'num_batches': len(batches),
        'batch_size': args.batch_size,
        'error_types': args.error_types,
        'batches': []
    }

    for i, batch in enumerate(batches):
        batch_file = args.output_dir / f'batch_{i:03d}.json'
        prompt_file = args.output_dir / f'batch_{i:03d}_prompt.md'

        # Group by file for the prompt
        by_file = defaultdict(list)
        for err in batch:
            by_file[err['file']].append(MypyError(
                file=err['file'],
                line=err['line'],
                column=err['column'],
                error_code=err['error_code'],
                message=err['message'],
                context_before=err['context_before'],
                error_line=err['error_line'],
                context_after=err['context_after'],
            ))

        # Write batch JSON
        with open(batch_file, 'w') as f:
            json.dump(batch, f, indent=2)

        # Write prompt file
        with open(prompt_file, 'w') as f:
            for file_path, file_errors in by_file.items():
                f.write(create_fix_prompt(file_errors, file_path))
                f.write("\n\n" + "="*60 + "\n\n")

        summary['batches'].append({
            'batch_id': i,
            'num_errors': len(batch),
            'files': list(set(e['file'] for e in batch)),
        })

    # Write summary
    with open(args.output_dir / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nOutput written to {args.output_dir}/")
    print(f"  - {len(batches)} batch files (batch_XXX.json)")
    print(f"  - {len(batches)} prompt files (batch_XXX_prompt.md)")
    print("  - 1 summary file (summary.json)")

    # Print batch distribution
    print("\nBatch distribution:")
    for i, batch_info in enumerate(summary['batches'][:10]):
        print(f"  Batch {i}: {batch_info['num_errors']} errors in {len(batch_info['files'])} files")
    if len(batches) > 10:
        print(f"  ... and {len(batches) - 10} more batches")


if __name__ == '__main__':
    main()
