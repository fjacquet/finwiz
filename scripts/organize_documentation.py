#!/usr/bin/env python3
"""
Documentation Organization Script

Reorganizes FinWiz documentation following Diátaxis framework:
- Tutorials (learning by doing)
- How-to Guides (solving problems)
- Reference (information lookup)
- Explanation (understanding concepts)
"""

import os
import shutil
from pathlib import Path


def create_doc_structure():
    """Create organized documentation structure."""
    doc_dirs = [
        "docs/tutorials",
        "docs/how-to",
        "docs/reference",
        "docs/explanations",
        "docs/archive/essential",  # Minimal essential archives
    ]

    for doc_dir in doc_dirs:
        Path(doc_dir).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created: {doc_dir}")


def categorize_documentation():
    """Categorize existing documentation by type."""
    # Reference documentation (API, schemas, commands)
    reference_docs = ["API_REFERENCE.md", "DEVELOPER_GUIDE.md", "docs/schemas/", "quantitative_analysis.md"]

    # How-to guides (solving specific problems)
    howto_docs = [
        "BATCH_PROCESSING.md",
        "PERFORMANCE_CONFIGURATION.md",
        "PERFORMANCE_OPTIMIZATION_GUIDE.md",
        "JINJA2_TEMPLATES.md",
        "PYTHON_SCORING_ENGINE.md",
        "MEMORY_MANAGEMENT.md",
    ]

    # Explanations (understanding concepts)
    explanation_docs = [
        "ARCHITECTURE.md",
        "DEEP_ANALYSIS_INTEGRATION.md",
        "DATA_QUALITY_AND_FLOW_GUIDE.md",
        "REPORT_AGGREGATION_DEVELOPER_GUIDE.md",
        "REPORT_FILE_STRUCTURE.md",
    ]

    # Tutorials (learning by doing)
    tutorial_docs = ["USER_GUIDE.md", "portfolio_holdings_analysis_user_guide.md"]

    return {"reference": reference_docs, "how-to": howto_docs, "explanations": explanation_docs, "tutorials": tutorial_docs}


def move_documentation(categorized_docs: dict[str, list[str]]):
    """Move documentation to appropriate categories."""
    for category, docs in categorized_docs.items():
        target_dir = f"docs/{category}"

        for doc in docs:
            source_path = f"docs/{doc}"
            if os.path.exists(source_path):
                if os.path.isdir(source_path):
                    # Move directory
                    target_path = f"{target_dir}/{Path(doc).name}"
                    if not os.path.exists(target_path):
                        shutil.move(source_path, target_path)
                        print(f"📁 Moved directory: {doc} → {category}/")
                else:
                    # Move file
                    target_path = f"{target_dir}/{doc}"
                    if not os.path.exists(target_path):
                        shutil.move(source_path, target_path)
                        print(f"📄 Moved: {doc} → {category}/")


def consolidate_implementation_summaries():
    """Consolidate task implementation summaries."""
    summaries = [
        "TASK_5_IMPLEMENTATION_SUMMARY.md",
        "TASK_6_IMPLEMENTATION_SUMMARY.md",
        "TASK_7_IMPLEMENTATION_SUMMARY.md",
        "TASK_8_IMPLEMENTATION_SUMMARY.md",
        "TASK_9_IMPLEMENTATION_SUMMARY.md",
        "TASK_10_IMPLEMENTATION_SUMMARY.md",
    ]

    # Create consolidated summary
    consolidated_content = "# Implementation Summaries\n\n"
    consolidated_content += "Consolidated task implementation summaries for reference.\n\n"

    for summary in summaries:
        source_path = f"docs/{summary}"
        if os.path.exists(source_path):
            with open(source_path) as f:
                content = f.read()

            consolidated_content += f"## {summary.replace('_', ' ').replace('.md', '')}\n\n"
            consolidated_content += content + "\n\n---\n\n"

            # Move to archive
            shutil.move(source_path, f"docs/archive/essential/{summary}")
            print(f"📄 Archived: {summary}")

    # Write consolidated summary
    with open("docs/reference/IMPLEMENTATION_SUMMARIES.md", "w") as f:
        f.write(consolidated_content)

    print("📄 Created: docs/reference/IMPLEMENTATION_SUMMARIES.md")


