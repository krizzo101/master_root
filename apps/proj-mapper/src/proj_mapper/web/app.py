"""Web interface for Project Mapper.

This module provides a web interface for the Project Mapper tool.
"""

import os
import logging
from flask import Flask, render_template

from proj_mapper.version import __version__
from proj_mapper.web.routes import blueprints

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(test_config=None):
    """Create and configure the Flask application."""
    
    # Initialize Flask app
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'development-key')
    
    # Apply test configuration if provided
    if test_config is not None:
        app.config.update(test_config)
    
    # Register blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    
    # Register home route
    @app.route('/')
    def index():
        """Render the home page."""
        return render_template('index.html', version=__version__)
    
    return app


# Initialize the application when running directly
app = create_app()

if __name__ == '__main__':
    # Run the Flask app when executed directly
    app.run(debug=True) 