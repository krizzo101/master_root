"""
Main entry point for the Real-Time Collaborative Document Editing Web Application Backend API.

- API via FastAPI (REST) and WebSocket for real-time collaboration
- OAuth2/JWT authentication
- Document CRUD
- File upload integration (S3)
- AI summarization (mocked provider)
- Fulltext search (Elasticsearch)
- Version history & audit trail

This is a minimal but complete kernel implementation of the backend in Python,
meant to be the authoritative FastAPI app.
"""

import logging
import os
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Request,
    Response,
    status,
    HTTPException,
    UploadFile,
    File,
    Form,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import List, Optional, Any, Dict
import uuid
import asyncio
from datetime import datetime, timedelta
from .models import User, Document, DocumentVersion, UserPresence, AuditLog
from . import crud, auth, config, ai, search, file as filemod, collab

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rt-collab-backend")

app = FastAPI(title="Real-Time Collaborative Doc Edit API", version="1.0.0")

# CORS setup for frontend-dev interaction
origins = config.CORS_ORIGINS or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


@app.get("/health")
def health_check() -> Dict[str, str]:
    """App health endpoint."""
    return {"status": "ok"}


# --- AUTH ---


@app.post("/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 login and JWT token issue."""
    user = await crud.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        user = await crud.get_user_by_username(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except JWTError as e:
        logger.warning(f"JWTError: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


# --- USER DASHBOARD ---


@app.get("/users/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user.dict()


# --- DOCUMENT CRUD/APIs ---


@app.post("/documents", response_model=Document)
async def create_document(
    title: str = Form(...),
    body: str = Form(""),
    current_user: User = Depends(get_current_user),
):
    """Create a new document."""
    return await crud.create_document(current_user, title, body)


@app.get("/documents", response_model=List[Document])
async def list_documents(current_user: User = Depends(get_current_user)):
    """List all documents visible to current user."""
    return await crud.list_documents(current_user)


@app.get("/documents/{doc_id}", response_model=Document)
async def get_document(doc_id: str, current_user: User = Depends(get_current_user)):
    """Get a document by ID."""
    return await crud.get_document(current_user, doc_id)


@app.put("/documents/{doc_id}", response_model=Document)
async def update_document(
    doc_id: str,
    title: str = Form(...),
    body: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    """Update a document."""
    return await crud.update_document(current_user, doc_id, title, body)


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, current_user: User = Depends(get_current_user)):
    """Delete a document."""
    await crud.delete_document(current_user, doc_id)
    return {"status": "deleted"}


# --- DOCUMENT VERSIONING ---


@app.get("/documents/{doc_id}/versions", response_model=List[DocumentVersion])
async def get_document_versions(
    doc_id: str, current_user: User = Depends(get_current_user)
):
    return await crud.get_document_versions(current_user, doc_id)


@app.post("/documents/{doc_id}/restore/{version_id}", response_model=Document)
async def restore_document_version(
    doc_id: str, version_id: str, current_user: User = Depends(get_current_user)
):
    return await crud.restore_document_version(current_user, doc_id, version_id)


# --- SEARCH ---


@app.get("/search", response_model=List[Document])
async def search_docs(query: str, current_user: User = Depends(get_current_user)):
    """Fulltext search documents."""
    return await search.search_documents(current_user, query)


# --- FILE UPLOAD ---


@app.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...), current_user: User = Depends(get_current_user)
):
    """Upload a file and link to document."""
    result = await filemod.handle_upload(file, current_user)
    return result


@app.get("/files/{file_id}/download")
async def get_presigned_download_url(
    file_id: str, current_user: User = Depends(get_current_user)
):
    return await filemod.get_download_url(file_id, current_user)


# --- AI SUGGESTIONS/SUMMARIZATION ---


@app.post("/ai/summarize")
async def summarize_body(
    body: str = Form(...), current_user: User = Depends(get_current_user)
):
    """Summarize document body using AI."""
    return await ai.summarize(body)


@app.post("/ai/suggest")
async def suggest_content(
    body: str = Form(...), current_user: User = Depends(get_current_user)
):
    """Return AI suggestions for document improvement."""
    return await ai.suggest(body)


# --- REAL-TIME COLLABORATION (WEBSOCKET) ---


@app.websocket("/ws/collab/{doc_id}")
async def collab_ws_endpoint(websocket: WebSocket, doc_id: str, token: str):
    """
    WebSocket endpoint for collaborative editing of a document.
    Client must send JWT as `token` query param for auth.
    """
    # Token verification
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
        username: str = payload.get("sub")
        user = await crud.get_user_by_username(username)
        if user is None:
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4002)
        return
    await collab.join_collab_room(doc_id, websocket, user)


# --- AUDIT LOGS ---


@app.get("/audit", response_model=List[AuditLog])
async def get_audit_logs(current_user: User = Depends(get_current_user)):
    """Get audit logs for your documents."""
    return await crud.get_audit_logs(current_user)


# --- ERROR HANDLING ---


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Server error: {repr(exc)}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
