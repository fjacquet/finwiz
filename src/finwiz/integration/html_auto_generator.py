"""
Automatic HTML generation from JSON crew outputs.

Generates HTML reports inline when crew outputs are saved.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def auto_generate_html(json_path: Path) -> Path | None:
    """
    Automatically generate HTML report from JSON output.

    Args:
        json_path: Path to the JSON file

    Returns:
        Path to generated HTML file, or None if generation failed

    """
    try:
        from finwiz.utils.json_to_html_converter import JsonToHtmlConverter

        # Initialize converter
        converter = JsonToHtmlConverter()

        # convert_file() takes only json_path and returns html_path string or None
        # HTML is saved in the same directory as the JSON file
        html_path_str = converter.convert_file(json_path)

        if html_path_str:
            logger.info(f"✅ Auto-generated HTML: {html_path_str}")
            return Path(html_path_str)
        else:
            logger.debug(f"HTML generation skipped for {json_path.name} (no template)")
            return None

    except Exception as e:
        logger.warning(f"Failed to auto-generate HTML for {json_path.name}: {e}")
        return None


def auto_generate_html_for_crew(crew_name: str, output_dir: Path = Path("output")) -> list[Path]:
    """
    Automatically generate HTML for all JSON files created by a crew.

    This function is called after a crew completes execution to convert
    all its JSON outputs to HTML.

    Args:
        crew_name: Name of the crew (e.g., "deep_analysis_stock")
        output_dir: Root output directory

    Returns:
        List of generated HTML file paths

    """
    html_files = []

    try:
        from finwiz.utils.json_to_html_converter import JsonToHtmlConverter

        # Find crew output directory
        crew_dir = output_dir / crew_name
        if not crew_dir.exists():
            logger.debug(f"No output directory found for {crew_name}")
            return html_files

        # Initialize converter
        converter = JsonToHtmlConverter()

        # Find all JSON files in crew directory
        json_files = list(crew_dir.glob("*.json"))
        if not json_files:
            logger.debug(f"No JSON files found in {crew_dir}")
            return html_files

        logger.info(f"Converting {len(json_files)} JSON files to HTML for {crew_name}")

        # Convert each JSON file
        for json_path in json_files:
            # Skip symlinks (e.g., *_latest.json)
            if json_path.is_symlink():
                continue

            html_path_str = converter.convert_file(json_path)
            if html_path_str:
                html_files.append(Path(html_path_str))
                logger.debug(f"✅ Generated: {Path(html_path_str).name}")

        if html_files:
            logger.info(f"✅ Generated {len(html_files)} HTML reports for {crew_name}")

        return html_files

    except Exception as e:
        logger.warning(f"Failed to auto-generate HTML for {crew_name}: {e}")
        return html_files
