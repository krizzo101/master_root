"""
Real-Time Collaborative Document Editing Web Application — Python Backend Layer

Implements the API gateway, real-time (WebSocket) services, OAuth 2.0 authentication, JWT session issuance, file upload orchestration,
AI summarization/suggestion proxy, versioning, and search on top of PostgreSQL.

This Python backend focuses on security, scalability, and composability, providing a powerful entrypoint for frontend and real-time collaboration services.

Note: Some platform integrations involving JavaScript (e.g. Passport.js, Apollo Server) are referenced but not implemented in this Python-centric project.
"""
import os
import logging
from typing import Optional, List

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Request,
    status,
    Depends,
    UploadFile,
    File,
    Form,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import BaseModel
import jwt
import secrets
from datetime import datetime, timedelta
import psycopg2
from passlib.hash import bcrypt_sha256
import uuid
import redis
import aiohttp

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# FastAPI Application
app = FastAPI(title="Real-Time Collaborative Document Editing API", docs_url="/docs")

# Security Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 86400

# OAuth2 (Google for example) — configuration examples
OAUTH2_CLIENT_ID = os.environ.get("OAUTH2_CLIENT_ID", "demo-client-id")
OAUTH2_CLIENT_SECRET = os.environ.get("OAUTH2_CLIENT_SECRET", "demo-client-secret")
OAUTH2_REDIRECT_URI = os.environ.get(
    "OAUTH2_REDIRECT_URI", "http://localhost:8000/api/auth/callback"
)
OAUTH2_AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/auth"
OAUTH2_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
OAUTH2_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"

# Database Configuration
PG_HOST = os.environ.get("PG_HOST", "localhost")
PG_USER = os.environ.get("PG_USER", "postgres")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "postgres")
PG_DB = os.environ.get("PG_DB", "realtime_docs")

# Redis Configuration
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# AWS S3 Example
S3_BUCKET = os.environ.get("S3_BUCKET", "demo-bucket")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "demo-aws-key")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "demo-aws-secret")

# AI Summarization/Suggestions
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "demo-openai-key")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# CORS Setup
origins = [
    "http://localhost:3000",
    "https://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database Connection Helpers
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=PG_DB,
            connect_timeout=5,
        )
        return conn
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        raise


# Redis Helper
redis_pool = redis.ConnectionPool.from_url(REDIS_URL)
redis_conn = redis.Redis(connection_pool=redis_pool)


