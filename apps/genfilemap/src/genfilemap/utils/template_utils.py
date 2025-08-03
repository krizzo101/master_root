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
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None 