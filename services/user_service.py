from __future__ import annotations
from typing import List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, or_
from fastapi import HTTPException
import model.models as models
import controller.auth as auth
import schemas.schemas as schemas
import logging

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def create(db: Session, user_in: schemas.UserCreate) -> models.User:
        nip = user_in.nip.strip()
        nama = user_in.nama_lengkap.strip()
        email = user_in.email.strip().lower()
        no_telp = user_in.no_telepon.strip() if user_in.no_telepon else None
        
        user = models.User(
            nip=nip, 
            role=models.RoleEnum.pic, 
            nama_lengkap=nama, 
            email=email,
            no_telepon=no_telp, 
            password=auth.get_password_hash(user_in.password),
            dinas_id=None, 
            is_verified=False,
        )
        db.add(user)
        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            msg = str(e.orig).lower() if getattr(e, 'orig', None) else ''
            if 'duplicate' in msg or 'uq_users_nip' in msg: 
                detail = "NIP atau Email sudah terdaftar"
            else: 
                detail = "Gagal membuat user"
            raise HTTPException(status_code=400, detail=detail)
        
        db.refresh(user)
        
        try:
            from utils.otp import create_account_verification_code 
            from utils.mailer import send_registration_otp
            otp_rec = create_account_verification_code(db, user)  
            if otp_rec and otp_rec.kode_unik:
                send_registration_otp(str(user.email), str(otp_rec.kode_unik))
        except Exception as e:
            logger.error(f"OTP Error: {e}")
            
        return user

    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 10, dinas_id: int | None = None) -> Dict[str, Any]:
        q = db.query(models.User).options(joinedload(models.User.dinas))
        
        if dinas_id is not None:
            q = q.filter(models.User.dinas_id == dinas_id)
        
        total_records = q.count()
        data = q.order_by(models.User.id.desc()).offset(skip).limit(limit).all()
        has_more = (skip + len(data)) < total_records
        
        # Stats
        stat_dict = {"total_data": total_records}
        stat_q = db.query(models.User.is_verified, func.count(models.User.id))
        
        if dinas_id is not None:
            stat_q = stat_q.filter(models.User.dinas_id == dinas_id)
            
        stats_ver = stat_q.group_by(models.User.is_verified).all()
        
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
        return db.query(models.User).options(
            joinedload(models.User.dinas)
        ).filter(models.User.id == user_id).first()
    
    @staticmethod
    def update(db: Session, user_id: int, user_update: schemas.UserUpdate) -> models.User:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user: 
            raise HTTPException(404, "User tidak ditemukan")
        
        update_data = user_update.model_dump(exclude_unset=True)
        
        # Mapping key schema -> attribute model (sekarang 1:1, kecuali password hash)
        for key, value in update_data.items():
            if value is not None:
                if key == "password":
                    value = auth.get_password_hash(value)
                # Pastikan key ada di model User
                if hasattr(user, key):
                    setattr(user, key, value)

        try:
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            raise HTTPException(400, "Data konflik (NIP/Email sudah ada)")
            
        return UserService.get_by_id(db, user.id) # type: ignore

    @staticmethod
    def get_user_count_by_dinas(db: Session) -> List[Dict[str, Any]]:
        query = (
            db.query(
                models.User.dinas_id.label("dinas_id"),
                models.Dinas.nama.label("dinas_nama"),
                func.count(models.User.id).label("total_users")
            )
            .outerjoin(models.Dinas, models.User.dinas_id == models.Dinas.id)
            .group_by(models.User.dinas_id, models.Dinas.nama)
            .order_by(func.count(models.User.id).desc())
        )
        
        results = query.all()
        return [
            {
                "dinas_id": row.dinas_id,
                "dinas_nama": row.dinas_nama if row.dinas_nama else "Tidak Ada Dinas",
                "total_users": row.total_users
            } 
            for row in results
        ]

    @staticmethod
    def get_user_detail_complete(db: Session, user_id: int) -> Dict[str, Any] | None:
        results = UserService.search_users_detailed(db, user_id_filter=user_id, limit=1)
        return results[0] if results else None

    @staticmethod
    def search_users_detailed(
        db: Session,
        search: str | None = None,
        role: str | None = None,
        dinas_id: int | None = None,
        is_verified: bool | None = None,
        user_id_filter: int | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        
        # Subqueries (gunakan snake_case columns)
        sub_created = db.query(
            models.Submission.creator_id, 
            func.count(models.Submission.id).label("total_created")
        ).group_by(models.Submission.creator_id).subquery()

        sub_received = db.query(
            models.Submission.receiver_id, 
            func.count(models.Submission.id).label("total_received")
        ).group_by(models.Submission.receiver_id).subquery()

        # Main Query
        query = db.query(
            models.User,
            models.Dinas,
            models.Wallet,
            models.WalletType.nama.label("wallet_type_name"),
            func.coalesce(sub_created.c.total_created, 0).label("created_count"),
            func.coalesce(sub_received.c.total_received, 0).label("received_count")
        ).outerjoin(
            models.Dinas, models.User.dinas_id == models.Dinas.id
        ).outerjoin(
            models.Wallet, models.User.id == models.Wallet.user_id
        ).outerjoin(
            models.WalletType, models.Wallet.wallet_type_id == models.WalletType.id
        ).outerjoin(
            sub_created, models.User.id == sub_created.c.creator_id
        ).outerjoin(
            sub_received, models.User.id == sub_received.c.receiver_id
        )

        if user_id_filter:
            query = query.filter(models.User.id == user_id_filter)
        
        if search:
            pat = f"%{search}%"
            query = query.filter(
                or_(
                    models.User.nip.ilike(pat),
                    models.User.nama_lengkap.ilike(pat),
                    models.User.email.ilike(pat)
                )
            )
        
        if role:
            try:
                role_enum = models.RoleEnum(role)
                query = query.filter(models.User.role == role_enum)
            except ValueError:
                pass
        
        if dinas_id is not None:
            query = query.filter(models.User.dinas_id == dinas_id)
        
        if is_verified is not None:
            query = query.filter(models.User.is_verified == is_verified)
        
        query = query.order_by(models.User.id.desc())
        results = query.offset(offset).limit(limit).all()
        
        mapped_results = []
        for user, dinas, wallet, w_type, created_count, received_count in results:
            # Return Dictionary sesuai field Schema (snake_case)
            user_dict = {
                "id": user.id,
                "nip": user.nip,
                "nama_lengkap": user.nama_lengkap,
                "email": user.email,
                "no_telepon": user.no_telepon,
                "role": user.role,
                "is_verified": user.is_verified,
                "dinas_id": user.dinas_id,
                "dinas": dinas,
                
                # Extra fields for Detail Response
                "wallet_id": wallet.id if wallet else None,
                "wallet_saldo": float(wallet.saldo) if wallet else None,
                "wallet_type": w_type,
                "total_submissions_created": created_count,
                "total_submissions_received": received_count
            }
            mapped_results.append(user_dict)
            
        return mapped_results
    
    @staticmethod
    def count_users(db: Session, search=None, role=None, dinas_id=None, is_verified=None):
        q = db.query(models.User)
        if search:
            pat = f"%{search}%"
            q = q.filter(or_(models.User.nip.ilike(pat), models.User.nama_lengkap.ilike(pat), models.User.email.ilike(pat)))
        if role:
             try: q = q.filter(models.User.role == models.RoleEnum(role))
             except: pass
        if dinas_id: q = q.filter(models.User.dinas_id == dinas_id)
        if is_verified is not None: q = q.filter(models.User.is_verified == is_verified)
        return q.count()
    
    @staticmethod
    def get_user_balance(db: Session, user_id: int) -> Dict[str, Any]:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")
        
        wallet = db.query(models.Wallet).filter(models.Wallet.user_id == user_id).first()
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet tidak ditemukan")
        
        # Return snake_case keys match Schema
        return {
            "user": user, 
            "dinas_nama": user.dinas.nama if user.dinas else None,
            "wallet_id": wallet.id,
            "saldo": float(wallet.saldo),
            "wallet_type": wallet.wallet_type.nama if wallet.wallet_type else None
        }
    
    @staticmethod
    def get_by_vehicle_id(db: Session, vehicle_id: int) -> List[models.User]:
        veh = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
        if not veh:
            raise HTTPException(404, "Kendaraan tidak ditemukan")

        return db.query(models.User).join(
            models.user_vehicle_association,
            models.user_vehicle_association.c.user_id == models.User.id
        ).filter(
            models.user_vehicle_association.c.vehicle_id == vehicle_id
        ).options(
            joinedload(models.User.dinas)
        ).all()
    
    @staticmethod
    def assign_vehicle(db: Session, user_id: int, vehicle_id: int) -> None:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")
            
        vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Kendaraan tidak ditemukan")
            
        if vehicle not in user.vehicles:
            user.vehicles.append(vehicle)
            db.commit()

    @staticmethod
    def unassign_vehicle(db: Session, user_id: int, vehicle_id: int) -> None:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")

        vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Kendaraan tidak ditemukan")
            
        if vehicle in user.vehicles:
            user.vehicles.remove(vehicle)
            db.commit()