# FinWiz Design Principles

## Overview

FinWiz is designed to be elegant and minimalist, like a haiku. 
It works with crewai as a flow of tasks and as the fondation of all.
This document outlines the core principles that guide its development.

## Core Principles

### Simple and Easy to Understand

- Code should be self-explanatory
- Functions should have a single responsibility
- Class and function names should clearly describe their purpose
- Comments and docstrings should explain "why" not just "what"

### Light as a Haiku

Like a haiku poem with its strict form of simplicity and elegance:

- Minimal dependencies
- Concise implementations
- Elegant solutions over complex ones
- Purposeful design choices

### CrewAI Flow Design Principles

- Clear separation between state and behavior
- Explicit flow transitions
- Parallel processing where appropriate
- Event-driven architecture

### Configuration-Driven Design

- Separate code from configuration using YAML files
- Use CrewAI decorators (@agent, @task, @crew) with config dictionaries
- Maintain strict separation between agent/task definitions and their parameters
- Configuration should be externally modifiable without code changes
- Default to configuration-driven approach, with coded fallbacks for robustness

### KISS (Keep It Simple, Stupid)

- Avoid premature optimization
- Choose straightforward solutions over clever ones
- Minimize complexity in algorithms and structures
- Favor readability over brevity

### YAGNI (You Aren't Gonna Need It)

- Only implement features that are immediately necessary
- Avoid speculative generality
- Refactor when patterns emerge, not before
- Focus on solving the current problem well

### DRY (Don't Repeat Yourself)

- Extract common functionality into helper methods
- Use inheritance and composition appropriately
- Maintain a single source of truth for data
- Leverage patterns like the template method when appropriate

## Code Structure Guidelines

1. **State Management**
   - Keep state immutable where possible
   - Document state transitions clearly
   - Minimize global state

2. **Flow Design**
   - Use descriptive names for flow steps
   - Document dependencies between steps
   - Keep flows linear where possible

3. **Error Handling**
   - Fail fast and explicitly
   - Provide meaningful error messages
   - Handle edge cases gracefully

4. **Documentation**
   - Document public interfaces thoroughly
   - Include examples where appropriate
   - Keep documentation up-to-date with code changes

5. **Module Organization**
   - Split utility functions into separate modules by functionality
   - Use empty `__init__.py` files for package structure
   - Prefer explicit imports from specific modules over package-level imports
   - Place all imports at the top of the file, never inline within functions or methods
   - Group related functionality in dedicated directories

6. **Project Directory Layout**
   - The `src` directory should contain only Python source code (e.g., the main application package `finwiz`, tools, etc.).
   - Data files, logs, outputs, archives, and other runtime artifacts should be stored in directories at the project root (e.g., `knowledge/`, `logs/`, `output/`, `archive/`, `storage/`).
   - Configuration in `settings.py` should define the paths to these root-level artifact directories. This keeps the source code separate from generated data and improves clarity.

7. **Python Package and Workflow Management**
   - Use `uv` for all Python package and virtual environment operations (e.g., `uv pip install`, `uv venv`).
   - Run individual Python scripts using `uv run python <script.py>`.
   - To execute the main project workflow, use the `crewai flow kickoff` command from the project root. This is the standard way to run the entire sequence of crews.

     ```bash
     crewai flow kickoff
     ```

   - Maintain consistent package versions across development environments.

8. **Report Generation**
   - Generate reports in HTML format for rich presentation
   - Always include UTF-8 encoding declarations to handle special characters and emojis
   - Use emojis strategically to enhance readability and visual appeal
   - Ensure cross-browser compatibility with proper HTML5 standards
   - Structure reports with clear sections and a logical flow of information

## Implementation Examples

### Good Example - DRY Principle

