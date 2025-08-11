# /home/opsvi/asea/development/autonomous_systems/core_systems_service.py
from flask import Flask, jsonify, request
import logging
import os
import sys

# Add the parent directory to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from autonomous_systems.core_systems.session_continuity_system import (
    SessionContinuitySystem,
)

app = Flask(__name__)

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "core_systems_service.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file_path), logging.StreamHandler(sys.stdout)],
)

# Initialize the core system
try:
    session_continuity = SessionContinuitySystem()
    logging.info("SessionContinuitySystem initialized successfully.")
except Exception as e:
    logging.critical(
        f"Failed to initialize SessionContinuitySystem: {e}", exc_info=True
    )
    session_continuity = None


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint to verify the service is running and systems are initialized.
    """
    if session_continuity:
        return (
            jsonify({"status": "ok", "message": "Core Systems Service is running."}),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "SessionContinuitySystem not initialized.",
                }
            ),
            500,
        )


@app.route("/validate_paths", methods=["POST"])
def validate_paths():
    """
    Endpoint to validate a list of file paths.
    """
    if not session_continuity:
        return jsonify({"error": "Service not properly initialized"}), 500

    data = request.get_json()
    if not data or "paths" not in data:
        return jsonify({"error": "Missing 'paths' in request body"}), 400

    paths_to_validate = data["paths"]
    logging.info(f"Received request to validate paths: {paths_to_validate}")

    try:
        results = session_continuity.validate_paths(paths_to_validate)
        logging.info(f"Validation results: {results}")
        return jsonify(results), 200
    except Exception as e:
        logging.error(f"An error occurred during path validation: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500


if __name__ == "__main__":
    # This block is for direct execution, but using a proper WSGI server like Gunicorn is recommended for production.
    # The start_service.py script will be used to run this.
    logging.info("Starting Flask development server.")
    app.run(host="127.0.0.1", port=5001, debug=False)
