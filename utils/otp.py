from __future__ import annotations
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from typing import TYPE_CHECKING
from model import models    
from config import get_settings
import hmac, hashlib, base64, json
if TYPE_CHECKING:
    from model.models import User, UniqueCodeGenerator


PurposeEnum = models.PurposeEnum

OTP_LENGTH = 4
OTP_EXP_MINUTES = 2


_SETTINGS = get_settings()
_QR_SECRET: bytes = (_SETTINGS.secret_key or "sibeda-secret").encode("utf-8")

def generate_otp(length: int = OTP_LENGTH) -> str:
    return ''.join(random.choice('0123456789') for _ in range(length))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _to_utc(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware in UTC.
    Many DB backends (e.g., MySQL) may return naive datetimes even when timezone=True.
    We assume stored times are UTC and coerce accordingly.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

# --- QR token encode/decode helpers ---
def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _b64url_decode(data: str) -> bytes:
    pad = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)

def encode_qr_token(user: 'User', code: str) -> str:
    """Encode a QR token containing user id and raw code with HMAC signature.
    Format: base64url(payload).base64url(signature)
    payload: {"uid": int, "code": str, "ts": epoch_sec}
    """
    uid_val = getattr(user, "ID", None)
    payload: dict[str, int | str] = {
        "uid": int(uid_val) if uid_val is not None else 0,
        "code": str(code),
        "ts": int(_utc_now().timestamp()),
    }
    p_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sig = hmac.new(_QR_SECRET, p_bytes, hashlib.sha256).digest()
    return f"{_b64url(p_bytes)}.{_b64url(sig)}"

def decode_qr_token(token: str) -> tuple[bool, str | None, int | None, str | None]:
   
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return False, "format", None, None
        p_bytes = _b64url_decode(parts[0])
        sig = _b64url_decode(parts[1])
        expected = hmac.new(_QR_SECRET, p_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return False, "signature", None, None
        obj = json.loads(p_bytes.decode("utf-8"))
        uid = int(obj.get("uid")) if obj.get("uid") is not None else None
        code = str(obj.get("code")) if obj.get("code") is not None else None
        return True, None, uid, code
    except Exception:
        return False, "json", None, None

def extract_kode_unik_from_qr(qr_input: str) -> str:
  
    
    if "." in qr_input:
        ok, reason, _uid, code = decode_qr_token(qr_input)
        if ok and code:
            return code
        else:
            raise ValueError(f"Token QR tidak valid: {reason}")
    
    return qr_input

def create_password_reset_code(db: Session, user: 'User') -> 'UniqueCodeGenerator':
    db.query(models.UniqueCodeGenerator).filter(
        models.UniqueCodeGenerator.UserID == user.ID,
        models.UniqueCodeGenerator.Purpose == PurposeEnum.password_reset
    ).delete()
    otp = generate_otp()
    rec = models.UniqueCodeGenerator(
        UserID=user.ID,
        KodeUnik=otp,
        Purpose=PurposeEnum.password_reset,
        expired_at=_utc_now() + timedelta(minutes=OTP_EXP_MINUTES),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

def verify_password_reset_code(db: Session, user: 'User', otp: str):
    rec = db.query(models.UniqueCodeGenerator).filter(
        models.UniqueCodeGenerator.UserID == user.ID,
        models.UniqueCodeGenerator.Purpose == PurposeEnum.password_reset,
        models.UniqueCodeGenerator.KodeUnik == otp,
    ).first()
    if not rec:
        return False, "invalid"
    now = _utc_now()
    exp_val = getattr(rec, "expired_at", None)
    if isinstance(exp_val, datetime):
        if _to_utc(exp_val) < now:
            return False, "expired"
    else:
        
        return False, "expired"
    return True, None

def consume_password_reset_code(db: Session, user: 'User', otp: str):
    db.query(models.UniqueCodeGenerator).filter(
        models.UniqueCodeGenerator.UserID == user.ID,
        models.UniqueCodeGenerator.Purpose == PurposeEnum.password_reset,
        models.UniqueCodeGenerator.KodeUnik == otp,
    ).delete()
    db.commit()

def create_account_verification_code(db: Session, user: 'User') -> 'UniqueCodeGenerator':
    db.query(models.UniqueCodeGenerator).filter(
        models.UniqueCodeGenerator.UserID == user.ID,
        models.UniqueCodeGenerator.Purpose == PurposeEnum.register
    ).delete()
    otp = generate_otp()
    rec = models.UniqueCodeGenerator(
        UserID=user.ID,
        KodeUnik=otp,
        Purpose=PurposeEnum.register,
        expired_at=_utc_now() + timedelta(minutes=OTP_EXP_MINUTES),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

def verify_account_verification_code(db: Session, user: 'User', otp: str):
    rec = db.query(models.UniqueCodeGenerator).filter(
        models.UniqueCodeGenerator.UserID == user.ID,
        models.UniqueCodeGenerator.Purpose == PurposeEnum.register,
        models.UniqueCodeGenerator.KodeUnik == otp,
    ).first()
    if not rec:
        return False, "invalid"
    now = _utc_now()
    exp_val = getattr(rec, "expired_at", None)
    if isinstance(exp_val, datetime):
        if _to_utc(exp_val) < now:
            return False, "expired"
    else:
        return False, "expired"
    return True, None

def consume_account_verification_code(db: Session, user: 'User', otp: str):
    db.query(models.UniqueCodeGenerator).filter(
        models.UniqueCodeGenerator.UserID == user.ID,
        models.UniqueCodeGenerator.Purpose == PurposeEnum.register,
        models.UniqueCodeGenerator.KodeUnik == otp,
    ).delete()
    db.commit()

# ---------------- QR Code (Purpose: otp) ----------------
def get_or_create_qr_code(db: Session, user: 'User') -> 'UniqueCodeGenerator':
  
    now = _utc_now()
    rec = db.query(models.UniqueCodeGenerator).filter(
        models.UniqueCodeGenerator.UserID == user.ID,
        models.UniqueCodeGenerator.Purpose == PurposeEnum.otp,
    ).order_by(models.UniqueCodeGenerator.ID.desc()).first()
    if rec is not None:
        exp_val = getattr(rec, "expired_at", None)
        if isinstance(exp_val, datetime) and _to_utc(exp_val) > now:
            return rec
    # else create new
    new_rec = models.UniqueCodeGenerator(
        UserID=user.ID,
        KodeUnik=generate_otp(),
        Purpose=PurposeEnum.otp,
        expired_at=now + timedelta(minutes=OTP_EXP_MINUTES),
    )
    db.add(new_rec)
    db.commit()
    db.refresh(new_rec)
    return new_rec

def verify_qr_code(db: Session, user: 'User', code: str):
    rec = db.query(models.UniqueCodeGenerator).filter(
        models.UniqueCodeGenerator.UserID == user.ID,
        models.UniqueCodeGenerator.Purpose == PurposeEnum.otp,
        models.UniqueCodeGenerator.KodeUnik == code,
    ).first()
    if not rec:
        return False, "invalid"
    if isinstance(rec.expired_at, datetime):
        if _to_utc(rec.expired_at) < _utc_now():
            return False, "expired"
    else:
        return False, "expired"
    return True, None

def consume_qr_code(db: Session, user: 'User', code: str) -> None:
    db.query(models.UniqueCodeGenerator).filter(
        models.UniqueCodeGenerator.UserID == user.ID,
        models.UniqueCodeGenerator.Purpose == PurposeEnum.otp,
        models.UniqueCodeGenerator.KodeUnik == code,
    ).delete()
    db.commit()