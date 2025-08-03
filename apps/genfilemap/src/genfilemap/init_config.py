
"""
Configuration initialization module for GenFileMap.

This module provides functions for initializing global and project-specific
configuration files with appropriate default settings.
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any, Optional

from genfilemap.config import (
    save_config,
    get_user_config_dir,
    get_user_cache_dir,
    get_user_data_dir,
    get_user_log_dir,
    DEFAULT_CONFIG_PATH,
    DEFAULT_PROJECT_CONFIG_PATH
)

def create_project_config(config_path: str) -> Dict[str, Any]:
    """
    Create a project-specific configuration file.

    Args:
        config_path: Path where the configuration file will be created

    Returns:
        The created configuration dictionary
    """
    project_config = {
        "output_dirs": {
            "maps": ".genfilemap/maps",
            "logs": ".genfilemap/logs",
            "cache": ".genfilemap/cache",
            "reports": ".genfilemap/reports",
            "map_reports": ".genfilemap/map_reports"
        },
        "project_map_output": ".genfilemap/maps/PROJECT_FILE_MAP.md",
        "output": {
            "template": "standard",
            "template_dir": ".genfilemap/templates",
            "schema_path": ".genfilemap/schemas/schema.json",
            "report_path": ".genfilemap/reports/filemap_report.json"
        }
    }

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)

    # Save configuration
    save_config(project_config, config_path)
    logging.info(f"Created project configuration at: {config_path}")

    return project_config

def create_global_config(config_path: str) -> Dict[str, Any]:
    """
    Create a global configuration file.

    Args:
        config_path: Path where the configuration file will be created

    Returns:
        The created configuration dictionary
    """
    # Use platform-appropriate directories
    global_config = {
        "output_dirs": {
            "maps": os.path.join(get_user_data_dir(), "maps"),
            "logs": get_user_log_dir(),
            "cache": get_user_cache_dir(),
            "config": get_user_config_dir(),
            "templates": os.path.join(get_user_data_dir(), "templates"),
            "schemas": os.path.join(get_user_data_dir(), "schemas")
        },
        "project_map_output": os.path.join(get_user_data_dir(), "maps/PROJECT_FILE_MAP.md"),
        "output": {
            "template": "standard",
            "template_dir": os.path.join(get_user_data_dir(), "templates"),
            "schema_path": os.path.join(get_user_data_dir(), "schemas/schema.json"),
            "report_path": os.path.join(get_user_data_dir(), "reports/filemap_report.json")
        }
    }

    # Create all necessary directories
    for dir_path in global_config["output_dirs"].values():
        os.makedirs(dir_path, exist_ok=True)

    os.makedirs(os.path.dirname(global_config["project_map_output"]), exist_ok=True)
    os.makedirs(os.path.dirname(global_config["output"]["schema_path"]), exist_ok=True)
    os.makedirs(global_config["output"]["template_dir"], exist_ok=True)
    os.makedirs(os.path.dirname(global_config["output"]["report_path"]), exist_ok=True)

    # Save configuration
    os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
    save_config(global_config, config_path)
    logging.info(f"Created global configuration at: {config_path}")

    return global_config

def main():
    """
    Main entry point for initializing configuration files.
    """
    parser = argparse.ArgumentParser(description="Initialize GenFileMap configuration")
    parser.add_argument(
        "--global-config",
        default=DEFAULT_CONFIG_PATH,
        help="Path to create global configuration file"
    )
    parser.add_argument(
        "--project-config",
        default=DEFAULT_PROJECT_CONFIG_PATH,
        help="Path to create project-specific configuration file"
    )
    parser.add_argument(
        "--init-type",
        choices=["global", "project", "both"],
        default="both",
        help="Type of configuration to initialize"
    )
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    # Create global configuration if requested
    if args.init_type in ["global", "both"]:
        global_config = create_global_config(args.global_config)
        print(f"\nCreated global configuration at: {args.global_config}")
        print("\nGlobal directory structure:")
        print(f"  Config: {os.path.dirname(args.global_config)}")
        for name, path in global_config["output_dirs"].items():
            print(f"  {name.capitalize()}: {path}")
        print(f"  Templates: {global_config['output']['template_dir']}")
        print(f"  Project Maps: {os.path.dirname(global_config['project_map_output'])}")
        print(f"  Schemas: {os.path.dirname(global_config['output']['schema_path'])}")
        print(f"  Reports: {os.path.dirname(global_config['output']['report_path'])}")

    # Create project configuration if requested
    if args.init_type in ["project", "both"]:
        project_config = create_project_config(args.project_config)
        print(f"\nCreated project configuration at: {args.project_config}")
        print("\nProject directory structure:")
        print(f"  Config: {args.project_config}")
        for name, path in project_config["output_dirs"].items():
            print(f"  {name.capitalize()}: {path}")
        print(f"  Templates: {project_config['output']['template_dir']}")
        print(f"  Project Maps: {os.path.dirname(project_config['project_map_output'])}")
        print(f"  Schemas: {os.path.dirname(project_config['output']['schema_path'])}")
        print(f"  Reports: {os.path.dirname(project_config['output']['report_path'])}")

if __name__ == "__main__":
    main()