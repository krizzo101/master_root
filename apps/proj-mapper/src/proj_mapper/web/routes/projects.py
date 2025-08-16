"""Project-related routes for the web interface.

This module provides project-related routes for the web interface.
"""

import os
import zipfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from flask import (
    render_template, request, redirect, url_for, 
    jsonify, flash, send_file, abort
)
from werkzeug.utils import secure_filename

from proj_mapper.web.routes import projects_bp
from proj_mapper.web.utils import (
    allowed_file, generate_project_id, save_project_metadata,
    load_project_metadata, load_all_projects, load_project_map,
    get_project_tree, UPLOAD_FOLDER, PROJECTS_FOLDER
)
from proj_mapper.web.models import analyze_project, delete_project


@projects_bp.route('/')
def projects_list():
    """Render the projects list page."""
    projects_list = load_all_projects()
    return render_template('projects.html', projects=projects_list)


@projects_bp.route('/upload')
def upload():
    """Render the upload page."""
    return render_template('upload.html')


@projects_bp.route('/upload-file', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'project_file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
        
    file = request.files['project_file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
        
    if not allowed_file(file.filename):
        flash(f'File type not allowed. Please upload a ZIP file.', 'error')
        return redirect(request.url)
    
    # Get project name
    project_name = request.form.get('project_name', 'Unnamed Project')
    
    # Generate project ID
    project_id = generate_project_id()
    
    # Create project directory
    project_dir = os.path.join(PROJECTS_FOLDER, project_id)
    os.makedirs(project_dir, exist_ok=True)
    
    # Save the uploaded file
    file_path = os.path.join(project_dir, secure_filename(file.filename))
    file.save(file_path)
    
    # Extract the ZIP file
    source_dir = os.path.join(project_dir, 'source')
    os.makedirs(source_dir, exist_ok=True)
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(source_dir)
    except Exception as e:
        flash(f'Error extracting ZIP file: {e}', 'error')
        shutil.rmtree(project_dir)
        return redirect(url_for('projects.upload'))
    
    # Create and save metadata
    metadata = {
        'name': project_name,
        'timestamp': datetime.now().isoformat(),
        'original_filename': file.filename,
        'analyzed': False
    }
    save_project_metadata(project_id, metadata)
    
    # Analyze now if requested
    analyze_now = request.form.get('analyze_now') == 'on'
    if analyze_now:
        try:
            analyze_project(project_id)
            flash('Project uploaded and analyzed successfully', 'success')
        except Exception as e:
            flash(f'Project uploaded but analysis failed: {e}', 'warning')
    else:
        flash('Project uploaded successfully', 'success')
    
    return redirect(url_for('projects.project_details', project_id=project_id))


@projects_bp.route('/analyze-directory', methods=['POST'])
def analyze_directory():
    """Handle directory analysis."""
    directory_path = request.form.get('directory_path')
    project_name = request.form.get('project_name', 'Unnamed Project')
    
    if not directory_path or not os.path.isdir(directory_path):
        flash('Invalid directory path', 'error')
        return redirect(url_for('projects.upload'))
    
    # Generate project ID
    project_id = generate_project_id()
    
    # Create project directory
    project_dir = os.path.join(PROJECTS_FOLDER, project_id)
    os.makedirs(project_dir, exist_ok=True)
    
    # Copy the directory contents
    source_dir = os.path.join(project_dir, 'source')
    try:
        shutil.copytree(directory_path, source_dir)
    except Exception as e:
        flash(f'Error copying directory: {e}', 'error')
        shutil.rmtree(project_dir)
        return redirect(url_for('projects.upload'))
    
    # Create and save metadata
    metadata = {
        'name': project_name,
        'timestamp': datetime.now().isoformat(),
        'original_path': directory_path,
        'analyzed': False
    }
    save_project_metadata(project_id, metadata)
    
    # Parse configuration options
    include_patterns = request.form.get('include_patterns', '')
    exclude_patterns = request.form.get('exclude_patterns', '')
    
    config = {}
    if include_patterns:
        config['include_patterns'] = [p.strip() for p in include_patterns.split(',')]
    if exclude_patterns:
        config['exclude_patterns'] = [p.strip() for p in exclude_patterns.split(',')]
    
    # Parse advanced options
    for key in request.form:
        if key.startswith('analyze_') or key.startswith('generate_'):
            config[key] = request.form.get(key) == 'true'
    
    # Analyze the project
    try:
        analyze_project(project_id, config)
        flash('Project analyzed successfully', 'success')
    except Exception as e:
        flash(f'Error analyzing project: {e}', 'error')
    
    return redirect(url_for('projects.project_details', project_id=project_id))


@projects_bp.route('/<project_id>')
def project_details(project_id):
    """Render the project details page."""
    metadata = load_project_metadata(project_id)
    if not metadata:
        flash('Project not found', 'error')
        return redirect(url_for('projects.projects_list'))
    
    # Add ID to metadata
    metadata['id'] = project_id
    
    # Load project map if available
    project_map = load_project_map(project_id)
    if not project_map:
        flash('Project map not found. Analysis may not have been performed.', 'warning')
        return render_template('project_detail.html', project=metadata, project_map={}, project_tree={})
    
    # Generate project tree
    project_tree = get_project_tree(project_map)
    
    return render_template('project_detail.html', 
                          project=metadata, 
                          project_map=project_map,
                          project_tree=project_tree)


@projects_bp.route('/<project_id>/download')
def project_download(project_id):
    """Download the project map."""
    map_path = os.path.join(PROJECTS_FOLDER, project_id, 'project_map.json')
    if not os.path.exists(map_path):
        flash('Project map not found', 'error')
        return redirect(url_for('projects.project_details', project_id=project_id))
    
    metadata = load_project_metadata(project_id)
    project_name = metadata.get('name', 'project')
    safe_name = secure_filename(project_name)
    
    return send_file(map_path, 
                    mimetype='application/json',
                    as_attachment=True,
                    download_name=f'{safe_name}_map.json')


@projects_bp.route('/<project_id>/delete')
def project_delete(project_id):
    """Delete a project."""
    if delete_project(project_id):
        flash('Project deleted successfully', 'success')
    else:
        flash('Error deleting project', 'error')
    
    return redirect(url_for('projects.projects_list')) 