from fastapi import APIRouter, Depends, HTTPException, Header, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any, Dict
import controller.auth as auth
import schemas.schemas as schemas
from database.database import SessionLocal
from i18n.messages import get_message, normalize_lang
from utils.otp import (
    create_password_reset_code,
    verify_password_reset_code,
    consume_password_reset_code,
    verify_account_verification_code,
    consume_account_verification_code,
    create_account_verification_code,
)
from utils.responses import detect_lang
from model import models
from config import get_settings, Settings

router = APIRouter(tags=["Auth"])

# Settings & typed constants
_settings: Settings = get_settings()
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(_settings.access_token_expire_minutes)

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

@router.post(
    "/login", 
    response_model=schemas.SuccessResponse[schemas.Token],
    summary="Login (Formatted Response)",
    description="Login menggunakan NIP dan Password. Mengembalikan token dalam format standard JSON API response."
)
def login(request: Request, form_data: OAuth2PasswordRequestFormWithLang = Depends(), db: Session = Depends(get_db)) -> schemas.SuccessResponse[schemas.Token]:
    lang = detect_lang(request)
    if lang == "id" and form_data.lang and form_data.lang != "id":  
        lang = normalize_lang(form_data.lang)
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail=get_message("invalid_credentials", lang))
    if not getattr(user, "isVerified", False):
        raise HTTPException(status_code=403, detail="account_not_verified")
    role = user.Role.value if hasattr(user.Role, "value") else user.Role
    role_str = str(role)
    roles_list = [role_str]
    dinas_id = getattr(user, "DinasID", None)
    dinas_rel = getattr(user, "dinas", None)
    dinas_name = getattr(dinas_rel, "Nama", None) if dinas_rel is not None else None
    dinas_obj: Dict[str, Any] | None = {"DinasID": dinas_id, "Nama": dinas_name} if dinas_id is not None else None
    claims: Dict[str, Any] = {
        "sub": user.NIP,
        "ID": user.ID,
        "NIP": user.NIP,
        "Role": roles_list,
        "NamaLengkap": user.NamaLengkap,
        "Email": user.Email,
        "NoTelepon": user.NoTelepon,
        "DinasID": dinas_id,
        "Dinas": dinas_obj,
        "isVerified": getattr(user, "isVerified", None),
        "Lang": lang,
    }
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data=claims, expires_delta=access_token_expires)
    token = schemas.Token(access_token=access_token)
    return schemas.SuccessResponse[schemas.Token](data=token, message=get_message("login_success", lang))

@router.get(
    "/auth/verify", 
    response_model=schemas.SuccessResponse[schemas.TokenVerifyData],
    summary="Verify Token",
    description="Memverifikasi apakah token JWT valid dan belum expired."
)
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
    try:
        payload = jwt.decode(token, _settings.secret_key, algorithms=["HS256"])
        claims = schemas.TokenClaims(**payload)
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

@router.post(
    "/token", 
    summary="OAuth2 Login",
    description="Endpoint standar OAuth2 untuk Swagger UI. Mengembalikan access token langsung."
)
def token(request: Request, form_data: OAuth2PasswordRequestFormWithLang = Depends(), db: Session = Depends(get_db)):
    lang = detect_lang(request)
    if lang == "id" and form_data.lang and form_data.lang != "id":
        lang = normalize_lang(form_data.lang)
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail=get_message("invalid_credentials", lang))
    if not getattr(user, "isVerified", False):
        raise HTTPException(status_code=403, detail="account_not_verified")
    role = user.Role.value if hasattr(user.Role, "value") else user.Role
    role_str = str(role)
    roles_list = [role_str]
    dinas_id = getattr(user, "DinasID", None)
    dinas_rel = getattr(user, "dinas", None)
    dinas_name = getattr(dinas_rel, "Nama", None) if dinas_rel is not None else None
    dinas_obj: Dict[str, Any] | None = {"DinasID": dinas_id, "Nama": dinas_name} if dinas_id is not None else None
    claims: Dict[str, Any] = {
        "sub": user.NIP,
        "ID": user.ID,
        "NIP": user.NIP,
        "Role": roles_list,
        "NamaLengkap": user.NamaLengkap,
        "Email": user.Email,
        "NoTelepon": user.NoTelepon,
        "DinasID": dinas_id,
        "Dinas": dinas_obj,
        "isVerified": getattr(user, "isVerified", None),
        "Lang": lang,
    }
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data=claims, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post(
    "/auth/forgot-password", 
    response_model=schemas.SuccessResponse[schemas.Message],
    summary="Forgot Password",
    description="Meminta kode OTP reset password ke email."
)
def forgot_password(payload: schemas.ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    lang = detect_lang(request)
    user = db.query(models.User).filter(models.User.Email == payload.email).first()
    if user:
        create_password_reset_code(db, user)
        # TODO: kirim email logic
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="ok"), message=get_message("otp_sent", lang))

