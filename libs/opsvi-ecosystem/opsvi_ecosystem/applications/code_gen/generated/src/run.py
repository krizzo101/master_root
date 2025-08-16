"""
Flask application entry point for running the Weather Information Web App.
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Run the Flask web application
    app.run(debug=False, host="0.0.0.0", port=5000)
