import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, cast

# Third-party imports
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy.orm import Session

# Local application imports
from config import get_settings
from database import database
from model import models

# --- Konfigurasi Passlib & Bcrypt Shim ---
try:
    import bcrypt as _bcrypt  # type: ignore
    if not hasattr(_bcrypt, "__about__") and hasattr(_bcrypt, "__version__"):
        class _About:
            __version__ = getattr(_bcrypt, "__version__", "4.0.0")
        _bcrypt.__about__ = _About()  # type: ignore[attr-defined]
except Exception:
    pass

# --- Setup ---
settings = get_settings()
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

logger = logging.getLogger("auth")

# Konfigurasi Hashing Password
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],
    deprecated="auto",
)

# Skema Auth OAuth2 (Endpoint token diarahkan ke /token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# --- Helper Functions ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Memverifikasi apakah password plain cocok dengan hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        return False


def get_password_hash(password: str) -> str:
    """Membuat hash dari password plain."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Membuat JWT Access Token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- Core Logic ---

def authenticate_user(db: Session, nip: str, password: str) -> Optional[models.User]:
    """
    Mencari user berdasarkan NIP dan memverifikasi password.
    Return User object jika sukses, None jika gagal.
    """
    if settings.debug:
        logger.debug(f"AUTH: Memulai autentikasi untuk NIP={nip}")
    
    # UPDATE: Menggunakan nama atribut baru (nip)
    user = db.query(models.User).filter(models.User.nip == nip).first()
    
    if not user:
        if settings.debug:
            logger.debug("AUTH: User tidak ditemukan")
        return None
        
    # UPDATE: Menggunakan nama atribut baru (password)
    hashed_password = cast(str, user.password)
    
    if not verify_password(password, hashed_password):
        if settings.debug:
            logger.debug("AUTH: Password salah")
        return None
        
    if settings.debug:
        logger.debug(f"AUTH: Sukses login user_id={user.id}")
        
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(database.get_db)
) -> models.User:
    """
    Dependency untuk mendapatkan current user dari JWT Token.
    Akan raise 401 jika token tidak valid atau expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tidak bisa validasi token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if settings.debug:
        logger.debug(f"AUTH: Validasi token masuk, prefix={token[:10]}...")

    try:
        # Decode JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if settings.debug:
            logger.debug(f"AUTH: Payload keys={list(payload.keys())}")
            
        sub: Optional[str] = payload.get("sub")
        
        if sub is None:
            if settings.debug:
                logger.debug("AUTH: Claim 'sub' (NIP) tidak ditemukan dalam token")
            raise credentials_exception
            
        token_nip = sub
        
    except JWTError as e:
        if settings.debug:
            logger.debug(f"AUTH: JWT Error - {str(e)}")
        raise credentials_exception

    # UPDATE: Menggunakan nama atribut baru (nip)
    user = db.query(models.User).filter(models.User.nip == token_nip).first()
    
    if user is None:
        if settings.debug:
            logger.debug("AUTH: User dari token tidak ditemukan di Database")
        raise credentials_exception
        
    if settings.debug:
        logger.debug(f"AUTH: User terotorisasi ID={user.id}")
        
    return user