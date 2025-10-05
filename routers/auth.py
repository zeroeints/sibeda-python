from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any, Dict
import controller.auth as auth
import schemas.schemas as schemas
from database.database import SessionLocal

router = APIRouter(tags=["Auth"])  # no prefix for login

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login", response_model=schemas.SuccessResponse[schemas.Token])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> schemas.SuccessResponse[schemas.Token]:
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="NIP atau password salah")
    role = user.Role.value if hasattr(user.Role, "value") else user.Role
    claims: Dict[str, Any] = {
        "sub": user.NIP,
        "ID": user.ID,
        "NIP": user.NIP,
        "Role": role,
        "NamaLengkap": user.NamaLengkap,
        "Email": user.Email,
        "NoTelepon": user.NoTelepon,
        "DinasID": user.DinasID,
    }
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data=claims, expires_delta=access_token_expires
    )
    token = schemas.Token(access_token=access_token)
    return schemas.SuccessResponse[schemas.Token](data=token)

@router.get("/auth/verify", response_model=schemas.SuccessResponse[schemas.TokenVerifyData])
def verify_token(authorization: str | None = Header(default=None), check_user: bool = False, db: Session = Depends(get_db)) -> schemas.SuccessResponse[schemas.TokenVerifyData]:
    if not authorization:
        data = schemas.TokenVerifyData(valid=False, reason="Authorization header tidak ada")
        return schemas.SuccessResponse[schemas.TokenVerifyData](data=data)
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        data = schemas.TokenVerifyData(valid=False, reason="Format Authorization harus Bearer <token>")
        return schemas.SuccessResponse[schemas.TokenVerifyData](data=data)
    token = parts[1]
    from jose import jwt, JWTError
    from config import get_settings
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        claims = schemas.TokenClaims(**payload)
        # optional DB check
        if check_user:
            from model.models import User
            _exists = db.query(User).filter(User.NIP == claims.sub).first()
            if not _exists:
                data = schemas.TokenVerifyData(valid=False, claims=claims, reason="user_not_found_in_db")
                return schemas.SuccessResponse[schemas.TokenVerifyData](data=data)
        data = schemas.TokenVerifyData(valid=True, claims=claims)
        return schemas.SuccessResponse[schemas.TokenVerifyData](data=data)
    except JWTError as e:
        data = schemas.TokenVerifyData(valid=False, reason=str(e))
        return schemas.SuccessResponse[schemas.TokenVerifyData](data=data)

@router.post("/token")
def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="NIP atau password salah")
    role = user.Role.value if hasattr(user.Role, "value") else user.Role
    claims: Dict[str, Any] = {
        "sub": user.NIP,
        "ID": user.ID,
        "NIP": user.NIP,
        "Role": role,
        "NamaLengkap": user.NamaLengkap,
        "Email": user.Email,
        "NoTelepon": user.NoTelepon,
        "DinasID": user.DinasID,
    }
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data=claims, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
