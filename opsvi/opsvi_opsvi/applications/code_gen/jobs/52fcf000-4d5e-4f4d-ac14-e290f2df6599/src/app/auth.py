"""
Authentication and authorization (JWT, password hashing, current user dep).
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.db import get_db
from app.schemas import UserCreate, UserLogin, UserRead, Token

router = APIRouter()
logger = logging.getLogger("auth")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# Password hashing utils
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


# JWT token utils
def create_access_token(
    subject: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Generate JWT token (user claims)."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = subject.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email/password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """OAuth2 dependency: Parse JWT and fetch user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


@router.post("/signup", response_model=UserRead)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """User registration/signup."""
    existing = (
        db.query(User)
        .filter((User.username == user_in.username) | (User.email == user_in.email))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Username or email already registered."
        )
    hashed_password = get_password_hash(user_in.password)
    user = User(
        username=user_in.username, email=user_in.email, hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Registered new user: {user.username}")
    return user


@router.post("/token", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """User login, returns JWT access token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(
        subject={
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
        }
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user."""
    return current_user
