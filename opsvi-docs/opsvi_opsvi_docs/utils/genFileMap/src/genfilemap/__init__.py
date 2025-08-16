# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"genfilemap module","description":"This module provides functionality to generate structured file maps that help AI systems understand code and documentation files.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Module Documentation","description":"Documentation string providing an overview of the module's purpose.","line_start":3,"line_end":7},{"name":"Version Declaration","description":"Defines the version of the module.","line_start":9,"line_end":9},{"name":"Imports","description":"Imports necessary components from other modules.","line_start":10,"line_end":20},{"name":"Public API Exports","description":"Defines the public API of the module.","line_start":22,"line_end":22}],"key_elements":[{"name":"__version__","description":"The version of the module.","line":9},{"name":"main","description":"Main function imported from genfilemap.cli.","line":10},{"name":"__all__","description":"Public API exports of the module.","line":12},{"name":"update_file_with_map","description":"Function imported from genfilemap.core.","line":15},{"name":"process_files_async","description":"Function imported from genfilemap.core.","line":16},{"name":"generate_project_map","description":"Function imported from genfilemap.core.","line":17},{"name":"Config","description":"Class imported from genfilemap.config.","line":20},{"name":"DEFAULT_CONFIG_PATH","description":"Constant imported from genfilemap.config.","line":20}]}
"""
# FILE_MAP_END

"""
genfilemap - Generate file maps for better AI agent context

This module provides functionality to generate structured file maps
that help AI systems understand code and documentation files.
"""

__version__ = "0.1.0"

from genfilemap.cli import main

__all__ = ["main"]

# Public API exports
from genfilemap.core import (
    update_file_with_map,
    process_files_async,
    generate_project_map,
)
from genfilemap.config import Config, DEFAULT_CONFIG_PATH

# Note: generate_file_map has been moved to processor classes
