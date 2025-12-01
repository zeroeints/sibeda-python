from __future__ import annotations
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session, joinedload
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
        # (Isi create tetap sama seperti sebelumnya, tidak ada perubahan logic)
        nip = user_in.NIP.strip()
        nama = user_in.NamaLengkap.strip()
        email = user_in.Email.strip().lower()
        no_telp = user_in.NoTelepon.strip() if user_in.NoTelepon else None
        user = models.User(
            NIP=nip, Role=models.RoleEnum.pic, NamaLengkap=nama, Email=email,
            NoTelepon=no_telp, Password=auth.get_password_hash(user_in.Password),
            DinasID=None, isVerified=False,
        )
        db.add(user)
        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            msg = str(e.orig).lower() if getattr(e, 'orig', None) else ''
            if 'duplicate' in msg or 'uq_user_nip' in msg: detail = "NIP atau Email sudah terdaftar"
            else: detail = "Gagal membuat user"
            raise HTTPException(status_code=400, detail=detail)
        db.refresh(user)
        
        # Trigger OTP logic (tetap sama)
        try:
            from utils.otp import create_account_verification_code 
            from utils.mailer import send_registration_otp
            otp_rec = create_account_verification_code(db, user)  
            if otp_rec and otp_rec.KodeUnik:
                send_registration_otp(str(user.Email), str(otp_rec.KodeUnik))
        except Exception as e:
            logger.error(f"OTP Error: {e}")
            
        return user

    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
        """List users dengan eager loading Dinas"""
        q = db.query(models.User).options(joinedload(models.User.dinas))
        
        total_records = q.count()
        data = q.order_by(models.User.ID.desc()).offset(skip).limit(limit).all()
        has_more = (skip + len(data)) < total_records
        
        # Stats: Verified vs Not
        stat_dict = {"total_data": total_records}
        stats_ver = db.query(models.User.isVerified, func.count(models.User.ID)).group_by(models.User.isVerified).all()
        
        stat_dict["total_verified"] = 0
        stat_dict["total_unverified"] = 0
        for is_ver, count in stats_ver:
            if is_ver: stat_dict["total_verified"] = count
            else: stat_dict["total_unverified"] = count
            
        return {
            "list": data,
            "limit": limit,
            "offset": skip,
            "has_more": has_more,
            "month": None, "year": None, "stat": stat_dict
        }
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> models.User | None:
        """Get Single User dengan Relasi"""
        return db.query(models.User).options(
            joinedload(models.User.dinas)
        ).filter(models.User.ID == user_id).first()
    
    @staticmethod
    def update(db: Session, user_id: int, user_update: schemas.UserUpdate) -> models.User:
        # (Isi update tetap sama)
        user = db.query(models.User).filter(models.User.ID == user_id).first()
        if not user: raise HTTPException(404, "User tidak ditemukan")
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                if field == "Password": value = auth.get_password_hash(value)
                setattr(user, field, value)
        try:
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            raise HTTPException(400, "Data konflik (NIP/Email sudah ada)")
        return UserService.get_by_id(db, user.ID)

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
    def get_user_detail_complete(db: Session, user_id: int) -> Dict[str, Any] | None:
        """
        Get detail lengkap satu user (untuk endpoint /{id}).
        Menggunakan logic yang sama dengan search_detailed tapi untuk 1 ID.
        """
        results = UserService.search_users_detailed(db, user_id_filter=user_id, limit=1)
        return results[0] if results else None

    # --- SEARCH OPTIMIZATION (Fix N+1) ---
    @staticmethod
    def search_users_detailed(
        db: Session,
        search: str | None = None,
        role: str | None = None,
        dinas_id: int | None = None,
        is_verified: bool | None = None,
        user_id_filter: int | None = None, # New param for single get
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Mencari user dengan detail lengkap dalam 1 Query Utama.
        """
        # Subquery untuk menghitung submission created
        sub_created = db.query(
            models.Submission.CreatorID, 
            func.count(models.Submission.ID).label("total_created")
        ).group_by(models.Submission.CreatorID).subquery()

        # Subquery untuk menghitung submission received
        sub_received = db.query(
            models.Submission.ReceiverID, 
            func.count(models.Submission.ID).label("total_received")
        ).group_by(models.Submission.ReceiverID).subquery()

        # Main Query
        query = db.query(
            models.User,
            models.Dinas,
            models.Wallet,
            models.WalletType.Nama.label("wallet_type_name"),
            func.coalesce(sub_created.c.total_created, 0).label("created_count"),
            func.coalesce(sub_received.c.total_received, 0).label("received_count")
        ).outerjoin(
            models.Dinas, models.User.DinasID == models.Dinas.ID
        ).outerjoin(
            models.Wallet, models.User.ID == models.Wallet.UserID
        ).outerjoin(
            models.WalletType, models.Wallet.WalletTypeID == models.WalletType.ID
        ).outerjoin(
            sub_created, models.User.ID == sub_created.c.CreatorID
        ).outerjoin(
            sub_received, models.User.ID == sub_received.c.ReceiverID
        )

        # Filters
        if user_id_filter:
            query = query.filter(models.User.ID == user_id_filter)
        
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
            # Handle enum filtering safely
            try:
                role_enum = models.RoleEnum(role) # Strict check
                query = query.filter(models.User.Role == role_enum)
            except ValueError:
                pass # Or raise error if strict
        
        if dinas_id is not None:
            query = query.filter(models.User.DinasID == dinas_id)
        
        if is_verified is not None:
            query = query.filter(models.User.isVerified == is_verified)
        
        # Pagination
        query = query.order_by(models.User.ID.desc())
        results = query.offset(offset).limit(limit).all()
        
        # Mapping Result
        mapped_results = []
        for user, dinas, wallet, w_type, created_count, received_count in results:
            # Construct Dictionary sesuai UserDetailResponse
            # Note: Pydantic will handle `Dinas` nested object from `dinas` param if passed correctly,
            # but here we are constructing flat dict mostly.
            
            user_dict = {
                "ID": user.ID,
                "NIP": user.NIP,
                "NamaLengkap": user.NamaLengkap,
                "Email": user.Email,
                "NoTelepon": user.NoTelepon,
                "Role": user.Role,
                "isVerified": user.isVerified,
                "DinasID": user.DinasID,
                "Dinas": dinas, # Object Dinas untuk nested schema
                
                # Extra fields for UserDetailResponse
                "DinasNama": dinas.Nama if dinas else None,
                "WalletID": wallet.ID if wallet else None,
                "WalletSaldo": float(wallet.Saldo) if wallet else None,
                "WalletType": w_type,
                "TotalSubmissionsCreated": created_count,
                "TotalSubmissionsReceived": received_count
            }
            mapped_results.append(user_dict)
            
        return mapped_results
    
    @staticmethod
    def count_users(db: Session, search=None, role=None, dinas_id=None, is_verified=None):
        q = db.query(models.User)
        # Apply same filters as above (simplified for brevity)
        if search:
            pat = f"%{search}%"
            q = q.filter(or_(models.User.NIP.ilike(pat), models.User.NamaLengkap.ilike(pat), models.User.Email.ilike(pat)))
        if role:
             try: q = q.filter(models.User.Role == models.RoleEnum(role))
             except: pass
        if dinas_id: q = q.filter(models.User.DinasID == dinas_id)
        if is_verified is not None: q = q.filter(models.User.isVerified == is_verified)
        return q.count()
    
    @staticmethod
    def get_user_balance(db: Session, user_id: int) -> Dict[str, Any]:
        user = db.query(models.User).filter(models.User.ID == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")
        
        wallet = db.query(models.Wallet).filter(models.Wallet.UserID == user_id).first()
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet tidak ditemukan")
        
        # Pydantic akan meng-convert SQLAlchemy object 'user' menjadi UserSimpleResponse
        return {
            "User": user, 
            "DinasNama": user.dinas.Nama if user.dinas else None,
            "WalletID": wallet.ID,
            "Saldo": float(wallet.Saldo),
            "WalletType": wallet.wallet_type.Nama if wallet.wallet_type else None
        }