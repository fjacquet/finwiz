"""
Template Variable Documentation System.

This module scans task configuration files for template variables and documents
them for developers. CrewAI crews receive inputs via kickoff(inputs={...}), not
via __init__ parameters.

Requirement 14: Template Variable Validation
- Scan task configs for {variable} patterns
- Document required inputs for each crew
- Provide clear guidance on kickoff() usage
"""

import re
from pathlib import Path

import yaml

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""

    pass


class TemplateVariableValidator:
    """
    Documents template variables in task configurations.

    Scans tasks.yaml files for {variable} placeholders and documents what
    inputs each crew expects via kickoff(inputs={...}).
    """

    def __init__(self, crews_dir: Path | None = None):
        """
        Initialize the template variable validator.

        Args:
            crews_dir: Path to crews directory (defaults to src/finwiz/crews)

        """
        if crews_dir is None:
            # Default to src/finwiz/crews
            current_file = Path(__file__)
            src_dir = current_file.parent.parent
            crews_dir = src_dir / "crews"

        self.crews_dir = Path(crews_dir)

    def scan_task_configs(self, tasks_yaml_path: Path) -> set[str]:
        """
        Extract all {variable} patterns from a tasks.yaml file.

        Args:
            tasks_yaml_path: Path to tasks.yaml file

        Returns:
            Set of variable names found in template strings

        Example:
            For "Analyze {ticker} of type {asset_class}"
            Returns: {"ticker", "asset_class"}

        """
        try:
            with open(tasks_yaml_path, encoding="utf-8") as f:
                tasks_config = yaml.safe_load(f)

            if not tasks_config:
                return set()

            # Pattern to match {variable_name}
            pattern = re.compile(r"\{(\w+)\}")
            variables = set()

            # Recursively search for template variables in all string values
            def extract_variables(obj):
                if isinstance(obj, str):
                    matches = pattern.findall(obj)
                    variables.update(matches)
                elif isinstance(obj, dict):
                    for value in obj.values():
                        extract_variables(value)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_variables(item)

            extract_variables(tasks_config)

            logger.debug(f"Found {len(variables)} template variables in {tasks_yaml_path.name}: {sorted(variables)}")

            return variables

        except Exception as e:
            logger.error(f"Failed to scan {tasks_yaml_path}: {e}")
            return set()

    def document_crew(self, crew_dir: Path) -> list[str]:
        """
        Document a single crew's required inputs.

        Args:
            crew_dir: Path to crew directory

        Returns:
            List of info messages (empty if no template variables)

        """
        info = []
        crew_name = crew_dir.name

        # Check if tasks.yaml exists
        tasks_yaml = crew_dir / "config" / "tasks.yaml"
        if not tasks_yaml.exists():
            logger.debug(f"{crew_name}: No tasks.yaml found, skipping")
            return info

        # Extract template variables from tasks.yaml
        template_variables = self.scan_task_configs(tasks_yaml)

        if not template_variables:
            logger.debug(f"{crew_name}: No template variables found")
            return info

        # Document required inputs
        info.append(f"✓ {crew_name}: Requires kickoff(inputs={{...}}) with: {sorted(template_variables)}")

        logger.debug(f"{crew_name}: Documented {len(template_variables)} required inputs")

        return info

    def document_all_crews(self) -> tuple[bool, list[str]]:
        """
        Document all crews in the crews directory.

        Returns:
            Tuple of (success, info_messages)
            - success: Always True (documentation only)
            - info_messages: List of documentation messages

        """
        all_info = []

        if not self.crews_dir.exists():
            logger.warning(f"Crews directory not found: {self.crews_dir}")
            return True, all_info

        # Iterate through all crew directories
        for crew_dir in self.crews_dir.iterdir():
            if not crew_dir.is_dir():
                continue

            # Skip __pycache__ and other non-crew directories
            if crew_dir.name.startswith("__") or crew_dir.name.startswith("."):
                continue

            # Document this crew
            crew_info = self.document_crew(crew_dir)
            all_info.extend(crew_info)

        if all_info:
            logger.info(f"📋 Documented template variables for {len(all_info)} crews")
        else:
            logger.info("📋 No template variables found in any crews")

        return True, all_info

    def validate_at_startup(self) -> None:
        """
        Document template variables at system startup.

        This method scans all crews and logs what inputs they expect via
        kickoff(inputs={...}). It does not block startup.
        """
        logger.info("🔍 Scanning template variables in crew configurations...")

        success, info_messages = self.document_all_crews()

        if info_messages:
            logger.info("\n📋 Crew Input Requirements:")
            for msg in info_messages:
                logger.info(f"  {msg}")
            logger.info("\n💡 Remember: Pass these inputs via crew.crew().kickoff(inputs={...})")
        else:
            logger.info("✅ No template variables found (crews use no dynamic inputs)")


def validate_template_variables_at_startup() -> None:
    """
    Document template variables at startup.

    This scans all crews and logs what inputs they expect. It does not block
    startup - it's informational only.
    """
    validator = TemplateVariableValidator()
    validator.validate_at_startup()
