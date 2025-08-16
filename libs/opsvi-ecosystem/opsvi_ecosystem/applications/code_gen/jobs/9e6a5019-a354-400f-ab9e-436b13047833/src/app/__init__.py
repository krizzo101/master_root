"""
Main Flask application factory and blueprint registration
"""
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_admin import Admin
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from flask_uploads import configure_uploads
from flask_wtf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .uploads import images

# Extension initializations
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]
)
talisman = Talisman()
redis_client = FlaskRedis()

admin = Admin(name="AI-Enhanced CMS Admin", template_mode="bootstrap4")


def create_app(config_class=Config) -> Flask:
    """
    Flask application factory
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Middleware for reverse proxy setups (e.g. behind nginx / gunicorn)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    talisman.init_app(app)
    redis_client.init_app(app)
    configure_uploads(app, images)

    # Register blueprints
    from .routes.admin import admin_bp
    from .routes.ai import ai_bp
    from .routes.analytics import analytics_bp
    from .routes.api import api_bp
    from .routes.auth import auth_bp
    from .routes.main import main_bp
    from .routes.posts import posts_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(ai_bp, url_prefix="/ai")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")

    # Register Flask-Admin views
    from .admin_views import register_admin_views

    register_admin_views(admin, db)
    admin.init_app(app)

    # Setup logging
    file_handler = RotatingFileHandler("cms.log", maxBytes=10240, backupCount=5)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info("AI-Enhanced CMS startup")

    # Custom error pages


def setup_error_handlers(app):
    from .routes.errors import internal_error, page_not_found

    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_error)

    setup_error_handlers(app)
    return app
