from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from typing import Any, cast
from model import models
from database import database
from config import get_settings
import logging

settings = get_settings()
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],
    deprecated="auto",
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

logger = logging.getLogger("auth")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(db: Session, nip: str, password: str):
    if settings.debug:
        logger.debug(f"AUTH: mulai authenticate nip={nip}")
    user = db.query(models.User).filter(models.User.NIP == nip).first()
    if not user:
        if settings.debug:
            logger.debug("AUTH: user tidak ditemukan")
        return False
    hashed_password: str = cast(str, user.Password)
    if not verify_password(password, hashed_password):
        if settings.debug:
            logger.debug("AUTH: password salah")
        return False
    if settings.debug:
        logger.debug(f"AUTH: sukses user_id={user.ID}")
    return user


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Tidak bisa validasi token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if settings.debug:
        logger.debug(f"AUTH: validasi token masuk, prefix={token[:15]}...")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if settings.debug:
            logger.debug(f"AUTH: payload decoded keys={list(payload.keys())}")
        sub = payload.get("sub")
        if not isinstance(sub, str):
            if settings.debug:
                logger.debug("AUTH: claim sub invalid")
            raise credentials_exception
        nip: str = sub
    except JWTError as e:
        if settings.debug:
            logger.debug(f"AUTH: JWTError {e}")
        raise credentials_exception
    user = db.query(models.User).filter(models.User.NIP == nip).first()
    if user is None:
        if settings.debug:
            logger.debug("AUTH: user dari token tidak ditemukan di DB")
        raise credentials_exception
    if settings.debug:
        logger.debug(f"AUTH: user terotorisasi id={user.ID}")
    return user

