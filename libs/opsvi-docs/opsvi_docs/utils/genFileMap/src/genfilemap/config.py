# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Configuration Module for Genfilemap","description":"This module handles loading, parsing, and managing configuration settings for the genfilemap utility.","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules for configuration handling.","line_start":3,"line_end":12},{"name":"Default Configuration Path","description":"Defines the default path for the configuration file.","line_start":14,"line_end":14},{"name":"Config Class","description":"Main configuration manager class for handling configuration settings.","line_start":16,"line_end":221}],"key_elements":[{"name":"DEFAULT_CONFIG_PATH","description":"Default configuration file path.","line":14},{"name":"Config","description":"Configuration manager for genfilemap.","line":16},{"name":"__init__","description":"Initializes the configuration with optional config path and command-line arguments.","line":19},{"name":"_load_defaults","description":"Loads default configuration settings.","line":44},{"name":"_load_config_file","description":"Loads configuration from a specified file.","line":83},{"name":"_merge_dict","description":"Recursively merges source dictionary into target dictionary.","line":94},{"name":"get","description":"Retrieves a value from the configuration using dot notation.","line":108},{"name":"generate_default_config","description":"Generates a default configuration file.","line":164}]}
"""
# FILE_MAP_END

"""
Configuration module for genfilemap.