```python
# Instead of repeating file processing logic:
def _process_files(self, file_list: List[str], file_type: str) -> None:
    """Process files of a specific type."""
    print(f"Indexing {file_type}")
    for file in file_list:
        print(Path(file).name)
        archive_files(file)

# Then use it in specific handlers:
def index_text(self):
    self._process_files(self.state.document_state.list_txt, "text")
```

### Good Example - KISS Principle

```python
# Simple, direct approach to file archiving
def archive_files(file: str) -> None:
    """Move processed files to an archive directory."""
    knowledge_dir = "knowledge"
    archive_dir = "archive"
    
    if not os.path.exists(knowledge_dir):
        return
        
    rel_path = os.path.relpath(file, knowledge_dir)
    dest_dir = os.path.join(archive_dir, os.path.dirname(rel_path))
    os.makedirs(dest_dir, exist_ok=True)
    
    dest_file = os.path.join(archive_dir, rel_path)
    shutil.move(file, dest_file)
```

### Good Example - Module Organization

```text
src/finwiz/
├── utils/                  # Utilities package
│   ├── __init__.py         # Empty file to mark as package
│   ├── file_finder.py      # File discovery utilities
│   ├── file_archiver.py    # File archiving utilities
│   └── file_processor.py   # File processing utilities
```

```python
# In main.py - Explicit imports from specific modules
from finwiz.utils.file_finder import find_files
from finwiz.utils.file_processor import process_files

# In file_processor.py - Importing from other utility modules
from finwiz.utils.file_archiver import archive_files
```

### Good Example - KISS and "Light as a Haiku" with Yahoo Finance Tools

Instead of having a single monolithic file with multiple tools:

```text
src/finwiz/tools/
├── __init__.py             # Empty file to mark as package
├── yahoo_ticker_info_tool.py    # Specific tool for ticker information
├── yahoo_history_tool.py        # Specific tool for historical data
├── yahoo_company_info_tool.py   # Specific tool for company information
├── yahoo_etf_holdings_tool.py   # Specific tool for ETF holdings
└── yahoo_news_tool.py           # Specific tool for financial news
```

```python
# In research_crew.py - Explicit imports for each tool
from finwiz.tools.yahoo_ticker_info_tool import YahooFinanceTickerInfoTool
from finwiz.tools.yahoo_history_tool import YahooFinanceHistoryTool
from finwiz.tools.yahoo_company_info_tool import YahooFinanceCompanyInfoTool
from finwiz.tools.yahoo_etf_holdings_tool import YahooFinanceETFHoldingsTool
from finwiz.tools.yahoo_news_tool import YahooFinanceNewsTool

# Each tool has a single responsibility and can be used independently
ticker_info_tool = YahooFinanceTickerInfoTool()
history_tool = YahooFinanceHistoryTool()
company_info_tool = YahooFinanceCompanyInfoTool()
etf_holdings_tool = YahooFinanceETFHoldingsTool()
news_tool = YahooFinanceNewsTool()
```

### Good Example - HTML Report Generation with Emojis

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PowerFlex Analysis Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .emoji-header {
            font-size: 1.5em;
            margin-right: 10px;
        }
        .key-point {
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 10px 15px;
            margin: 15px 0;
        }
        .toc {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>🔍 PowerFlex Analysis Report</h1>
    <p><strong>Date:</strong> June 9, 2025</p>
    
    <div class="toc">
        <h2>📋 Table of Contents</h2>
        <ul>
            <li><a href="#summary">📊 Executive Summary</a></li>
            <li><a href="#benefits">🌟 Key Benefits</a></li>
            <li><a href="#use-cases">🛠️ Proven Use Cases</a></li>
            <li><a href="#conclusion">🏁 Conclusion</a></li>
        </ul>
    </div>
    
    <section id="summary">
        <h2><span class="emoji-header">📊</span>Executive Summary</h2>
        <p>This report addresses the question: <strong>"What are the top 5 reasons to buy PowerFlex? What are the proven benefits and use cases?"</strong></p>
        <!-- Report content continues... -->
    </section>
</body>
</html>
```
