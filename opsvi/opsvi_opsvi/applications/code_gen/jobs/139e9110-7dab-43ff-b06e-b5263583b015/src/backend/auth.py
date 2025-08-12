"""
Auth module: JWT login, registration, OIDC callback, role check, password hashing
"""
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.database import get_db
from backend.models import User, UserRole

logger = logging.getLogger("taskmgmt.auth")
router = APIRouter()
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = settings.jwt_secret
ALGORITHM = settings.jwt_algo
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8


class TokenData:
    def __init__(self, user_id: str, role: str):
        self.user_id = user_id
        self.role = role


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_user(email: str, db: Session) -> User | None:
    return db.query(User).filter(User.email.ilike(email)).first()


def authenticate(email: str, password: str, db: Session) -> User | None:
    user = get_user(email, db)
    if user and verify_password(password, user.hashed_password):
        return user
    return None


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        return TokenData(user_id, role)
    except JWTError:
        logger.exception("JWT Decode failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing auth header")
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid scheme")
    payload = decode_access_token(token)
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="Invalid user")
    return user


def require_role(required: UserRole):
    def wrapper(user: User = Depends(get_current_user)):
        if user.role != required:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return wrapper


@router.post("/register")
def register_user(payload: dict, db: Session = Depends(get_db)):
    email = payload["email"]
    if get_user(email, db):
        raise HTTPException(400, "Email already exists")
    hashed = hash_password(payload["password"])
    user = User(
        email=email,
        hashed_password=hashed,
        full_name=payload.get("full_name", email),
    )
    db.add(user)
    db.commit()
    return {"message": "User registered", "user_id": user.id}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate(form.username, form.password, db)
    if not user:
        raise HTTPException(401, "Bad credentials")
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "role": user.role, "email": user.email},
    }
