"""
Core module initialization.

This module serves as the main entry point for the core functionality,
importing and re-exporting from the specialized submodules.
"""

# Import from specialized modules to re-export
from genfilemap.core.file_operations import count_lines, get_hash_file_path
from genfilemap.core.processing import process_files_async, update_file_with_map
from genfilemap.core.cleaning import clean_files_async, clean_file_maps, deep_clean_files_async
from genfilemap.core.reporting import generate_report, initialize_report, report_data
from genfilemap.core.project_map import generate_project_map
from genfilemap.logging_utils import initialize_logging, configure_logging
from genfilemap.core.core import run_process
from genfilemap.core.directory_hash_processing import process_files_with_directory_hashing

# Export validation functions
from genfilemap.core.validation import (
    validate_file_map,
    should_abort_on_validation_failure,
    log_validation_issues,
    create_validation_prompt
)

# Re-export for backward compatibility
__all__ = [
    'update_file_with_map',
    'clean_file_maps',
    'process_files_async',
    'clean_files_async',
    'deep_clean_files_async',
    'generate_project_map',
    'generate_report',
    'count_lines',
    'get_hash_file_path',
    'report_data',
    'initialize_logging',
    'initialize_report',
    'configure_logging',
    'run_process',
    'process_files_with_directory_hashing',
    'validate_file_map',
    'should_abort_on_validation_failure',
    'log_validation_issues',
    'create_validation_prompt'
] 