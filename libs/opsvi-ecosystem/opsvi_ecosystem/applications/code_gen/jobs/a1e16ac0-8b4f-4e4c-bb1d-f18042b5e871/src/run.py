"""
Flask development server entrypoint.
Use only for local development (not production).
"""
import os

from app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(
        host=os.environ.get("FLASK_RUN_HOST", "0.0.0.0"),
        port=int(os.environ.get("FLASK_RUN_PORT", 5000)),
        debug=True,
    )
