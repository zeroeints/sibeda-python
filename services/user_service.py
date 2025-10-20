from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import model.models as models
import controller.auth as auth
import schemas.schemas as schemas

class UserService:
    @staticmethod
    def create(db: Session, user_in: schemas.UserCreate) -> models.User:
        
        nip = user_in.NIP.strip()
        nama = user_in.NamaLengkap.strip()
        email = user_in.Email.strip().lower()
        no_telp = user_in.NoTelepon.strip() if user_in.NoTelepon else None
        user = models.User(
            NIP=nip,
            Role=models.RoleEnum.pic,
            NamaLengkap=nama,
            Email=email,
            NoTelepon=no_telp,
            Password=auth.get_password_hash(user_in.Password),
            DinasID=None,
            isVerified=False,
        )
        db.add(user)
        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            
            msg = str(e.orig).lower() if getattr(e, 'orig', None) else ''
            if 'duplicate' in msg or 'uq_user_nip' in msg or 'unique' in msg:
                detail = "NIP sudah terdaftar"
            elif 'foreign key' in msg or 'fk' in msg:
                detail = "Relasi Dinas tidak valid"
            else:
                detail = "Gagal membuat user"
            raise HTTPException(status_code=400, detail=detail)
        db.refresh(user)
       
        try:
            from utils.otp import create_account_verification_code 
            from utils.mailer import send_registration_otp, MailSendError  
            otp_rec = create_account_verification_code(db, user)  
            otp_code = getattr(otp_rec, "KodeUnik", None)
            if otp_code:
                setattr(user, "_registration_otp", otp_code)
                
                try:
                    send_registration_otp(str(user.Email), str(otp_code))
                except MailSendError:
                    pass
        except Exception:
           
            pass
        return user

    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 10) -> List[models.User]:
        return db.query(models.User).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> models.User | None:
        
        return db.query(models.User).filter(models.User.ID == user_id).first()
    
    @staticmethod
    def update(db: Session, user_id: int, user_update: schemas.UserUpdate) -> models.User:
       
        # Cari user
        user = db.query(models.User).filter(models.User.ID == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")
        
        # Update field yang tidak None
        update_data = user_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                # Handle password dengan hash
                if field == "Password":
                    value = auth.get_password_hash(value)
                
                # Normalisasi string fields
                if field == "NIP" and isinstance(value, str):
                    value = value.strip()
                elif field == "NamaLengkap" and isinstance(value, str):
                    value = value.strip()
                elif field == "Email" and isinstance(value, str):
                    value = value.strip().lower()
                elif field == "NoTelepon" and isinstance(value, str):
                    value = value.strip()
                
                setattr(user, field, value)
        
        try:
            db.commit()
            db.refresh(user)
        except IntegrityError as e:
            db.rollback()
            msg = str(e.orig).lower() if getattr(e, 'orig', None) else ''
            if 'duplicate' in msg or 'uq_user_nip' in msg or 'unique' in msg:
                detail = "NIP sudah digunakan oleh user lain"
            elif 'foreign key' in msg or 'fk' in msg:
                detail = "DinasID tidak valid"
            else:
                detail = "Gagal update user"
            raise HTTPException(status_code=400, detail=detail)
        
        return user
