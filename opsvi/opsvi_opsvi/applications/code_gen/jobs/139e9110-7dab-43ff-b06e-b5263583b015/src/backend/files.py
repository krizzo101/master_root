"""
File storage using AWS S3-compatible endpoint and signed URLs; upload/download; associates files with comments or tasks
"""
import uuid

import boto3
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi import File as FastAPIFile
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.config import get_settings
from backend.database import get_db
from backend.models import File as FileModel

settings = get_settings()
s3 = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
)

storage_router = APIRouter()


@storage_router.post("/upload", response_model=dict)
def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    key = f"uploads/{uuid.uuid4()}_{file.filename}"
    s3.upload_fileobj(file.file, settings.s3_bucket, key)
    url = s3.generate_presigned_url(
        "get_object", ExpiresIn=3600, Params={"Bucket": settings.s3_bucket, "Key": key}
    )
    file_model = FileModel(filename=file.filename, url=url, uploader_id=user.id)
    db.add(file_model)
    db.commit()
    return {"file_id": file_model.id, "url": url}


@storage_router.get("/download/{file_id}", response_model=dict)
def download_file(
    file_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    file = db.query(FileModel).filter_by(id=file_id).first()
    if not file:
        raise HTTPException(404, "File not found")
    url = file.url
    return {"file_id": file.id, "url": url}
