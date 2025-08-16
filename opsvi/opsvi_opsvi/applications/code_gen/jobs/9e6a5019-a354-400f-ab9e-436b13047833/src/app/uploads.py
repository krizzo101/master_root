"""
Flask-Uploads configuration for image uploads.
"""
from flask_uploads import UploadSet, IMAGES, configure_uploads

images = UploadSet("images", IMAGES)

# Usage: configure_uploads(app, images)
