"""
Handles loading YAML configurations for the FinWiz project.

This module provides centralized utilities to load YAML files,
including a specialized function for injecting shared agent
guidelines into agent configurations. This approach ensures
consistency and maintainability by decoupling configuration
loading from the crew definitions and removing dependencies
on the internal 'crewai.project.config' object.
"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml


def _get_config_path(relative_path: str) -> Path:
    """
    Construct the absolute path to a configuration file.

    Args:
        relative_path: The path to the config file relative to the 'crews' directory,
                       e.g., 'stock_crew/config/agents.yaml'.

    Returns:
        The absolute path to the configuration file.
    """
    # Assumes that 'crews' directory is a sibling of the 'utils' directory.
    base_path = Path(__file__).parent.parent / "crews"
    return base_path / relative_path


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load a generic YAML configuration file.

    Args:
        config_path: The relative path to the YAML file.

    Returns:
        A dictionary containing the configuration.
    """
    full_path = _get_config_path(config_path)
    try:
        with open(full_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            if not isinstance(config, dict) or not config:
                raise ValueError(
                    f"Config file at {full_path} is empty or not a valid dictionary."
                )
            return config
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Config file not found at {full_path}") from e


def load_config_with_guidelines(config_path: str) -> Dict[str, Any]:
    """
    Load an agent YAML configuration and inject shared guidelines.

    This function reads a specified agent YAML file, injects the common
    research guidelines from 'configs/guidelines.md' into the 'backstory'
    of each agent, and returns the modified configuration.

    Args:
        config_path: The relative path to the agent configuration YAML file.

    Returns:
        A dictionary containing the agent configurations with guidelines injected.
    """
    # Load the agent configurations
    agents_config = load_yaml_config(config_path)

    # Construct the path to the guidelines file
    guidelines_path = (
        Path(__file__).parent.parent.parent.parent / "docs" / "agent_handbook.md"
    )

    # Read the shared guidelines
    with open(guidelines_path, "r", encoding="utf-8") as file:
        guidelines = file.read()

    # Inject guidelines into each agent's backstory
    for agent_name in agents_config.keys():
        if "backstory" in agents_config[agent_name]:
            agents_config[agent_name]["backstory"] += f"\n\n{guidelines}"
        else:
            agents_config[agent_name]["backstory"] = guidelines

    return agents_config