This module handles loading, parsing, and managing configuration settings
for the genfilemap utility.
"""

import os
import json
from typing import Dict, Any, Optional

# Default configuration file path
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.genfilemap/config.json")


class Config:
    """Configuration manager for genfilemap"""

    def __init__(
        self, config_path: Optional[str] = None, args: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the configuration with optional config path and command-line arguments.

        Args:
            config_path: Path to configuration file
            args: Command-line arguments that override config file settings
        """
        self.config_data = {}
        self.args = args or {}

        # Load default configuration
        self._load_defaults()

        # If config path provided, load it
        if config_path:
            config_path = os.path.expanduser(config_path)
            if os.path.exists(config_path):
                self._load_config_file(config_path)
            else:
                print(f"Config file not found: {config_path}")
        # Otherwise try the default location
        elif os.path.exists(DEFAULT_CONFIG_PATH):
            self._load_config_file(DEFAULT_CONFIG_PATH)

    def _load_defaults(self):
        """Load default configuration settings"""
        self.config_data = {
            "path": ".",
            "dry_run": False,
            "file_processing": {
                "recursive": True,
                "include_extensions": [
                    ".py",
                    ".js",
                    ".ts",
                    ".jsx",
                    ".tsx",
                    ".html",
                    ".css",
                    ".md",
                ],
                "exclude_extensions": [
                    ".pyc",
                    ".min.js",
                    ".min.css",
                    ".log",
                    ".json",
                    ".map",
                ],
                "min_lines": 10,
                "ignore_file": ".fileignore",
            },
            "api": {
                "vendor": "openai",
                "model": "gpt-4o-mini",
                "api_key": "",
                "api_key_var": "OPENAI_API_KEY",
                "max_tokens": 1500,
            },
            "performance": {"concurrency": 3, "processes": 1},
            "output": {
                "template": "",
                "template_dir": os.path.expanduser("~/.file_map_templates"),
                "schema_path": "",
                "report_path": "",
            },
            "project_map": {"enabled": False, "output_path": "project_map.md"},
            "system_prompts": {
                "code_system_message": 'You are a specialized AI assistant for code analysis that creates structured file maps in JSON format.\n\nYour task requires precise analysis using multi-step reasoning:\n\n1) CAREFUL ANALYSIS: Examine the code file thoroughly to identify:\n   - Key components (classes, functions, variables, imports)\n   - Logical sections and their boundaries\n   - Important interfaces and data structures\n   - The file\'s overall purpose and architecture\n\n2) STRUCTURED THINKING: Use a Tree of Thought approach to map the file:\n   a) First identify all major sections and their line boundaries\n   b) Then identify key elements within each section\n   c) Verify line numbers by counting from the top of the file\n   d) Double-check that all line ranges are accurate and non-overlapping\n\n3) JSON GENERATION: Create a precisely structured JSON object following this exact schema:\n```json\n{\n  "file_metadata": {\n    "title": "Descriptive title of the file",\n    "description": "Comprehensive description of the file\'s purpose and contents",\n    "last_updated": "YYYY-MM-DD format date",\n    "type": "file_type (e.g., code, documentation, configuration)"\n  },\n  "ai_instructions": "When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",\n  "sections": [\n    {\n      "name": "Section Name",\n      "description": "Brief description of this section\'s purpose",\n      "line_start": X, // integer line number where section starts\n      "line_end": Y // integer line number where section ends\n    },\n    // Additional sections...\n  ],\n  "key_elements": [\n    {\n      "name": "Element Name",\n      "description": "Brief description of this element",\n      "line": Z // integer line number where this element is defined\n    },\n    // Additional key elements...\n  ]\n}\n```\n\n4) VERIFICATION: Validate your output with these checks:\n   - All line numbers are accurate and within the file bounds\n   - All required JSON fields are present and correctly formatted\n   - Section descriptions correctly capture each section\'s purpose\n   - Line ranges for sections are comprehensive and non-overlapping\n   - The file metadata accurately reflects the file\'s purpose\n\nIMPORTANT: Return ONLY the JSON object with no additional text, markdown formatting, or explanations. Your response must be valid, parseable JSON.',
                "documentation_system_message": 'You are a specialized AI assistant for documentation analysis that creates structured file maps in JSON format.\n\nYour task requires precise analysis using multi-step reasoning:\n\n1) DOCUMENTATION STRUCTURE ANALYSIS: Carefully examine the documentation to identify:\n   - Main sections and their hierarchical relationships\n   - Headings and subheadings with their exact line numbers\n   - Key concepts, definitions, and examples\n   - The document\'s overall purpose and audience\n\n2) STRUCTURED MAPPING PROCESS: Use a Tree of Thought approach to map the document:\n   a) First identify all major headers and their line numbers\n   b) Group content under appropriate sections based on heading hierarchy\n   c) Verify line numbers by counting from the top of the document\n   d) Double-check that all section boundaries are accurate and complete\n\n3) JSON GENERATION: Create a precisely structured JSON object following this exact schema:\n```json\n{\n  "file_metadata": {\n    "title": "Descriptive title of the document",\n    "description": "Comprehensive description of the document\'s purpose and contents",\n    "last_updated": "YYYY-MM-DD format date",\n    "type": "file_type (e.g., documentation, tutorial, reference)"\n  },\n  "ai_instructions": "When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",\n  "sections": [\n    {\n      "name": "Section Name",\n      "description": "Brief description of this section\'s purpose",\n      "line_start": X, // integer line number where section starts\n      "line_end": Y // integer line number where section ends\n    },\n    // Additional sections...\n  ],\n  "key_elements": [\n    {\n      "name": "Element Name",\n      "description": "Brief description of this element",\n      "line": Z // integer line number where this element is defined\n    },\n    // Additional key elements...\n  ]\n}\n```\n\n4) VERIFICATION: Validate your output with these checks:\n   - All line numbers are accurate by counting from line 1\n   - All required JSON fields are present and correctly formatted\n   - Section boundaries correspond to actual section transitions\n   - Line ranges for sections are comprehensive and non-overlapping\n   - The file metadata accurately captures the document\'s purpose\n\nIMPORTANT: Return ONLY the JSON object with no additional text, markdown formatting, or explanations. Your response must be valid, parseable JSON.',
            },
        }

    def _load_config_file(self, config_path: str):
        """Load configuration from a file"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = json.load(f)

            # Recursively merge with default config
            self._merge_dict(self.config_data, file_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config file: {str(e)}")

    def _merge_dict(self, target: dict, source: dict):
        """
        Recursively merge source dictionary into target dictionary

        Args:
            target: The target dictionary to merge into
            source: The source dictionary to merge from
        """
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._merge_dict(target[key], value)
            else:
                target[key] = value

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a value from the configuration using dot notation following precedence order:
        1. Command-line arguments
        2. Environment variables
        3. Config file values
        4. Default values

        Args:
            key_path: The dot-separated path to the configuration value
            default: Default value if the key doesn't exist

        Returns:
            The configuration value or default if not found
        """
        # 1. First check command-line arguments (highest priority)
        if key_path in self.args and self.args[key_path] is not None:
            return self.args[key_path]

        # 2. Check for environment variables (second priority)
        # Convert dot notation to uppercase with underscores (e.g., api.model -> GENFILEMAP_API_MODEL)
        env_var_name = f"GENFILEMAP_{key_path.replace('.', '_').upper()}"
        env_value = os.environ.get(env_var_name)
        if env_value is not None:
            # Try to convert environment value to appropriate type based on default
            if isinstance(default, bool):
                return env_value.lower() in ("true", "yes", "1", "y")
            elif isinstance(default, int):
                try:
                    return int(env_value)
                except ValueError:
                    pass
            elif isinstance(default, float):
                try:
                    return float(env_value)
                except ValueError:
                    pass
            elif isinstance(default, list):
                # Split by commas for list values
                return env_value.split(",")
            return env_value

        # 3. Check config data from config file (third priority)
        keys = key_path.split(".")
        value = self.config_data

        # Navigate through nested dictionaries
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default  # 4. Return default value if not found anywhere else

        return value

    @staticmethod
    def generate_default_config(output_path: str = DEFAULT_CONFIG_PATH):
        """
        Generate a default configuration file

        Args:
            output_path: Path where to save the default configuration
        """
        # Try to load template configuration
        template_path = os.path.join(
            os.path.dirname(__file__), "schema/config.json.template"
        )
        try:
            with open(template_path, "r") as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If template doesn't exist, use hardcoded defaults
            config = {
                "path": ".",
                "dry_run": False,
                "file_processing": {
                    "recursive": True,
                    "include_extensions": [
                        ".py",
                        ".js",
                        ".ts",
                        ".jsx",
                        ".tsx",
                        ".html",
                        ".css",
                        ".md",
                    ],
                    "exclude_extensions": [
                        ".pyc",
                        ".min.js",
                        ".min.css",
                        ".log",
                        ".json",
                        ".map",
                    ],
                    "min_lines": 10,
                    "ignore_file": ".fileignore",
                },
                "api": {
                    "vendor": "openai",
                    "model": "gpt-4o-mini",
                    "api_key": "",
                    "api_key_var": "OPENAI_API_KEY",
                    "max_tokens": 1500,
                },
                "performance": {"concurrency": 5, "processes": 1},
                "output": {
                    "template": "",
                    "template_dir": "~/.file_map_templates",
                    "schema_path": "",
                    "report_path": "filemap_report.json",
                },
                "project_map": {"enabled": False, "output_path": "project_map.md"},
                "system_prompts": {
                    "code_system_message": 'You are a specialized AI assistant for code analysis that creates structured file maps in JSON format.\n\nYour task requires precise analysis using multi-step reasoning:\n\n1) CAREFUL ANALYSIS: Examine the code file thoroughly to identify:\n   - Key components (classes, functions, variables, imports)\n   - Logical sections and their boundaries\n   - Important interfaces and data structures\n   - The file\'s overall purpose and architecture\n\n2) STRUCTURED THINKING: Use a Tree of Thought approach to map the file:\n   a) First identify all major sections and their line boundaries\n   b) Then identify key elements within each section\n   c) Verify line numbers by counting from the top of the file\n   d) Double-check that all line ranges are accurate and non-overlapping\n\n3) JSON GENERATION: Create a precisely structured JSON object following this exact schema:\n```json\n{\n  "file_metadata": {\n    "title": "Descriptive title of the file",\n    "description": "Comprehensive description of the file\'s purpose and contents",\n    "last_updated": "YYYY-MM-DD format date",\n    "type": "file_type (e.g., code, documentation, configuration)"\n  },\n  "ai_instructions": "When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",\n  "sections": [\n    {\n      "name": "Section Name",\n      "description": "Brief description of this section\'s purpose",\n      "line_start": X, // integer line number where section starts\n      "line_end": Y // integer line number where section ends\n    },\n    // Additional sections...\n  ],\n  "key_elements": [\n    {\n      "name": "Element Name",\n      "description": "Brief description of this element",\n      "line": Z // integer line number where this element is defined\n    },\n    // Additional key elements...\n  ]\n}\n```\n\n4) VERIFICATION: Validate your output with these checks:\n   - All line numbers are accurate and within the file bounds\n   - All required JSON fields are present and correctly formatted\n   - Section descriptions correctly capture each section\'s purpose\n   - Line ranges for sections are comprehensive and non-overlapping\n   - The file metadata accurately reflects the file\'s purpose\n\nIMPORTANT: Return ONLY the JSON object with no additional text, markdown formatting, or explanations. Your response must be valid, parseable JSON.',
                    "documentation_system_message": 'You are a specialized AI assistant for documentation analysis that creates structured file maps in JSON format.\n\nYour task requires precise analysis using multi-step reasoning:\n\n1) DOCUMENTATION STRUCTURE ANALYSIS: Carefully examine the documentation to identify:\n   - Main sections and their hierarchical relationships\n   - Headings and subheadings with their exact line numbers\n   - Key concepts, definitions, and examples\n   - The document\'s overall purpose and audience\n\n2) STRUCTURED MAPPING PROCESS: Use a Tree of Thought approach to map the document:\n   a) First identify all major headers and their line numbers\n   b) Group content under appropriate sections based on heading hierarchy\n   c) Verify line numbers by counting from the top of the document\n   d) Double-check that all section boundaries are accurate and complete\n\n3) JSON GENERATION: Create a precisely structured JSON object following this exact schema:\n```json\n{\n  "file_metadata": {\n    "title": "Descriptive title of the document",\n    "description": "Comprehensive description of the document\'s purpose and contents",\n    "last_updated": "YYYY-MM-DD format date",\n    "type": "file_type (e.g., documentation, tutorial, reference)"\n  },\n  "ai_instructions": "When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",\n  "sections": [\n    {\n      "name": "Section Name",\n      "description": "Brief description of this section\'s purpose",\n      "line_start": X, // integer line number where section starts\n      "line_end": Y // integer line number where section ends\n    },\n    // Additional sections...\n  ],\n  "key_elements": [\n    {\n      "name": "Element Name",\n      "description": "Brief description of this element",\n      "line": Z // integer line number where this element is defined\n    },\n    // Additional key elements...\n  ]\n}\n```\n\n4) VERIFICATION: Validate your output with these checks:\n   - All line numbers are accurate by counting from line 1\n   - All required JSON fields are present and correctly formatted\n   - Section boundaries correspond to actual section transitions\n   - Line ranges for sections are comprehensive and non-overlapping\n   - The file metadata accurately captures the document\'s purpose\n\nIMPORTANT: Return ONLY the JSON object with no additional text, markdown formatting, or explanations. Your response must be valid, parseable JSON.',
                },
            }

        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write the configuration file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        print(f"Default configuration generated at {output_path}")
