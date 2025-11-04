from __future__ import annotations
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from fastapi import HTTPException
import model.models as models
import controller.auth as auth
import schemas.schemas as schemas
import logging

logger = logging.getLogger(__name__)

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
       
        # Generate OTP verifikasi dan kirim email
        try:
            from utils.otp import create_account_verification_code 
            from utils.mailer import send_registration_otp, MailSendError  
            
            logger.info(f"Creating OTP verification code for user {user.ID}")
            otp_rec = create_account_verification_code(db, user)  
            otp_code = getattr(otp_rec, "KodeUnik", None)
            
            if otp_code:
                setattr(user, "_registration_otp", otp_code)
                logger.info(f"OTP code generated: {otp_code}")
                
                # Kirim email OTP (abaikan error agar tidak blok registrasi)
                try:
                    logger.info(f"Attempting to send OTP email to {user.Email}")
                    send_registration_otp(str(user.Email), str(otp_code))
                    logger.info(f"OTP email sent successfully to {user.Email}")
                except MailSendError as e:
                    logger.warning(f"Failed to send OTP email to {user.Email}: {e}")
                    # Tidak raise error, biarkan user tetap terdaftar
                except Exception as e:
                    logger.error(f"Unexpected error sending OTP email: {e}", exc_info=True)
        except Exception as e:
            # Jangan gagal total jika OTP gagal dibuat
            logger.error(f"Failed to create OTP for user {user.ID}: {e}", exc_info=True)
        
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

    @staticmethod
    def get_user_count_by_dinas(db: Session) -> List[Dict[str, Any]]:
     
        query = (
            db.query(
                models.User.DinasID.label("dinas_id"),
                models.Dinas.Nama.label("dinas_nama"),
                func.count(models.User.ID).label("total_users")
            )
            .outerjoin(models.Dinas, models.User.DinasID == models.Dinas.ID)
            .group_by(models.User.DinasID, models.Dinas.Nama)
            .order_by(func.count(models.User.ID).desc())  # Sort by total users descending
        )
        
        results = query.all()
        
        user_counts: List[Dict[str, Any]] = []
        for row in results:
            count_data: Dict[str, Any] = {
                "dinas_id": row.dinas_id,
                "dinas_nama": row.dinas_nama if row.dinas_nama else "Tidak Ada Dinas",
                "total_users": row.total_users
            }
            user_counts.append(count_data)
        
        return user_counts

    @staticmethod
    def search_users_detailed(
        db: Session,
        search: str | None = None,
        role: str | None = None,
        dinas_id: int | None = None,
        is_verified: bool | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Mencari user dengan detail lengkap (wallet, dinas, submission count)
        """
        from sqlalchemy import or_, func as sql_func
        
        # Base query
        query = db.query(models.User)
        
        # Apply search filter (search by NIP, Name, or Email)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    models.User.NIP.ilike(search_pattern),
                    models.User.NamaLengkap.ilike(search_pattern),
                    models.User.Email.ilike(search_pattern)
                )
            )
        
        # Apply role filter
        if role:
            try:
                role_enum = models.RoleEnum[role]
                query = query.filter(models.User.Role == role_enum)
            except KeyError:
                pass  # Invalid role, ignore
        
        # Apply dinas filter
        if dinas_id is not None:
            query = query.filter(models.User.DinasID == dinas_id)
        
        # Apply verification filter
        if is_verified is not None:
            query = query.filter(models.User.isVerified == is_verified)
        
        # Order by ID and apply pagination
        query = query.order_by(models.User.ID.desc())
        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        users = query.all()
        
        # Build detailed response
        detailed_users: List[Dict[str, Any]] = []
        for user in users:
            # Get wallet info
            wallet = db.query(models.Wallet).filter(models.Wallet.UserID == user.ID).first()
            wallet_type_name = None
            if wallet:
                wallet_type = db.query(models.WalletType).filter(
                    models.WalletType.ID == wallet.WalletTypeID
                ).first()
                wallet_type_name = wallet_type.Nama if wallet_type else None
            
            # Get dinas name
            dinas_name = None
            if user.DinasID is not None:  # type: ignore
                dinas = db.query(models.Dinas).filter(models.Dinas.ID == user.DinasID).first()
                dinas_name = dinas.Nama if dinas else None
            
            # Count submissions
            submissions_created = db.query(sql_func.count(models.Submission.ID)).filter(
                models.Submission.CreatorID == user.ID
            ).scalar() or 0
            
            submissions_received = db.query(sql_func.count(models.Submission.ID)).filter(
                models.Submission.ReceiverID == user.ID
            ).scalar() or 0
            
            user_detail: Dict[str, Any] = {
                "ID": user.ID,
                "NIP": user.NIP,
                "NamaLengkap": user.NamaLengkap,
                "Email": user.Email,
                "NoTelepon": user.NoTelepon,
                "Role": user.Role.value,
                "isVerified": user.isVerified,
                "DinasID": user.DinasID,
                "DinasNama": dinas_name,
                "WalletID": wallet.ID if wallet else None,
                "WalletSaldo": float(wallet.Saldo) if wallet else None,  # type: ignore
                "WalletType": wallet_type_name,
                "TotalSubmissionsCreated": submissions_created,
                "TotalSubmissionsReceived": submissions_received,
            }
            detailed_users.append(user_detail)
        
        return detailed_users
    
    @staticmethod
    def count_users(
        db: Session,
        search: str | None = None,
        role: str | None = None,
        dinas_id: int | None = None,
        is_verified: bool | None = None
    ) -> int:
        """
        Menghitung total user berdasarkan filter
        """
        from sqlalchemy import or_
        
        query = db.query(models.User)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    models.User.NIP.ilike(search_pattern),
                    models.User.NamaLengkap.ilike(search_pattern),
                    models.User.Email.ilike(search_pattern)
                )
            )
        
        if role:
            try:
                role_enum = models.RoleEnum[role]
                query = query.filter(models.User.Role == role_enum)
            except KeyError:
                pass
        
        if dinas_id is not None:
            query = query.filter(models.User.DinasID == dinas_id)
        
        if is_verified is not None:
            query = query.filter(models.User.isVerified == is_verified)
        
        return query.count()
    
    @staticmethod
    def get_user_balance(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Mendapatkan saldo wallet user beserta informasi user
        """
        # Get user
        user = db.query(models.User).filter(models.User.ID == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")
        
        # Get wallet
        wallet = db.query(models.Wallet).filter(models.Wallet.UserID == user_id).first()
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet tidak ditemukan untuk user ini")
        
        # Get wallet type
        wallet_type = db.query(models.WalletType).filter(
            models.WalletType.ID == wallet.WalletTypeID
        ).first()
        
        # Get dinas name if exists
        dinas_name = None
        if user.DinasID is not None:  # type: ignore
            dinas = db.query(models.Dinas).filter(models.Dinas.ID == user.DinasID).first()
            dinas_name = dinas.Nama if dinas else None
        
        balance_info: Dict[str, Any] = {
            "user_id": user.ID,
            "nip": user.NIP,
            "nama_lengkap": user.NamaLengkap,
            "email": user.Email,
            "role": user.Role.value,
            "dinas_id": user.DinasID,
            "dinas_nama": dinas_name,
            "wallet_id": wallet.ID,
            "saldo": float(wallet.Saldo),  # type: ignore
            "wallet_type_id": wallet.WalletTypeID,
            "wallet_type_nama": wallet_type.Nama if wallet_type else None,
        }
        
        return balance_info
