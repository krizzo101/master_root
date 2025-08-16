"""Flask blueprints for the web interface.

This package contains Flask blueprints for the web interface.
"""

from flask import Blueprint

# Create blueprints
projects_bp = Blueprint('projects', __name__, url_prefix='/projects')
analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')

# Import views to register with blueprints
from proj_mapper.web.routes import projects
from proj_mapper.web.routes import analysis

# Export blueprints for use in app.py
blueprints = [
    projects_bp,
    analysis_bp
] 