@router.post(
    "/auth/verify-otp", 
    response_model=schemas.SuccessResponse[schemas.OTPVerifyResponse],
    summary="Verify Reset OTP",
    description="Memverifikasi kode OTP untuk reset password."
)
def verify_otp(payload: schemas.VerifyOTPRequest, request: Request, db: Session = Depends(get_db)):
    lang = detect_lang(request)
    user = db.query(models.User).filter(models.User.Email == payload.email).first()
    if not user:
        return schemas.SuccessResponse[schemas.OTPVerifyResponse](data=schemas.OTPVerifyResponse(valid=False, reason="invalid"), message=get_message("otp_invalid", lang))
    ok, reason = verify_password_reset_code(db, user, payload.otp)
    if not ok:
        key = "otp_invalid" if reason == "invalid" else "otp_expired"
        return schemas.SuccessResponse[schemas.OTPVerifyResponse](data=schemas.OTPVerifyResponse(valid=False, reason=reason), message=get_message(key, lang))
    return schemas.SuccessResponse[schemas.OTPVerifyResponse](data=schemas.OTPVerifyResponse(valid=True), message=get_message("otp_sent", lang))

@router.post(
    "/auth/reset-password", 
    response_model=schemas.SuccessResponse[schemas.Message],
    summary="Reset Password",
    description="Mengubah password menggunakan kode OTP yang valid."
)
def reset_password(payload: schemas.ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    lang = detect_lang(request)
    user = db.query(models.User).filter(models.User.Email == payload.email).first()
    if not user:
        return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="ignored"), message=get_message("otp_invalid", lang))
    ok, reason = verify_password_reset_code(db, user, payload.otp)
    if not ok:
        key = "otp_invalid" if reason == "invalid" else "otp_expired"
        return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail=reason or "invalid"), message=get_message(key, lang))
    setattr(user, "Password", auth.get_password_hash(payload.new_password))
    db.add(user)
    consume_password_reset_code(db, user, payload.otp)
    db.commit()
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="done"), message=get_message("password_reset_success", lang))

class RegisterVerifyRequest(schemas.BaseModel): 
    email: str
    otp: str

@router.post(
    "/auth/verify-register", 
    response_model=schemas.SuccessResponse[schemas.OTPVerifyResponse],
    summary="Verify Registration OTP",
    description="Memverifikasi akun baru dengan kode OTP yang dikirim via email."
)
def verify_register(payload: RegisterVerifyRequest, request: Request, db: Session = Depends(get_db)):
    lang = detect_lang(request)
    user = db.query(models.User).filter(models.User.Email == payload.email).first()
    if not user:
        return schemas.SuccessResponse[schemas.OTPVerifyResponse](data=schemas.OTPVerifyResponse(valid=False, reason="invalid"), message=get_message("otp_invalid", lang))
    ok, reason = verify_account_verification_code(db, user, payload.otp)
    if not ok:
        key = "otp_invalid" if reason == "invalid" else "otp_expired"
        return schemas.SuccessResponse[schemas.OTPVerifyResponse](data=schemas.OTPVerifyResponse(valid=False, reason=reason), message=get_message(key, lang))
    setattr(user, "isVerified", True)
    db.add(user)
    consume_account_verification_code(db, user, payload.otp)
    db.commit()
    return schemas.SuccessResponse[schemas.OTPVerifyResponse](data=schemas.OTPVerifyResponse(valid=True), message="account_verified")

