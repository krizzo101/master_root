# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Template Utilities for Genfilemap","description":"This module provides functions for loading and managing templates used in the genfilemap project.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Module Documentation","description":"Documentation string providing an overview of the module's purpose.","line_start":2,"line_end":5},{"name":"Imports","description":"Import statements for required modules.","line_start":6,"line_end":9},{"name":"Constants","description":"Definition of constants used in the module.","line_start":11,"line_end":11},{"name":"Function Definitions","description":"Definition of functions for loading templates.","line_start":13,"line_end":18}],"key_elements":[{"name":"TEMPLATES_DIR","description":"Directory path for custom templates.","line":11},{"name":"load_template","description":"Function to load a custom file map template.","line":13}]}
"""
# FILE_MAP_END

"""
Template handling utilities for genfilemap.

This module provides functions for loading and managing templates.
"""

import os
from typing import Optional

# Custom templates storage (configurable via config file)
TEMPLATES_DIR = os.path.expanduser("~/.file_map_templates")


def load_template(template_name: str) -> Optional[str]:
    """Load a custom file map template"""
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.template")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return None
