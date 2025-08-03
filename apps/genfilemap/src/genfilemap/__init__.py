"""
GenFileMap - Generate structured file maps for AI navigation.

This package provides tools for generating structured file maps that enhance
AI comprehension of code and documentation files.
"""

__version__ = "0.1.0"
__author__ = "GenFileMap Team"
__email__ = "example@genfilemap.com"

# Export public API
from genfilemap.core import (
    run_process,
    update_file_with_map,
    process_files_async,
    initialize_report,
    generate_report,
    validate_file_map,
    should_abort_on_validation_failure,
    log_validation_issues,
    create_validation_prompt
)

# Make important modules and functions accessible at package level
from genfilemap.config import load_config, save_config
from genfilemap.cli import main

__all__ = [
    'run_process',
    'update_file_with_map',
    'process_files_async',
    'initialize_report',
    'generate_report',
    'validate_file_map',
    'should_abort_on_validation_failure',
    'log_validation_issues',
    'create_validation_prompt',
    '__version__',
    '__author__',
    '__email__',
    'load_config',
    'save_config',
    'main'
]

