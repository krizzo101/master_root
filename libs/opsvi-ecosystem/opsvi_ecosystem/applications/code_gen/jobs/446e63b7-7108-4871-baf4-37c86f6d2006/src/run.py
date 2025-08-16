"""
Entrypoint for Flask Weather App. Used for local dev. Use gunicorn in production.
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Local development only!
    app.run(host="0.0.0.0", port=5000, debug=True)
