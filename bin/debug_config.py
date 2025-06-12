#!/usr/bin/env python3
"""
Debug script to examine configuration loading in the FinWiz application.
This script helps diagnose issues with YAML configuration file loading.
"""

import os
from pathlib import Path
import yaml
import sys

# Add the src directory to the Python path so we can import modules
sys.path.append(str(Path(__file__).parent / "src"))

from finwiz.utils.config_loader import load_config_with_guidelines, load_yaml_config, _get_config_path

def print_separator():
    print("\n" + "=" * 70 + "\n")

def debug_path_resolution():
    print("Debugging Path Resolution:")
    print(f"Current working directory: {os.getcwd()}")
    print(f"This file location: {Path(__file__).absolute()}")
    
    # Test different ways of resolving paths
    base_path = Path(__file__).parent / "src" / "finwiz" / "crews"
    print(f"Base path for crews: {base_path}")
    print(f"Does base path exist? {base_path.exists()}")
    
    stock_config_path = base_path / "stock_crew" / "config" / "agents.yaml"
    print(f"Stock agents config path: {stock_config_path}")
    print(f"Does stock agents config exist? {stock_config_path.exists()}")
    
    print_separator()

def debug_config_loader():
    print("Debugging Config Loader:")
    
    # Test internal path resolution
    try:
        resolved_path = _get_config_path("stock_crew/config/agents.yaml")
        print(f"Resolved path from _get_config_path: {resolved_path}")
        print(f"Does resolved path exist? {resolved_path.exists()}")
    except Exception as e:
        print(f"Error in _get_config_path: {e}")
    
    # Test actual loading with load_yaml_config
    try:
        print("\nAttempting to load stock crew agents config with load_yaml_config:")
        config = load_yaml_config("stock_crew/config/agents.yaml")
        print(f"Keys in config: {list(config.keys())}")
        if "market_technical_analyst" in config:
            print("'market_technical_analyst' key found!")
        else:
            print("'market_technical_analyst' key NOT found!")
    except Exception as e:
        print(f"Error in load_yaml_config: {e}")
    
    # Test loading with guidelines
    try:
        print("\nAttempting to load stock crew agents config with load_config_with_guidelines:")
        config_with_guidelines = load_config_with_guidelines("stock_crew/config/agents.yaml")
        print(f"Keys in config_with_guidelines: {list(config_with_guidelines.keys())}")
        if "market_technical_analyst" in config_with_guidelines:
            print("'market_technical_analyst' key found!")
        else:
            print("'market_technical_analyst' key NOT found!")
    except Exception as e:
        print(f"Error in load_config_with_guidelines: {e}")
    
    print_separator()

def debug_direct_yaml_load():
    print("Debugging Direct YAML Loading:")
    
    # Try to load the YAML file directly
    stock_config_path = Path(__file__).parent / "src" / "finwiz" / "crews" / "stock_crew" / "config" / "agents.yaml"
    
    try:
        print(f"Attempting to load YAML directly from: {stock_config_path}")
        with open(stock_config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            print(f"Direct YAML load successful. Keys: {list(config.keys())}")
            if "market_technical_analyst" in config:
                print("'market_technical_analyst' key found!")
            else:
                print("'market_technical_analyst' key NOT found!")
    except Exception as e:
        print(f"Error loading YAML directly: {e}")
    
    print_separator()

if __name__ == "__main__":
    print("\nFinWiz Configuration Debugging Script")
    print_separator()
    
    debug_path_resolution()
    debug_config_loader()
    debug_direct_yaml_load()
    
    print("Debugging complete.")
