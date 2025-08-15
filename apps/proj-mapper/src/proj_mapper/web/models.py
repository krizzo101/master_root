"""Data models and operations for the web interface.

This module provides data models and operations for the web interface.
"""

import os
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

from proj_mapper.web.utils import (
    load_project_metadata,
    save_project_metadata,
    PROJECTS_FOLDER
)
from proj_mapper.core.project_manager import ProjectManager
from proj_mapper.core.config import Configuration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_project(project_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Analyze a project and generate maps."""
    project_dir = os.path.join(PROJECTS_FOLDER, project_id)
    source_dir = os.path.join(project_dir, 'source')

    # Default config
    if config is None:
        config = {}

    # Create a Configuration object
    config_obj = Configuration(**config)

    # Create a ProjectManager instance
    manager = ProjectManager(config=config_obj)

    # Analyze the project
    project_map = manager.analyze_project(source_dir)

    # Save the project map
    map_path = os.path.join(project_dir, 'project_map.json')
    with open(map_path, 'w') as f:
        json.dump(project_map.to_dict(), f, indent=2)

    # Update metadata
    metadata = load_project_metadata(project_id)
    metadata['analyzed'] = True
    metadata['analysis_timestamp'] = datetime.now().isoformat()
    save_project_metadata(project_id, metadata)

    return project_map.to_dict()


def delete_project(project_id: str) -> bool:
    """Delete a project and its files.

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    project_dir = os.path.join(PROJECTS_FOLDER, project_id)
    if not os.path.exists(project_dir):
        return False

    try:
        shutil.rmtree(project_dir)
        return True
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        return False