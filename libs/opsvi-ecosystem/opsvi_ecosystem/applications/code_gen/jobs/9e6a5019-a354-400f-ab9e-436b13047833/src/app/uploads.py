"""
Flask-Uploads configuration for image uploads.
"""
from flask_uploads import IMAGES, UploadSet

images = UploadSet("images", IMAGES)

# Usage: configure_uploads(app, images)
