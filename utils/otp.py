from __future__ import annotations
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from model.models import UniqueCodeGenerator, PurposeEnum, User

OTP_LENGTH = 6
OTP_EXP_MINUTES = 10

def generate_otp(length: int = OTP_LENGTH) -> str:
    return ''.join(random.choice('0123456789') for _ in range(length))

def create_password_reset_code(db: Session, user: User) -> UniqueCodeGenerator:
    # hapus kode lama purpose password_reset (opsional agar hanya satu aktif)
    db.query(UniqueCodeGenerator).filter(
        UniqueCodeGenerator.UserID == user.ID,
        UniqueCodeGenerator.Purpose == PurposeEnum.password_reset
    ).delete()
    otp = generate_otp()
    rec = UniqueCodeGenerator(
        UserID=user.ID,
        KodeUnik=otp,
        Purpose=PurposeEnum.password_reset,
        expired_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXP_MINUTES),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

def verify_password_reset_code(db: Session, user: User, otp: str):
    rec = db.query(UniqueCodeGenerator).filter(
        UniqueCodeGenerator.UserID == user.ID,
        UniqueCodeGenerator.Purpose == PurposeEnum.password_reset,
        UniqueCodeGenerator.KodeUnik == otp,
    ).first()
    if not rec:
        return False, "invalid"
    # Pylance mungkin menganggap expired_at sebagai ColumnElement, jadi amankan dengan isinstance
    now = datetime.now(timezone.utc)
    exp_val = getattr(rec, "expired_at", None)
    if isinstance(exp_val, datetime):
        if exp_val < now:
            return False, "expired"
    else:
        
        return False, "expired"
    return True, None

def consume_password_reset_code(db: Session, user: User, otp: str):
    db.query(UniqueCodeGenerator).filter(
        UniqueCodeGenerator.UserID == user.ID,
        UniqueCodeGenerator.Purpose == PurposeEnum.password_reset,
        UniqueCodeGenerator.KodeUnik == otp,
    ).delete()
    db.commit()