def create_documentation_index():
    """Create main documentation index."""
    index_content = """# FinWiz Documentation

Welcome to the FinWiz documentation. This documentation follows the [Diátaxis framework](https://diataxis.fr/) for clear, organized technical documentation.

## 📚 Documentation Categories

### 🎓 [Tutorials](tutorials/)
Learning-oriented guides that help you get started:
- [User Guide](tutorials/USER_GUIDE.md) - Getting started with FinWiz
- [Portfolio Analysis Guide](tutorials/portfolio_holdings_analysis_user_guide.md)

### 🔧 [How-to Guides](how-to/)
Problem-solving guides for specific tasks:
- [Batch Processing](how-to/BATCH_PROCESSING.md) - Process multiple assets efficiently
- [Performance Optimization](how-to/PERFORMANCE_OPTIMIZATION_GUIDE.md) - Optimize analysis speed
- [Template Configuration](how-to/JINJA2_TEMPLATES.md) - Customize report templates
- [Memory Management](how-to/MEMORY_MANAGEMENT.md) - Optimize memory usage

### 📖 [Reference](reference/)
Information-oriented reference material:
- [API Reference](reference/API_REFERENCE.md) - Complete API documentation
- [Developer Guide](reference/DEVELOPER_GUIDE.md) - Development standards
- [Schemas](reference/schemas/) - Data model specifications
- [Implementation Summaries](reference/IMPLEMENTATION_SUMMARIES.md) - Task completion records

### 💡 [Explanations](explanations/)
Understanding-oriented explanations of concepts:
- [Architecture](explanations/ARCHITECTURE.md) - System architecture overview
- [Deep Analysis Integration](explanations/DEEP_ANALYSIS_INTEGRATION.md) - Analysis workflow
- [Data Quality Guide](explanations/DATA_QUALITY_AND_FLOW_GUIDE.md) - Data validation concepts
- [Report Aggregation](explanations/REPORT_AGGREGATION_DEVELOPER_GUIDE.md) - Report generation

## 🚀 Quick Start

1. **New to FinWiz?** Start with [User Guide](tutorials/USER_GUIDE.md)
2. **Need to solve a problem?** Check [How-to Guides](how-to/)
3. **Looking for specific information?** Browse [Reference](reference/)
4. **Want to understand concepts?** Read [Explanations](explanations/)

## 📋 Development

- **Code Standards**: See [Developer Guide](reference/DEVELOPER_GUIDE.md)
- **Architecture**: See [Architecture](explanations/ARCHITECTURE.md)
- **Performance**: See [Performance Optimization](how-to/PERFORMANCE_OPTIMIZATION_GUIDE.md)

---

**Last Updated**: 2025-01-26
"""

    with open("docs/README.md", "w") as f:
        f.write(index_content)

    print("📄 Created: docs/README.md (main index)")


def main():
    """Execute documentation organization."""
    print("📚 Organizing FinWiz Documentation...")
    print("=" * 50)

    # Create structure
    create_doc_structure()

    # Categorize and move docs
    categorized_docs = categorize_documentation()
    move_documentation(categorized_docs)

    # Consolidate summaries
    consolidate_implementation_summaries()

    # Create index
    create_documentation_index()

    print("\n" + "=" * 50)
    print("✨ Documentation Organization Complete!")
    print("   • Created Diátaxis-compliant structure")
    print("   • Categorized documentation by purpose")
    print("   • Consolidated implementation summaries")
    print("   • Created comprehensive index")
    print("\n📚 Documentation is now well-organized and discoverable!")


if __name__ == "__main__":
    main()
