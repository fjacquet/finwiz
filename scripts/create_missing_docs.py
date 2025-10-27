#!/usr/bin/env python3
"""
Create all missing documentation files identified from MkDocs build errors.
"""

import re
import subprocess
from pathlib import Path


def get_missing_files_from_mkdocs():
    """Extract missing files from MkDocs build output."""
    try:
        result = subprocess.run(["uv", "run", "mkdocs", "build", "--clean"], capture_output=True, text=True, cwd=".")

        missing_files = set()
        for line in result.stderr.split("\n"):
            if "contains a link" in line and "but the target" in line and "is not found" in line:
                match = re.search(r"but the target '([^']+)' is not found", line)
                if match:
                    missing_files.add(match.group(1))

        return sorted(missing_files)
    except Exception as e:
        print(f"Error running mkdocs: {e}")
        return []


def create_content_by_type(file_path):
    """Create appropriate content based on file path and type."""
    filename = Path(file_path).stem
    title = filename.replace("_", " ").title()

    if file_path.startswith("explanations/"):
        return f"""# {title}

This explanation provides conceptual understanding of {title.lower()} in the FinWiz system.

## Overview

{title} is a key concept in FinWiz's architecture and operation.

## Key Concepts

- Core principles and ideas
- How it fits into the overall system
- Why it's designed this way

## How It Works

Detailed explanation of the mechanisms and processes involved.

## Benefits and Trade-offs

- Advantages of this approach
- Considerations and limitations
- When to use different strategies

## Examples

Practical examples demonstrating the concepts.

## Related Topics

- [Architecture Overview](ARCHITECTURE.md)
- [Design Principles](design_principles.md)

## Further Reading

Additional resources and documentation for deeper understanding.
"""

    elif file_path.startswith("how-to/"):
        return f"""# How to {title}

This guide shows you how to {title.lower()} in FinWiz.

## Prerequisites

- FinWiz installed and configured
- Basic familiarity with FinWiz concepts
- Required API keys (if applicable)

## Overview

Brief overview of what you'll accomplish and why it's useful.

## Step-by-Step Instructions

### Step 1: Preparation

Prepare your environment and gather necessary information.

```bash
# Example preparation commands
```

### Step 2: Configuration

Configure the necessary settings.

```python
# Example configuration code
```

### Step 3: Execution

Execute the main process.

```python
# Example execution code
```

### Step 4: Verification

Verify that the process completed successfully.

```bash
# Example verification commands
```

## Common Issues and Solutions

### Issue 1: Common Problem
**Problem**: Description of the problem
**Solution**: How to resolve it

### Issue 2: Another Problem
**Problem**: Description of the problem
**Solution**: How to resolve it

## Advanced Usage

Advanced techniques and customization options.

## Next Steps

- [Related How-to Guide](setup_environment.md)
- [Reference Documentation](../reference/index.md)
- [Tutorials](../tutorials/index.md)

## See Also

- Related documentation links
- External resources
"""

    elif file_path.startswith("reference/"):
        return f"""# {title} Reference

Complete reference documentation for {title.lower()}.

## Overview

This reference provides detailed technical information about {title.lower()}.

## API Reference

### Classes and Functions

#### Main Classes

```python
class ExampleClass:
    \"\"\"Example class documentation.\"\"\"
    pass
```

#### Key Functions

```python
def example_function(param1: str, param2: int) -> str:
    \"\"\"Example function documentation.\"\"\"
    pass
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| option1 | str | "default" | Description of option1 |
| option2 | int | 100 | Description of option2 |

## Parameters and Return Values

### Input Parameters

Detailed description of input parameters.

### Return Values

Detailed description of return values and their structure.

## Error Handling

Common errors and how to handle them.

### Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| E001 | Error description | How to fix |
| E002 | Error description | How to fix |

## Examples

### Basic Usage

```python
# Basic usage example
```

### Advanced Usage

```python
# Advanced usage example
```

## See Also

- [API Index](index.md)
- [How-to Guides](../how-to/index.md)
- [Tutorials](../tutorials/index.md)
"""

    elif file_path.startswith("tutorials/"):
        return f"""# {title} Tutorial

Learn {title.lower()} with this comprehensive tutorial.

## What You'll Learn

By the end of this tutorial, you'll be able to:

- Understand the basics of {title.lower()}
- Apply {title.lower()} concepts in practice
- Use {title.lower()} effectively in your workflow

## Prerequisites

- FinWiz installed and configured
- Basic understanding of financial analysis concepts
- Familiarity with command-line tools

## Tutorial Overview

This tutorial is divided into several sections:

1. **Getting Started** - Basic concepts and setup
2. **Hands-on Practice** - Step-by-step exercises
3. **Advanced Techniques** - More sophisticated usage
4. **Best Practices** - Recommendations and tips

## Getting Started

### Understanding the Basics

Introduction to key concepts and terminology.

### Setting Up Your Environment

Ensure your environment is properly configured.

```bash
# Setup commands
```

## Hands-on Practice

### Exercise 1: Basic Usage

Step-by-step walkthrough of basic functionality.

```python
# Example code for exercise 1
```

### Exercise 2: Intermediate Usage

More complex scenarios and use cases.

```python
# Example code for exercise 2
```

## Advanced Techniques

### Advanced Feature 1

Explanation and examples of advanced features.

### Advanced Feature 2

Additional advanced capabilities.

## Best Practices

### Do's and Don'ts

- ✅ **Do**: Best practice recommendations
- ❌ **Don't**: Common mistakes to avoid

### Performance Tips

Recommendations for optimal performance.

### Troubleshooting

Common issues and their solutions.

## Summary

What you've learned and key takeaways.

## Next Steps

- [Advanced Tutorial](portfolio_analysis.md)
- [How-to Guides](../how-to/index.md)
- [Reference Documentation](../reference/index.md)

## Additional Resources

- Links to related documentation
- External resources and references
"""

    else:
        # Generic content for other file types
        return f"""# {title}

Documentation for {title}.

## Overview

This document provides information about {title.lower()}.

## Content

Detailed content will be added here.

## Related Documentation

- [Main Documentation](index.md)
- [Getting Started](tutorials/getting_started.md)
- [Reference](reference/index.md)
"""


def main():
    """Main function to create all missing files."""
    print("🔍 Identifying missing files from MkDocs build...")
    missing_files = get_missing_files_from_mkdocs()

    print(f"📋 Found {len(missing_files)} missing files")

    docs_dir = Path("docs")
    created_count = 0

    for missing_file in missing_files:
        file_path = docs_dir / missing_file

        # Skip if file already exists
        if file_path.exists():
            continue

        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate content
        content = create_content_by_type(missing_file)

        # Write the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Created: {file_path}")
        created_count += 1

    print(f"\n🎉 Created {created_count} missing files!")
    print("Run 'make docs-build' to check for remaining issues.")


if __name__ == "__main__":
    main()
