"""
Default configuration values for O3 Code Generator.

This module contains all default configuration values that are used
when no custom configuration is provided or when specific values are missing.
"""

from typing import Any

# Environment-specific configurations
ENVIRONMENT_CONFIGS: dict[str, dict[str, Any]] = {
    "development": {
        "system": {"debug_mode": True, "log_level": "DEBUG"},
        "api": {"timeout": 60},
    },
    "production": {
        "system": {"debug_mode": False, "log_level": "WARNING"},
        "api": {"timeout": 300},
    },
    "testing": {
        "system": {"debug_mode": True, "log_level": "DEBUG"},
        "api": {"timeout": 30},
    },
}

# Default configuration structure
DEFAULT_CONFIG: dict[str, Any] = {
    # Model configurations
    "models": {
        "o3": {
            "name": "o3",
            "max_completion_tokens": 16000,  # Set to 16000 tokens
            "description": "Advanced reasoning model for complex tasks",
        },
        "o4-mini": {
            "name": "o4-mini",
            "max_completion_tokens": 16000,  # Set to 16000 tokens
            "description": "Fast reasoning model for quick tasks",
        },
    },
    # API settings
    "api": {
        "base_url": "https://api.openai.com/v1",
        "timeout": 300,  # 5 minutes for complex O3 reasoning tasks
        "max_retries": 3,
        "retry_delay": 1,
    },
    # File paths and directories
    "paths": {
        "generated_files": "generated_files",
        "schemas": "schemas",
        "prompts": "prompts",
        "config": "config",
        "logs": "logs",
    },
    # Generation settings
    "generation": {
        "default_language": "python",
        "default_file_extension": ".py",
        "auto_save": True,
        "overwrite_protection": True,
        "create_backup": False,
    },
    # Output settings
    "output": {
        "format": "json",
        "include_metadata": True,
        "include_explanation": True,
        "show_progress": True,
        "verbose": False,
    },
    # System settings
    "system": {
        "log_level": "INFO",
        "log_file": None,
        "debug_mode": False,
        "validate_schemas": True,
        "check_dependencies": True,
    },
    # Logging settings
    "logging": {
        "level": "INFO",
        "log_dir": "logs",
        "standard_log_file": "o3_generator.log",
        "debug_log_file": "o3_generator_debug.log",
        "error_log_file": "o3_generator_error.log",
        "console_output": True,
        "enable_debug_log": False,
        "max_file_size_mb": 10,
        "backup_count": 5,
        "format_string": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S",
    },
    # Prompt settings
    "prompts": {
        "system_prompt_file": "prompts/system_prompt.py",
        "input_schema_file": "schemas/input_schema.py",
        "output_schema_file": "schemas/output_schema.py",
    },
    # Validation settings
    "validation": {
        "require_file_name": True,
        "require_language": False,
        "max_prompt_length": 10000,
        "max_context_files": 10,
        "allowed_languages": [
            "python",
            "javascript",
            "typescript",
            "java",
            "cpp",
            "csharp",
        ],
    },
}

# Environment-specific overrides
ENVIRONMENT_CONFIGS = {
    "development": {
        "system": {"debug_mode": True, "log_level": "DEBUG"},
        "logging": {"level": "DEBUG", "enable_debug_log": True, "console_output": True},
    },
    "production": {
        "system": {"debug_mode": False, "log_level": "WARNING"},
        "logging": {
            "level": "WARNING",
            "enable_debug_log": False,
            "console_output": False,
        },
    },
}
