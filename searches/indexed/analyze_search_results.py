#!/usr/bin/env python3
"""Script to analyze and deduplicate search results from the search_indexed directory."""

import json
import os
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


def extract_results(data: Any) -> List[Dict[str, Any]]:
    """Extract results from different possible JSON structures."""
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if "news" in data and isinstance(data["news"], list):
            return data["news"]
        elif "results" in data and isinstance(data["results"], list):
            return data["results"]
        elif any(k in data for k in ["title", "link", "snippet"]):
            return [data]
    return []


def load_search_results(directory: str) -> List[Dict[str, Any]]:
    """Load all search results from JSON files in the specified directory."""
    all_results = []
    search_dir = Path(directory)

    # First try to find JSON files
    json_files = list(search_dir.glob("*.json"))

    # If no JSON files found, try .txt files
    if not json_files:
        json_files = list(search_dir.glob("*.txt"))

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    continue

                # Try to parse as JSON
                try:
                    data = json.loads(content)
                    results = extract_results(data)
                    if results:
                        all_results.extend(results)
                    else:
                        print(f"Warning: No results found in {file_path}")
                except json.JSONDecodeError:
                    # Try to parse as JSONL (one JSON object per line)
                    valid_lines = 0
                    for line in content.split("\n"):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            results = extract_results(data)
                            if results:
                                all_results.extend(results)
                                valid_lines += 1
                        except json.JSONDecodeError:
                            continue
                    if valid_lines == 0:
                        print(
                            f"Warning: Could not parse any valid JSON from {file_path}"
                        )
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    print(f"Found {len(json_files)} files with {len(all_results)} total results")

    return all_results


def normalize_text(text: str) -> str:
    """Normalize text for better comparison."""
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation
    return re.sub(r"\s+", " ", text)  # Normalize whitespace


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts."""
    return SequenceMatcher(None, text1, text2).ratio()


def find_duplicates(
    items: List[Dict[str, Any]],
    title_similarity_threshold: float = 0.7,  # Lowered from 0.8
    content_similarity_threshold: float = 0.6,  # Lowered from 0.7
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Find and remove duplicate items based on URL, title, and content similarity.
    Returns a tuple of (unique_items, duplicates).
    """  # noqa: D205
    seen_urls = set()
    seen_titles = set()
    unique_items = []
    duplicates = []

    # First pass: remove exact URL duplicates, but keep query params
    url_dupes_removed = []
    for item in items:
        url = item.get("link", "")
        # Only remove the query parameters that are likely tracking parameters
        url = re.sub(r"[?&](utm_|ref_|source=)[^&]*", "", url)
        url = url.rstrip("?&")  # Clean up any trailing ? or &
        if url not in seen_urls:
            seen_urls.add(url)
            url_dupes_removed.append(item)

    print(f"Removed {len(items) - len(url_dupes_removed)} exact URL duplicates")

    # Second pass: find similar titles and content
    for item in url_dupes_removed:
        title = normalize_text(item.get("title", ""))
        snippet = normalize_text(item.get("snippet", ""))
        is_duplicate = False

        for seen_item in unique_items:
            seen_title = normalize_text(seen_item.get("title", ""))
            seen_snippet = normalize_text(seen_item.get("snippet", ""))

            # Check title similarity
            title_sim = calculate_similarity(title, seen_title)

            # If titles are very similar, check content
            if title_sim > title_similarity_threshold:
                snippet_sim = calculate_similarity(snippet, seen_snippet)
                # Only mark as duplicate if both title and content are similar
                if snippet_sim > content_similarity_threshold:
                    is_duplicate = True
                    break

        if is_duplicate:
            duplicates.append(item)
        else:
            unique_items.append(item)

    return unique_items, duplicates


def save_results(
    unique_items: List[Dict[str, Any]],
    duplicates: List[Dict[str, Any]],
    output_dir: str = "output",
):
    """Save unique and duplicate results to JSON files."""
    os.makedirs(output_dir, exist_ok=True)

    # Save unique results
    unique_file = os.path.join(output_dir, "unique_results.json")
    with open(unique_file, "w", encoding="utf-8") as f:
        json.dump(unique_items, f, indent=2, ensure_ascii=False)

    # Save duplicates
    dupes_file = os.path.join(output_dir, "duplicates.json")
    with open(dupes_file, "w", encoding="utf-8") as f:
        json.dump(duplicates, f, indent=2, ensure_ascii=False)

    # Calculate statistics
    total = len(unique_items) + len(duplicates)
    duplicate_pct = (len(duplicates) / total * 100) if total > 0 else 0

    # Save summary
    summary = {
        "total_unique": len(unique_items),
        "total_duplicates": len(duplicates),
        "duplicate_percentage": round(duplicate_pct, 2),
        "unique_file": str(Path(unique_file).resolve()),
        "duplicates_file": str(Path(dupes_file).resolve()),
    }

    summary_file = os.path.join(output_dir, "summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


def main():
    # Configuration
    script_dir = Path(__file__).parent
    search_dir = script_dir / "search_indexed"
    output_dir = script_dir / "deduplicated_results"

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading search results from {search_dir}...")
    all_results = load_search_results(search_dir)
    print(f"Loaded {len(all_results)} total search results")

    if not all_results:
        print("No search results found. Exiting.")
        return

    if not all_results:
        print("No valid search results found. Please check the input files.")
        return

    print(f"Analyzing {len(all_results)} results for duplicates...")
    unique_items, duplicates = find_duplicates(all_results)

    print(f"\nResults:")
    print(f"- Total items: {len(all_results)}")
    print(f"- Unique items: {len(unique_items)}")
    print(f"- Duplicates found: {len(duplicates)}")
    print(f"- Duplicate percentage: {len(duplicates) / len(all_results) * 100:.1f}%")

    print(f"\nSaving results to {output_dir}...")
    summary = save_results(unique_items, duplicates, output_dir)

    print("\nAnalysis complete!")
    print(f"- Unique results saved to: {summary['unique_file']}")
    print(f"- Duplicates saved to: {summary['duplicates_file']}")
    print(f"- {summary['duplicate_percentage']:.1f}% of items were duplicates")


if __name__ == "__main__":
    main()