# Models
class User(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class Document(BaseModel):
    id: str
    title: str
    content: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    version: int


class DocumentVersion(BaseModel):
    id: str
    doc_id: str
    content: str
    created_at: datetime
    editor_id: str
    version: int


class AIRequest(BaseModel):
    document: str
    instruction: Optional[str] = "Summarize this document."


# Exception Handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


# JWT Encoding/Decoding
def issue_jwt(user: User) -> str:
    payload = {
        "sub": user.id,
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_jwt(token: str) -> Optional[User]:
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return User(id=decoded["sub"], email=decoded["email"])
    except Exception as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


def get_current_user(request: Request) -> Optional[User]:
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    return verify_jwt(token)


# OAuth2 Callback Handler
@app.get("/api/auth/callback")
async def oauth2_callback(code: str):
    """Handles OAuth2 authorization code exchange, issues JWT."""
    # For demo: Fake token, get email from provider,
    # In real application, use aiohttp to POST to token endpoint, fetch access_token and then /userinfo
    logger.info(f"OAuth2 callback with code: {code}")
    async with aiohttp.ClientSession() as session:
        try:
            token_resp = await session.post(
                OAUTH2_TOKEN_ENDPOINT,
                data={
                    "code": code,
                    "client_id": OAUTH2_CLIENT_ID,
                    "client_secret": OAUTH2_CLIENT_SECRET,
                    "redirect_uri": OAUTH2_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
                timeout=10,
            )
            token_data = await token_resp.json()
            access_token = token_data["access_token"]
            userinfo_resp = await session.get(
                OAUTH2_USERINFO_ENDPOINT,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            userinfo = await userinfo_resp.json()
            # Find or create user in DB. For the demo, we'll assume user exists.
            user = User(
                id=userinfo["sub"], email=userinfo["email"], name=userinfo.get("name")
            )
            jwt_token = issue_jwt(user)
            # Set as cookie or return in response body
            return JSONResponse({"token": jwt_token})
        except Exception as e:
            logger.error(f"OAuth2 token exchange failed: {e}")
            raise HTTPException(status_code=400, detail="OAuth2 authentication failed.")


# User Info Endpoint
@app.get("/api/me")
async def get_me(request: Request):
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return user.dict()


# Document CRUD
@app.post("/api/documents", response_model=Document)
async def create_document(
    title: str = Form(...), content: str = Form(...), request: Request = None
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    doc_id = str(uuid.uuid4())
    now = datetime.utcnow()
    try:
        conn = get_db_connection()
        with conn, conn.cursor() as cur:
            cur.execute(
                (
                    """
                INSERT INTO documents (id, title, content, owner_id, created_at, updated_at, version)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
                ),
                (doc_id, title, content, user.id, now, now, 1),
            )
        conn.close()
        logger.info(f"Document created: {doc_id} by {user.id}")
        return Document(
            id=doc_id,
            title=title,
            content=content,
            owner_id=user.id,
            created_at=now,
            updated_at=now,
            version=1,
        )
    except Exception as e:
        logger.error(f"Document creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create document.")


@app.get("/api/documents", response_model=List[Document])
async def list_documents(request: Request, search: Optional[str] = None):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    try:
        conn = get_db_connection()
        with conn, conn.cursor() as cur:
            if search:
                cur.execute(
                    """
                    SELECT id, title, content, owner_id, created_at, updated_at, version
                    FROM documents
                    WHERE owner_id = %s AND to_tsvector('english', content) @@ plainto_tsquery('english', %s)
                    ORDER BY updated_at DESC
                    LIMIT 50
                    """,
                    (user.id, search),
                )
            else:
                cur.execute(
                    """
                    SELECT id, title, content, owner_id, created_at, updated_at, version FROM documents
                    WHERE owner_id = %s
                    ORDER BY updated_at DESC
                    LIMIT 50
                    """,
                    (user.id,),
                )
            docs = [
                Document(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    owner_id=row[3],
                    created_at=row[4],
                    updated_at=row[5],
                    version=row[6],
                )
                for row in cur.fetchall()
            ]
        conn.close()
        return docs
    except Exception as e:
        logger.error(f"Document list failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents.")


@app.get("/api/documents/{doc_id}", response_model=Document)
async def get_document(doc_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    try:
        conn = get_db_connection()
        with conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, content, owner_id, created_at, updated_at, version FROM documents WHERE id = %s",
                (doc_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Document not found.")
            doc = Document(
                id=row[0],
                title=row[1],
                content=row[2],
                owner_id=row[3],
                created_at=row[4],
                updated_at=row[5],
                version=row[6],
            )
        conn.close()
        if doc.owner_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized.")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document.")


@app.put("/api/documents/{doc_id}", response_model=Document)
async def update_document(
    doc_id: str,
    title: str = Form(None),
    content: str = Form(None),
    request: Request = None,
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    try:
        conn = get_db_connection()
        with conn, conn.cursor() as cur:
            # Fetch current version
            cur.execute(
                "SELECT id, title, content, owner_id, created_at, updated_at, version FROM documents WHERE id = %s",
                (doc_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Document not found.")
            if row[3] != user.id:
                raise HTTPException(status_code=403, detail="Not authorized.")
            now = datetime.utcnow()
            new_title = title if title else row[1]
            new_content = content if content else row[2]
            new_version = row[6] + 1
            cur.execute(
                "UPDATE documents SET title = %s, content = %s, updated_at = %s, version = %s WHERE id = %s",
                (new_title, new_content, now, new_version, doc_id),
            )
            # Save previous version into document_versions
            cur.execute(
                "INSERT INTO document_versions (id, doc_id, content, created_at, editor_id, version) VALUES (%s, %s, %s, %s, %s, %s)",
                (str(uuid.uuid4()), doc_id, row[2], now, user.id, row[6]),
            )
            doc = Document(
                id=doc_id,
                title=new_title,
                content=new_content,
                owner_id=user.id,
                created_at=row[4],
                updated_at=now,
                version=new_version,
            )
        conn.close()
        logger.info(f"Document updated: {doc_id} v{new_version}")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update document failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update document.")


@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    try:
        conn = get_db_connection()
        with conn, conn.cursor() as cur:
            cur.execute("SELECT owner_id FROM documents WHERE id = %s", (doc_id,))
            row = cur.fetchone()
            if not row or row[0] != user.id:
                raise HTTPException(status_code=403, detail="Not authorized.")
            cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
        conn.close()
        return {"detail": "Document deleted."}
    except Exception as e:
        logger.error(f"Delete document failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document.")


# Document Versioning
@app.get("/api/documents/{doc_id}/history", response_model=List[DocumentVersion])
async def get_document_history(doc_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    try:
        conn = get_db_connection()
        with conn, conn.cursor() as cur:
            cur.execute("SELECT owner_id FROM documents WHERE id = %s", (doc_id,))
            row = cur.fetchone()
            if not row or row[0] != user.id:
                raise HTTPException(status_code=403, detail="Not authorized.")
            cur.execute(
                "SELECT id, doc_id, content, created_at, editor_id, version FROM document_versions WHERE doc_id = %s ORDER BY version DESC",
                (doc_id,),
            )
            history = [
                DocumentVersion(
                    id=r[0],
                    doc_id=r[1],
                    content=r[2],
                    created_at=r[3],
                    editor_id=r[4],
                    version=r[5],
                )
                for r in cur.fetchall()
            ]
        conn.close()
        return history
    except Exception as e:
        logger.error(f"Document history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document history.")


@app.put("/api/documents/{doc_id}/revert/{version}", response_model=Document)
async def revert_document_version(doc_id: str, version: int, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    try:
        conn = get_db_connection()
        with conn, conn.cursor() as cur:
            cur.execute("SELECT owner_id FROM documents WHERE id = %s", (doc_id,))
            row = cur.fetchone()
            if not row or row[0] != user.id:
                raise HTTPException(status_code=403, detail="Not authorized.")
            cur.execute(
                "SELECT content FROM document_versions WHERE doc_id = %s AND version = %s",
                (doc_id, version),
            )
            cv = cur.fetchone()
            if not cv:
                raise HTTPException(status_code=404, detail="Version not found.")
            content = cv[0]
            now = datetime.utcnow()
            # update main document
            cur.execute(
                "UPDATE documents SET content = %s, updated_at = %s, version = version + 1 WHERE id = %s RETURNING title, owner_id, created_at, version",
                (content, now, doc_id),
            )
            r = cur.fetchone()
            doc = Document(
                id=doc_id,
                title=r[0],
                content=content,
                owner_id=r[1],
                created_at=r[2],
                updated_at=now,
                version=r[3],
            )
        conn.close()
        logger.info(f"Document {doc_id} reverted to version {version}")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revert document version failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to revert.")


# File Upload + Presigned URLs
@app.post("/api/documents/{doc_id}/upload")
async def upload_file(
    doc_id: str, file: UploadFile = File(...), request: Request = None
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    try:
        # Generate presigned upload URL (simulated for demo)
        import boto3

        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
        )
        filename = f"uploads/{doc_id}/{uuid.uuid4()}_{file.filename}"
        presigned = s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": S3_BUCKET, "Key": filename},
            ExpiresIn=900,
        )
        # Here, store attachment record in DB
        return {"url": presigned, "key": filename}
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate upload url.")


# AI Summarization/Suggestion Proxy
@app.post("/api/ai/summarize")
async def ai_summarize(ai_request: AIRequest, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        }
        payload = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": ai_request.instruction},
                {"role": "user", "content": ai_request.document},
            ],
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OPENAI_API_URL, headers=headers, json=payload, timeout=15
            ) as resp:
                data = await resp.json()
        summary = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"summary": summary}
    except Exception as e:
        logger.error(f"AI summarization failed: {e}")
        raise HTTPException(status_code=500, detail="Unable to summarize document.")


# Real-time Collaboration (WebSocket broker/proxy for upstream service like Node/Yjs)
connections = {}


@app.websocket("/ws/documents/{doc_id}")
async def websocket_doc_collab(websocket: WebSocket, doc_id: str):
    # JWT required in query param or Cookie (demo: from query param)
    await websocket.accept()
    params = websocket.query_params
    token = params.get("token", None)
    if not token or not verify_jwt(token):
        await websocket.close(4401)
        return
    logger.info(f"WebSocket connection for doc {doc_id}")
    if doc_id not in connections:
        connections[doc_id] = set()
    connections[doc_id].add(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Broadcast to other connected clients (node/yjs service may also relay this)
            for conn in connections[doc_id].copy():
                if conn != websocket:
                    try:
                        await conn.send_json(data)
                    except Exception:
                        pass  # ignore dead connections
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for doc {doc_id}")
        connections[doc_id].remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(1011)
        except:
            pass
    finally:
        connections[doc_id].discard(websocket)


# Health/Readiness Probes
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
