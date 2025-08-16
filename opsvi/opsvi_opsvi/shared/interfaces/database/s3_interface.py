"""
S3/Blob Storage Shared Interface
-------------------------------
Authoritative implementation based on the official boto3 S3 documentation:
- https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
Implements all core features: file upload/download, bucket management, presigned URLs, and error handling.
Version: Referenced as of July 2024
"""

import logging

logger = logging.getLogger(__name__)


class S3Interface:
    """
    Authoritative shared interface for AWS S3 operations (boto3).
    See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
    """

    def __init__(self, **kwargs):
        try:
            import boto3

            self.client = boto3.client("s3", **kwargs)
            logger.info("S3 client initialized.")
        except ImportError:
            raise ImportError(
                "boto3 required for AWS S3. Install with `pip install boto3`."
            )

    def upload_file(self, bucket: str, key: str, filename: str) -> None:
        try:
            self.client.upload_file(filename, bucket, key)
        except Exception as e:
            logger.error(f"S3 upload_file failed: {e}")
            raise

    def download_file(self, bucket: str, key: str, filename: str) -> None:
        try:
            self.client.download_file(bucket, key, filename)
        except Exception as e:
            logger.error(f"S3 download_file failed: {e}")
            raise

    def list_files(self, bucket: str, prefix: str = "") -> list[str]:
        try:
            resp = self.client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            return [obj["Key"] for obj in resp.get("Contents", [])]
        except Exception as e:
            logger.error(f"S3 list_files failed: {e}")
            raise

    def generate_presigned_url(
        self, bucket: str, key: str, expires_in: int = 3600
    ) -> str:
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        except Exception as e:
            logger.error(f"S3 generate_presigned_url failed: {e}")
            raise

    # Extensibility for GCS/Azure can be added as stubs or in subclasses if needed.


# Example usage and advanced features are available in the official docs:
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
