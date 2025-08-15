"""Utility functions for the web interface.

This module provides utility functions for the web interface.
"""

import os
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.expanduser('~'), '.proj_mapper', 'uploads')
PROJECTS_FOLDER = os.path.join(os.path.expanduser('~'), '.proj_mapper', 'projects')
ALLOWED_EXTENSIONS = {'zip'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROJECTS_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_project_id() -> str:
    """Generate a unique project ID."""
    return str(uuid.uuid4())


def save_project_metadata(project_id: str, metadata: Dict[str, Any]) -> None:
    """Save project metadata to file."""
    project_dir = os.path.join(PROJECTS_FOLDER, project_id)
    os.makedirs(project_dir, exist_ok=True)
    
    metadata_path = os.path.join(project_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)


def load_project_metadata(project_id: str) -> Dict[str, Any]:
    """Load project metadata from file."""
    metadata_path = os.path.join(PROJECTS_FOLDER, project_id, 'metadata.json')
    if not os.path.exists(metadata_path):
        return {}
        
    with open(metadata_path, 'r') as f:
        return json.load(f)


def load_all_projects() -> List[Dict[str, Any]]:
    """Load metadata for all projects."""
    projects = []
    
    if not os.path.exists(PROJECTS_FOLDER):
        return []
        
    for project_id in os.listdir(PROJECTS_FOLDER):
        project_dir = os.path.join(PROJECTS_FOLDER, project_id)
        if os.path.isdir(project_dir):
            metadata_path = os.path.join(project_dir, 'metadata.json')
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        metadata['id'] = project_id
                        projects.append(metadata)
                except Exception as e:
                    logger.error(f"Error loading project {project_id}: {e}")
    
    # Sort by timestamp (newest first)
    projects.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return projects


def load_project_map(project_id: str) -> Dict[str, Any]:
    """Load project map from file."""
    map_path = os.path.join(PROJECTS_FOLDER, project_id, 'project_map.json')
    if not os.path.exists(map_path):
        return {}
        
    with open(map_path, 'r') as f:
        return json.load(f)


def get_project_tree(project_map: Dict[str, Any]) -> Dict[str, List]:
    """Generate project tree structure from project map."""
    files = project_map.get('files', [])
    tree = {}
    
    for file in files:
        path = file.get('path', '')
        if not path:
            continue
            
        parts = path.split('/')
        
        # Add to tree
        if len(parts) == 1:
            # Root level file
            if 'root' not in tree:
                tree['root'] = []
            tree['root'].append({'type': 'file', 'name': parts[0]})
        else:
            # Nested file
            folder = parts[0]
            if folder not in tree:
                tree[folder] = []
                
            if len(parts) == 2:
                # Direct child of folder
                tree[folder].append({'type': 'file', 'name': parts[1]})
            else:
                # Nested folder
                subfolder = parts[1]
                found = False
                
                for item in tree[folder]:
                    if item.get('type') == 'folder' and item.get('name') == subfolder:
                        if 'files' not in item:
                            item['files'] = []
                        item['files'].append('/'.join(parts[2:]))
                        found = True
                        break
                
                if not found:
                    tree[folder].append({
                        'type': 'folder',
                        'name': subfolder,
                        'files': ['/'.join(parts[2:])]
                    })
    
    return tree 