from fastapi import APIRouter, Depends, HTTPException, Header, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any, Dict
import controller.auth as auth
import schemas.schemas as schemas
from database.database import SessionLocal
from i18n.messages import get_message, normalize_lang
from utils.otp import create_password_reset_code, verify_password_reset_code, consume_password_reset_code
from utils.responses import detect_lang
from model import models

router = APIRouter(tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class OAuth2PasswordRequestFormWithLang(OAuth2PasswordRequestForm):
    def __init__(
        self,
        grant_type: str | None = Form(default=None, regex="password"),
        username: str = Form(...),
        password: str = Form(...),
        scope: str = Form(default=""),
        client_id: str | None = Form(default=None),
        client_secret: str | None = Form(default=None),
        lang: str = Form(default="id"),
    ):
       
        super().__init__(
            grant_type=grant_type,
            username=username,
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
        )
        self.lang = normalize_lang(lang)

@router.post("/login", response_model=schemas.SuccessResponse[schemas.Token])
def login(request: Request, form_data: OAuth2PasswordRequestFormWithLang = Depends(), db: Session = Depends(get_db)) -> schemas.SuccessResponse[schemas.Token]:
    # Deteksi bahasa: path/query/header (middleware) lalu fallback ke form lang bila masih default
    lang = detect_lang(request)
    if lang == "id" and form_data.lang and form_data.lang != "id":  # fallback only if user explicitly set different form lang
        lang = normalize_lang(form_data.lang)
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail=get_message("invalid_credentials", lang))
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
        "Lang": lang,
    }
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data=claims, expires_delta=access_token_expires)
    token = schemas.Token(access_token=access_token)
    return schemas.SuccessResponse[schemas.Token](data=token, message=get_message("login_success", lang))

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
def token(request: Request, form_data: OAuth2PasswordRequestFormWithLang = Depends(), db: Session = Depends(get_db)):
    lang = detect_lang(request)
    if lang == "id" and form_data.lang and form_data.lang != "id":
        lang = normalize_lang(form_data.lang)
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail=get_message("invalid_credentials", lang))
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
        "Lang": lang,
    }
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data=claims, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


# ---------------- OTP / Forgot Password Flow ----------------
@router.post("/auth/forgot-password", response_model=schemas.SuccessResponse[schemas.Message])
def forgot_password(payload: schemas.ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    lang = detect_lang(request)
    user = db.query(models.User).filter(models.User.Email == payload.email).first()
    if user:
        create_password_reset_code(db, user)
        # TODO: kirim email di masa depan
    # selalu success agar tidak bocorkan apakah email ada
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="ok"), message=get_message("otp_sent", lang))

@router.post("/auth/verify-otp", response_model=schemas.SuccessResponse[schemas.OTPVerifyResponse])
def verify_otp(payload: schemas.VerifyOTPRequest, request: Request, db: Session = Depends(get_db)):
    lang = detect_lang(request)
    user = db.query(models.User).filter(models.User.Email == payload.email).first()
    if not user:
        # treat as invalid to avoid enumeration
        return schemas.SuccessResponse[schemas.OTPVerifyResponse](data=schemas.OTPVerifyResponse(valid=False, reason="invalid"), message=get_message("otp_invalid", lang))
    ok, reason = verify_password_reset_code(db, user, payload.otp)
    if not ok:
        key = "otp_invalid" if reason == "invalid" else "otp_expired"
        return schemas.SuccessResponse[schemas.OTPVerifyResponse](data=schemas.OTPVerifyResponse(valid=False, reason=reason), message=get_message(key, lang))
    return schemas.SuccessResponse[schemas.OTPVerifyResponse](data=schemas.OTPVerifyResponse(valid=True), message=get_message("otp_sent", lang))

@router.post("/auth/reset-password", response_model=schemas.SuccessResponse[schemas.Message])
def reset_password(payload: schemas.ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    lang = detect_lang(request)
    user = db.query(models.User).filter(models.User.Email == payload.email).first()
    # hindari timing leak: proses sama walau user None
    if not user:
        return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="ignored"), message=get_message("otp_invalid", lang))
    ok, reason = verify_password_reset_code(db, user, payload.otp)
    if not ok:
        key = "otp_invalid" if reason == "invalid" else "otp_expired"
        return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail=reason or "invalid"), message=get_message(key, lang))
    # update password
    setattr(user, "Password", auth.get_password_hash(payload.new_password))
    db.add(user)
    consume_password_reset_code(db, user, payload.otp)
    db.commit()
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="done"), message=get_message("password_reset_success", lang))
