"""
File upload/download handler (S3-mock, real usage: boto3 or aioboto3 for AWS S3).
"""
from fastapi import UploadFile
from typing import Dict
import uuid
from .models import User
from . import config

# In-memory metadata; real: store in DB and S3
_FILEMETA = {}


async def handle_upload(file: UploadFile, current_user: User) -> Dict:
    file_id = str(uuid.uuid4())
    filename = file.filename
    # Just read chunk to "store" (simulate S3 upload)
    data = await file.read()  # In production, stream to S3
    # Simulated S3 URL
    url = f"https://{config.S3_BUCKET}.s3.{config.S3_REGION}.amazonaws.com/{file_id}/{filename}"
    _FILEMETA[file_id] = {"owner": current_user.id, "filename": filename, "url": url}
    return {"file_id": file_id, "url": url}


async def get_download_url(file_id: str, current_user: User) -> Dict:
    meta = _FILEMETA.get(file_id)
    if not meta or meta["owner"] != current_user.id:
        raise Exception("Not found or forbidden.")
    return {"url": meta["url"]}
