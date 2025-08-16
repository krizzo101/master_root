"""Analysis-related routes for the web interface.

This module provides analysis-related routes for the web interface.
"""

import os
from typing import Dict, Any

from flask import (
    render_template, request, redirect, url_for, 
    jsonify, flash, abort
)

from proj_mapper.web.routes import analysis_bp
from proj_mapper.web.utils import (
    load_project_metadata, load_project_map, PROJECTS_FOLDER
)
from proj_mapper.web.models import analyze_project


@analysis_bp.route('/project/<project_id>')
def project_analyze(project_id):
    """Re-analyze a project."""
    metadata = load_project_metadata(project_id)
    if not metadata:
        flash('Project not found', 'error')
        return redirect(url_for('projects.projects_list'))
    
    try:
        analyze_project(project_id)
        flash('Project analyzed successfully', 'success')
    except Exception as e:
        flash(f'Error analyzing project: {e}', 'error')
    
    return redirect(url_for('projects.project_details', project_id=project_id))


@analysis_bp.route('/api/project/<project_id>', methods=['POST'])
def api_project_analyze(project_id):
    """API endpoint to analyze a project."""
    metadata = load_project_metadata(project_id)
    if not metadata:
        return jsonify({'error': 'Project not found'}), 404
    
    try:
        project_map = analyze_project(project_id)
        return jsonify({
            'success': True,
            'message': 'Project analyzed successfully',
            'project_id': project_id,
            'project_name': metadata.get('name')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500 