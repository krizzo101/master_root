import os
from pathlib import Path


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f'sqlite:///{Path(__file__).parent / "app.db"}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = False if os.getenv("ENV") == "development" else True
    OPENAI_API_KEY = os.getenv(
        "OPENAI_API_KEY", ""
    )  # You must add your OpenAI API key in .env
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    OAUTHLIB_INSECURE_TRANSPORT = os.getenv("OAUTHLIB_INSECURE_TRANSPORT", "0")
    # Add other configuration as needed
