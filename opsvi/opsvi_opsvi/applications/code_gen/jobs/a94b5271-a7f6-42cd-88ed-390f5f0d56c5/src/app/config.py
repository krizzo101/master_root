"""
Application settings management (Env, defaults).
"""
import os

JWT_SECRET: str = os.getenv("JWT_SECRET", "changeme-supersecret")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRY_MINUTES", "120"))
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/rtcollab"
)
S3_BUCKET: str = os.getenv("S3_BUCKET", "rtcollab-files")
S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
S3_ACCESS_KEY_ID: str = os.getenv("S3_ACCESS_KEY_ID", "test")
S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "test")
CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")
ES_URL: str = os.getenv("ES_URL", "http://localhost:9200")
AUDIT_LOG_RETENTION: int = int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "90"))
AI_API_KEY: str = os.getenv("OPENAI_API_KEY", "test-key")

# Other configuration as needed
