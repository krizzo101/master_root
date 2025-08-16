"""
CRUD operations and business logic for User, Document, Version, Audit.
Uses simple in-memory/persistent implementations -- swap for ORM/DB in real-life.
"""
from typing import List, Optional
from datetime import datetime
import uuid
from .models import User, Document, DocumentVersion, AuditLog
from .auth import get_password_hash, verify_password
import logging

# In-memory emulation/datastore for demo; replace with DB/ORM logic
_USERS = {
    "testuser": User(
        id="u1",
        username="testuser",
        email="user@example.com",
        full_name="Test User",
        disabled=False,
        created_at=datetime.utcnow(),
    )
}
_USER_PW = {"testuser": get_password_hash("password123")}
_DOCUMENTS = {}
_VERSIONS = {}
_AUDIT_LOGS = []


async def authenticate_user(username: str, password: str) -> Optional[User]:
    user = _USERS.get(username)
    if not user:
        return None
    if not verify_password(password, _USER_PW[username]):
        return None
    return user


async def get_user_by_username(username: str) -> Optional[User]:
    return _USERS.get(username)


async def create_document(user: User, title: str, body: str) -> Document:
    doc_id = str(uuid.uuid4())
    now = datetime.utcnow()
    doc = Document(
        id=doc_id,
        owner_id=user.id,
        title=title,
        body=body,
        created_at=now,
        updated_at=now,
        collaborators=[user.id],
        current_version=1,
    )
    _DOCUMENTS[doc_id] = doc
    await _add_version(doc, user)  # Save initial version
    await _log(user.id, doc_id, "create_document", f"Title: {title}")
    return doc


async def get_document(user: User, doc_id: str) -> Document:
    doc = _DOCUMENTS.get(doc_id)
    if not doc:
        raise Exception("Document not found")
    if user.id not in doc.collaborators and user.id != doc.owner_id:
        raise Exception("Forbidden")
    return doc


async def update_document(user: User, doc_id: str, title: str, body: str) -> Document:
    doc = await get_document(user, doc_id)
    doc.body = body
    doc.title = title
    doc.updated_at = datetime.utcnow()
    doc.current_version += 1
    _DOCUMENTS[doc_id] = doc
    await _add_version(doc, user)
    await _log(user.id, doc_id, "update_document", f"Version: {doc.current_version}")
    return doc


async def delete_document(user: User, doc_id: str) -> None:
    doc = await get_document(user, doc_id)
    _DOCUMENTS.pop(doc_id, None)
    _VERSIONS.pop(doc_id, None)
    await _log(user.id, doc_id, "delete_document", "Deleted")


async def list_documents(user: User) -> List[Document]:
    return [
        doc
        for doc in _DOCUMENTS.values()
        if user.id in doc.collaborators or user.id == doc.owner_id
    ]


async def _add_version(doc: Document, author: User) -> None:
    ver = DocumentVersion(
        id=str(uuid.uuid4()),
        doc_id=doc.id,
        version=doc.current_version,
        title=doc.title,
        body=doc.body,
        created_at=datetime.utcnow(),
        author_id=author.id,
    )
    _VERSIONS.setdefault(doc.id, []).append(ver)


async def get_document_versions(user: User, doc_id: str) -> List[DocumentVersion]:
    doc = await get_document(user, doc_id)
    return _VERSIONS.get(doc_id, [])


async def restore_document_version(
    user: User, doc_id: str, version_id: str
) -> Document:
    doc = await get_document(user, doc_id)
    versions = _VERSIONS.get(doc_id, [])
    ver = next((v for v in versions if v.id == version_id), None)
    if not ver:
        raise Exception("Version not found")
    doc.body = ver.body
    doc.title = ver.title
    doc.current_version += 1
    doc.updated_at = datetime.utcnow()
    await _add_version(doc, user)
    await _log(user.id, doc_id, "restore_version", f"Restored to version {ver.version}")
    return doc


async def get_audit_logs(user: User) -> List[AuditLog]:
    return [l for l in _AUDIT_LOGS if l.user_id == user.id]


async def _log(user_id: str, doc_id: str, action: str, detail: str) -> None:
    l = AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        doc_id=doc_id,
        action=action,
        detail=detail,
        timestamp=datetime.utcnow(),
        ip="127.0.0.1",  # Mocked IP
    )
    _AUDIT_LOGS.append(l)
