#!/usr/bin/env python3
"""
Add JSON output requirements to all crew task descriptions that use JSON output.

This script updates task descriptions in crews' tasks.yaml files to include
explicit JSON formatting requirements to prevent LLM from adding explanatory text.
"""

import re
from pathlib import Path

JSON_REQUIREMENTS = """
    🚨 JSON OUTPUT REQUIREMENTS 🚨
    - Output MUST be ONLY valid JSON - no explanatory text before or after
    - Your ENTIRE response must be a single JSON object starting with { and ending with }
    - Do NOT include any text, comments, or explanations outside the JSON
    - CRITICAL: NO trailing commas in JSON - last item in arrays/objects must NOT have comma"""


def has_json_requirements(content: str) -> bool:
    """Check if content already has JSON output requirements."""
    return "JSON OUTPUT REQUIREMENTS" in content


def add_json_requirements_to_task(task_yaml: str, task_name: str) -> str:
    """Add JSON requirements to a task description."""
    # Pattern to find the description section of a specific task
    pattern = rf"({task_name}:.*?description:\s*>)(.*?)(\n  \w+:)"

    def replace_description(match):
        task_header = match.group(1)
        description = match.group(2)
        next_field = match.group(3)

        # Check if already has requirements
        if "JSON OUTPUT REQUIREMENTS" in description:
            return match.group(0)  # No change

        # Add requirements at the end of description
        new_description = description.rstrip() + JSON_REQUIREMENTS
        return task_header + new_description + next_field

    return re.sub(pattern, replace_description, task_yaml, flags=re.DOTALL)


def process_crew_tasks(tasks_file: Path) -> bool:
    """Process a crew's tasks.yaml file to add JSON requirements."""
    print(f"\nProcessing: {tasks_file}")

    content = tasks_file.read_text()

    # Find all tasks with output_json or output_pydantic
    json_tasks = re.findall(r"^(\w+):\n(?:.*\n)*?  output_(?:json|pydantic):", content, re.MULTILINE)

    if not json_tasks:
        print("  No JSON output tasks found")
        return False

    print(f"  Found {len(json_tasks)} JSON output tasks: {', '.join(json_tasks)}")

    modified = False
    for task_name in json_tasks:
        if not re.search(rf"{task_name}:.*?JSON OUTPUT REQUIREMENTS", content, re.DOTALL):
            print(f"  Adding JSON requirements to: {task_name}")
            content = add_json_requirements_to_task(content, task_name)
            modified = True
        else:
            print(f"  Already has JSON requirements: {task_name}")

    if modified:
        tasks_file.write_text(content)
        print(f"  ✅ Updated {tasks_file}")
        return True
    else:
        print("  No changes needed")
        return False


def main():
    """Main function to process all crew task files."""
    crews_dir = Path(__file__).parent.parent / "src" / "finwiz" / "crews"

    crew_dirs = [
        "stock_crew",
        "etf_crew",
        "crypto_crew",
        "portfolio_rebalancing_crew",
        "report_crew",
        "deep_analysis",  # Already done manually
    ]

    updated_files = []

    for crew_name in crew_dirs:
        tasks_file = crews_dir / crew_name / "config" / "tasks.yaml"
        if tasks_file.exists():
            if process_crew_tasks(tasks_file):
                updated_files.append(str(tasks_file.relative_to(crews_dir.parent.parent)))
        else:
            print(f"⚠️  Tasks file not found: {tasks_file}")

    print("\n" + "=" * 80)
    if updated_files:
        print(f"✅ Updated {len(updated_files)} files:")
        for f in updated_files:
            print(f"  - {f}")
    else:
        print("No files needed updates")
    print("=" * 80)


if __name__ == "__main__":
    main()
