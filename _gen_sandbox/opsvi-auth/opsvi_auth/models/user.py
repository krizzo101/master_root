"""User model utilities for opsvi-auth.

This module provides a lightweight, self-contained, typed User model suitable
for authentication-related operations: creating users, hashing/verifying
passwords, managing roles and API tokens, and serializing to/from dictionaries.

The cryptography uses hashlib.pbkdf2_hmac with a per-user salt and secure
comparison to avoid timing attacks. Async functions are provided for common
operations to fit into asyncio-based applications; they are thin wrappers over
CPU-bound calls.
"""
from __future__ import annotations

import asyncio
import base64
import dataclasses
import datetime
import hashlib
import hmac
import re
import secrets
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


PWD_ALGORITHM = "pbkdf2_sha256"
PWD_ITERATIONS = 100_000
SALT_BYTES = 16
DERIVED_KEY_BYTES = 32

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


def _generate_salt() -> str:
    return secrets.token_hex(SALT_BYTES)


def _derive_key(password: str, salt: str, iterations: int = PWD_ITERATIONS) -> str:
    """Derive a key from password and salt and return it as base64 string."""
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations, dklen=DERIVED_KEY_BYTES
    )
    return base64.b64encode(dk).decode("ascii")


def _format_hashed_password(salt: str, derived_key_b64: str, iterations: int = PWD_ITERATIONS) -> str:
    return f"{PWD_ALGORITHM}${iterations}${salt}${derived_key_b64}"


def _parse_hashed_password(hashed: str) -> Optional[Dict[str, Any]]:
    try:
        alg, iterations_s, salt, dk_b64 = hashed.split("$", 3)
        iterations = int(iterations_s)
        return {"alg": alg, "iterations": iterations, "salt": salt, "dk_b64": dk_b64}
    except Exception:
        return None


@dataclass
class User:
    """Represent an application user.

    Passwords are stored in a hashed form using PBKDF2-HMAC-SHA256 with a
    per-user salt. API tokens are generated randomly and stored hashed using the
    same mechanism to avoid storing plaintext credentials.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    email: str = ""
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    roles: List[str] = field(default_factory=list)
    # Stored encoded password: algorithm$iterations$salt$derived_key_b64
    hashed_password: Optional[str] = None
    # Stored encoded token (same format as password). None when no token issued.
    hashed_api_token: Optional[str] = None
    created_at: datetime.datetime = field(default_factory=_now_utc)
    last_login: Optional[datetime.datetime] = None

    def __post_init__(self) -> None:
        if self.email:
            self.email = self.email.strip().lower()
            if not EMAIL_RE.match(self.email):
                raise ValueError(f"Invalid email address: {self.email}")

    @property
    def is_authenticated(self) -> bool:
        """Simple property for frameworks that expect an "is_authenticated" flag."""
        return True

    async def set_password(self, password: str) -> None:
        """Hash and set the user's password asynchronously."""
        # Keep the CPU-bound work inside a thread to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        self.hashed_password = await loop.run_in_executor(None, self._sync_hash_password, password)

    def _sync_hash_password(self, password: str) -> str:
        if not password:
            raise ValueError("Password must not be empty")
        salt = _generate_salt()
        dk = _derive_key(password, salt)
        return _format_hashed_password(salt, dk)

    async def verify_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash asynchronously."""
        if not self.hashed_password:
            return False
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_verify_password, password)

    def _sync_verify_password(self, password: str) -> bool:
        parsed = _parse_hashed_password(self.hashed_password or "")
        if not parsed:
            return False
        expected_dk_b64 = parsed["dk_b64"]
        salt = parsed["salt"]
        iterations = parsed["iterations"]
        # derive key with same params
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations, dklen=DERIVED_KEY_BYTES)
        dk_b64 = base64.b64encode(dk).decode("ascii")
        # constant-time comparison
        return hmac.compare_digest(dk_b64, expected_dk_b64)

    async def generate_api_token(self) -> str:
        """Generate and store a new API token and return the plaintext token.

        The stored hashed_api_token is the hashed representation; the plaintext
        token is returned exactly once so callers should persist it to the user.
        """
        token = secrets.token_urlsafe(32)
        loop = asyncio.get_running_loop()
        hashed = await loop.run_in_executor(None, self._sync_hash_token, token)
        self.hashed_api_token = hashed
        return token

    def _sync_hash_token(self, token: str) -> str:
        salt = _generate_salt()
        dk = _derive_key(token, salt)
        return _format_hashed_password(salt, dk)

    async def verify_api_token(self, token: str) -> bool:
        """Verify an API token against the stored hashed token asynchronously."""
        if not self.hashed_api_token:
            return False
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_verify_token, token)

    def _sync_verify_token(self, token: str) -> bool:
        parsed = _parse_hashed_password(self.hashed_api_token or "")
        if not parsed:
            return False
        expected_dk_b64 = parsed["dk_b64"]
        salt = parsed["salt"]
        iterations = parsed["iterations"]
        dk = hashlib.pbkdf2_hmac("sha256", token.encode("utf-8"), salt.encode("utf-8"), iterations, dklen=DERIVED_KEY_BYTES)
        dk_b64 = base64.b64encode(dk).decode("ascii")
        return hmac.compare_digest(dk_b64, expected_dk_b64)

    def has_role(self, role: str) -> bool:
        """Return True if the user has the given role."""
        return role in self.roles

    def add_role(self, role: str) -> None:
        if role not in self.roles:
            self.roles.append(role)

    def remove_role(self, role: str) -> None:
        try:
            self.roles.remove(role)
        except ValueError:
            pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the user to a plain dictionary (safe for storage).

        Note: hashed_password and hashed_api_token are included because they are
        required to authenticate later. Do not leak the plaintext token.
        """
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "roles": list(self.roles),
            "hashed_password": self.hashed_password,
            "hashed_api_token": self.hashed_api_token,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create a User instance from a dictionary created by to_dict()."""
        created_at = (
            datetime.datetime.fromisoformat(data["created_at"]) if data.get("created_at") else _now_utc()
        )
        last_login = (
            datetime.datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None
        )
        return cls(
            id=data.get("id", uuid.uuid4().hex),
            email=data.get("email", ""),
            full_name=data.get("full_name"),
            is_active=bool(data.get("is_active", True)),
            is_superuser=bool(data.get("is_superuser", False)),
            roles=list(data.get("roles", [])),
            hashed_password=data.get("hashed_password"),
            hashed_api_token=data.get("hashed_api_token"),
            created_at=created_at,
            last_login=last_login,
        )

    async def touch_last_login(self) -> None:
        """Update last_login to now (async wrapper)."""
        self.last_login = _now_utc()
        # yield control to event loop in case callers expect an awaitable
        await asyncio.sleep(0)


# Convenience factory
async def create_user(email: str, password: str, full_name: Optional[str] = None, roles: Optional[List[str]] = None) -> User:
    """Create a new user with the given email and password.

    Returns the created User object with password hashed. This is async to fit
    into asyncio workflows.
    """
    user = User(email=email, full_name=full_name, roles=list(roles or []))
    await user.set_password(password)
    return user