class ResendRegisterOTPRequest(schemas.BaseModel):
    email: str

@router.post(
    "/auth/resend-register-otp", 
    response_model=schemas.SuccessResponse[schemas.Message],
    summary="Resend Registration OTP",
    description="Mengirim ulang kode OTP verifikasi akun."
)
def resend_register_otp(payload: ResendRegisterOTPRequest, request: Request, db: Session = Depends(get_db)):
    lang = detect_lang(request)
    user = db.query(models.User).filter(models.User.Email == payload.email).first()
    if not user:
        return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="ok"), message=get_message("otp_sent", lang))
    if getattr(user, "isVerified", False):
        return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="already_verified"), message="already_verified")
    rec = create_account_verification_code(db, user)
    from config import get_settings
    settings = get_settings()
    msg = get_message("otp_sent", lang)
    if settings.debug:
        msg = f"{msg} | OTP={rec.KodeUnik}"
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="resent"), message=msg)

@router.post(
    "/auth/refresh-token", 
    response_model=schemas.SuccessResponse[schemas.Token],
    summary="Refresh Token",
    description="Memperbarui token yang sudah ada untuk memperpanjang sesi."
)
def refresh_token(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
) -> schemas.SuccessResponse[schemas.Token]:
    lang = detect_lang(request)
    user = db.query(models.User).filter(models.User.ID == current_user.ID).first()
    if not user:
        raise HTTPException(status_code=404, detail=get_message("user_not_found", lang))
    if not getattr(user, "isVerified", False):
        raise HTTPException(status_code=403, detail="account_not_verified")
    
    role = user.Role.value if hasattr(user.Role, "value") else user.Role
    role_str = str(role)
    roles_list = [role_str]
    dinas_id = getattr(user, "DinasID", None)
    dinas_rel = getattr(user, "dinas", None)
    dinas_name = getattr(dinas_rel, "Nama", None) if dinas_rel is not None else None
    dinas_obj: Dict[str, Any] | None = {"DinasID": dinas_id, "Nama": dinas_name} if dinas_id is not None else None
    
    claims: Dict[str, Any] = {
        "sub": user.NIP,
        "ID": user.ID,
        "NIP": user.NIP,
        "Role": roles_list,
        "NamaLengkap": user.NamaLengkap,
        "Email": user.Email,
        "NoTelepon": user.NoTelepon,
        "DinasID": dinas_id,
        "Dinas": dinas_obj,
        "isVerified": getattr(user, "isVerified", None),
        "Lang": lang,
    }
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data=claims, expires_delta=access_token_expires)
    token = schemas.Token(access_token=access_token)
    return schemas.SuccessResponse[schemas.Token](
        data=token, 
        message=get_message("token_refresh_success", lang)
    )

@router.post(
    "/auth/change-password", 
    response_model=schemas.SuccessResponse[schemas.Message],
    summary="Change Password",
    description="Mengganti password user yang sedang login."
)
def change_password(
    payload: schemas.ChangePasswordRequest,
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    lang = detect_lang(request)
    user = db.query(models.User).filter(models.User.ID == current_user.ID).first()
    if not user:
        raise HTTPException(status_code=404, detail=get_message("user_not_found", lang))
    
    hashed_password = getattr(user, "Password", None)
    if not hashed_password:
        raise HTTPException(status_code=500, detail=get_message("internal_error", lang))
    
    if not auth.verify_password(payload.old_password, hashed_password):
        raise HTTPException(status_code=400, detail=get_message("old_password_incorrect", lang))
    
    if auth.verify_password(payload.new_password, hashed_password):
        raise HTTPException(status_code=400, detail=get_message("new_password_same_as_old", lang))
    
    new_hashed_password = auth.get_password_hash(payload.new_password) 
    setattr(user, "Password", new_hashed_password)
    db.add(user)
    db.commit()
    
    return schemas.SuccessResponse[schemas.Message](
        data=schemas.Message(detail="password_changed"),
        message=get_message("password_change_success", lang)
    )