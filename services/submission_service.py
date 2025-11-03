from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import extract
from fastapi import HTTPException
import model.models as models
from model.models import Submission as SubmissionModel
from schemas.schemas import SubmissionCreate, SubmissionUpdate, SubmissionSummary, SubmissionDetailResponse


class SubmissionService:
    @staticmethod
    def list(
        db: Session, 
        creator_id: int | None = None, 
        receiver_id: int | None = None, 
        vehicle_id: int | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int = 0
    ) -> List[SubmissionModel]:
        q = db.query(SubmissionModel)
        if creator_id is not None:
            q = q.filter(SubmissionModel.CreatorID == creator_id)
        if receiver_id is not None:
            q = q.filter(SubmissionModel.ReceiverID == receiver_id)
        if vehicle_id is not None:
            q = q.filter(SubmissionModel.VehicleID == vehicle_id)
        if status is not None:
            q = q.filter(SubmissionModel.Status == status)
        
        q = q.order_by(SubmissionModel.created_at.desc())
        
        if offset > 0:
            q = q.offset(offset)
        if limit is not None:
            q = q.limit(limit)
        
        return q.all()
    
    @staticmethod
    def list_all_detailed(
        db: Session,
        creator_id: int | None = None,
        receiver_id: int | None = None,
        vehicle_id: int | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int = 0
    ) -> List[SubmissionDetailResponse]:
        """
        Mendapatkan semua submission dengan detail lengkap (nama creator, receiver, vehicle)
        """
        q = db.query(
            SubmissionModel.ID,
            SubmissionModel.KodeUnik,
            SubmissionModel.CreatorID,
            models.User.NamaLengkap.label('CreatorName'),
            SubmissionModel.ReceiverID,
            SubmissionModel.TotalCashAdvance,
            SubmissionModel.VehicleID,
            models.Vehicle.Nama.label('VehicleName'),
            models.Vehicle.Plat.label('VehiclePlat'),
            SubmissionModel.Status,
            SubmissionModel.created_at
        ).join(
            models.User, SubmissionModel.CreatorID == models.User.ID
        ).join(
            models.Vehicle, SubmissionModel.VehicleID == models.Vehicle.ID
        )
        
        # Apply filters
        if creator_id is not None:
            q = q.filter(SubmissionModel.CreatorID == creator_id)
        if receiver_id is not None:
            q = q.filter(SubmissionModel.ReceiverID == receiver_id)
        if vehicle_id is not None:
            q = q.filter(SubmissionModel.VehicleID == vehicle_id)
        if status is not None:
            q = q.filter(SubmissionModel.Status == status)
        
        # Order by created_at desc
        q = q.order_by(SubmissionModel.created_at.desc())
        
        # Pagination
        if offset > 0:
            q = q.offset(offset)
        if limit is not None:
            q = q.limit(limit)
        
        submissions = q.all()
        
        # Build detailed response
        details: List[SubmissionDetailResponse] = []
        for sub in submissions:
            receiver = db.query(models.User).filter(models.User.ID == sub.ReceiverID).first()
            receiver_name = str(receiver.NamaLengkap) if receiver else "Unknown"
            details.append(SubmissionDetailResponse(
                ID=sub.ID,
                KodeUnik=sub.KodeUnik,
                CreatorID=sub.CreatorID,
                CreatorName=sub.CreatorName,
                ReceiverID=sub.ReceiverID,
                ReceiverName=receiver_name,
                TotalCashAdvance=float(sub.TotalCashAdvance),
                VehicleID=sub.VehicleID,
                VehicleName=sub.VehicleName,
                VehiclePlat=sub.VehiclePlat,
                Status=sub.Status,
                created_at=sub.created_at
            ))
        
        return details
    
    @staticmethod
    def count_all(
        db: Session,
        creator_id: int | None = None,
        receiver_id: int | None = None,
        vehicle_id: int | None = None,
        status: str | None = None
    ) -> int:
        """
        Menghitung total submission berdasarkan filter
        """
        q = db.query(SubmissionModel)
        if creator_id is not None:
            q = q.filter(SubmissionModel.CreatorID == creator_id)
        if receiver_id is not None:
            q = q.filter(SubmissionModel.ReceiverID == receiver_id)
        if vehicle_id is not None:
            q = q.filter(SubmissionModel.VehicleID == vehicle_id)
        if status is not None:
            q = q.filter(SubmissionModel.Status == status)
        return q.count()

    @staticmethod
    def get(db: Session, submission_id: int) -> Optional[SubmissionModel]:
        return db.query(SubmissionModel).filter(SubmissionModel.ID == submission_id).first()

    @staticmethod
    def create(db: Session, payload: SubmissionCreate) -> SubmissionModel:
        # Basic FK validation
        if not db.query(models.User).filter(models.User.ID == payload.CreatorID).first():
            raise HTTPException(status_code=400, detail="CreatorID tidak ditemukan")
        if not db.query(models.User).filter(models.User.ID == payload.ReceiverID).first():
            raise HTTPException(status_code=400, detail="ReceiverID tidak ditemukan")
        if not db.query(models.Vehicle).filter(models.Vehicle.ID == payload.VehicleID).first():
            raise HTTPException(status_code=400, detail="VehicleID tidak ditemukan")
        # Create model
        # Normalize status to underlying string value; default to Pending if not provided
        status_value = (
            payload.Status.value
            if payload.Status is not None
            else models.SubmissionStatusEnum.Pending.value
        )
        sub = SubmissionModel(
            KodeUnik=payload.KodeUnik,
            CreatorID=payload.CreatorID,
            ReceiverID=payload.ReceiverID,
            TotalCashAdvance=payload.TotalCashAdvance,
            VehicleID=payload.VehicleID,
            Status=status_value,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def update(db: Session, submission_id: int, payload: SubmissionUpdate) -> SubmissionModel:
        s = db.query(SubmissionModel).filter(SubmissionModel.ID == submission_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Submission tidak ditemukan")
        # handle optional changes with FK checks
        if payload.CreatorID is not None and payload.CreatorID != s.CreatorID:
            if not db.query(models.User).filter(models.User.ID == payload.CreatorID).first():
                raise HTTPException(status_code=400, detail="CreatorID tidak ditemukan")
            setattr(s, "CreatorID", payload.CreatorID)
        if payload.ReceiverID is not None and payload.ReceiverID != s.ReceiverID:
            if not db.query(models.User).filter(models.User.ID == payload.ReceiverID).first():
                raise HTTPException(status_code=400, detail="ReceiverID tidak ditemukan")
            setattr(s, "ReceiverID", payload.ReceiverID)
        if payload.VehicleID is not None and payload.VehicleID != s.VehicleID:
            if not db.query(models.Vehicle).filter(models.Vehicle.ID == payload.VehicleID).first():
                raise HTTPException(status_code=400, detail="VehicleID tidak ditemukan")
            setattr(s, "VehicleID", payload.VehicleID)
        # simple mutable fields
        if payload.KodeUnik is not None:
            setattr(s, "KodeUnik", payload.KodeUnik)
        if payload.TotalCashAdvance is not None:
            setattr(s, "TotalCashAdvance", payload.TotalCashAdvance)
        if payload.Status is not None:
            setattr(s, "Status", payload.Status.value)
        db.commit()
        db.refresh(s)
        return s

    @staticmethod
    def delete(db: Session, submission_id: int) -> None:
        s = db.query(SubmissionModel).filter(SubmissionModel.ID == submission_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Submission tidak ditemukan")
        db.delete(s)
        db.commit()

    @staticmethod
    def get_monthly_summary(db: Session, month: int, year: int) -> SubmissionSummary:
        """
        Mendapatkan ringkasan pengajuan untuk bulan dan tahun tertentu
        """
        # Validasi input
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Bulan harus antara 1-12")
        if year < 2000 or year > 2100:
            raise HTTPException(status_code=400, detail="Tahun tidak valid")

        # Query submissions untuk bulan dan tahun tertentu
        submissions = db.query(SubmissionModel).filter(
            extract('month', SubmissionModel.created_at) == month,
            extract('year', SubmissionModel.created_at) == year
        ).all()

        # Hitung statistik
        total_submissions = len(submissions)
        total_pending = sum(1 for s in submissions if s.Status.value == models.SubmissionStatusEnum.Pending.value)
        total_accepted = sum(1 for s in submissions if s.Status.value == models.SubmissionStatusEnum.Accepted.value)
        total_rejected = sum(1 for s in submissions if s.Status.value == models.SubmissionStatusEnum.Rejected.value)
        
        # type: ignore digunakan karena SQLAlchemy Column[Decimal] bisa dikonversi ke float saat runtime
        total_cash_advance = sum(float(s.TotalCashAdvance) for s in submissions)  # type: ignore
        total_cash_advance_accepted = sum(float(s.TotalCashAdvance) for s in submissions if s.Status.value == models.SubmissionStatusEnum.Accepted.value)  # type: ignore
        total_cash_advance_rejected = sum(float(s.TotalCashAdvance) for s in submissions if s.Status.value == models.SubmissionStatusEnum.Rejected.value)  # type: ignore
        total_cash_advance_pending = sum(float(s.TotalCashAdvance) for s in submissions if s.Status.value == models.SubmissionStatusEnum.Pending.value)  # type: ignore

        return SubmissionSummary(
            month=month,
            year=year,
            total_submissions=total_submissions,
            total_pending=total_pending,
            total_accepted=total_accepted,
            total_rejected=total_rejected,
            total_cash_advance=total_cash_advance,
            total_cash_advance_accepted=total_cash_advance_accepted,
            total_cash_advance_rejected=total_cash_advance_rejected,
            total_cash_advance_pending=total_cash_advance_pending
        )

    @staticmethod
    def get_monthly_details(db: Session, month: int, year: int) -> List[SubmissionDetailResponse]:
        """
        Mendapatkan detail lengkap pengajuan untuk bulan dan tahun tertentu
        """
        # Validasi input
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Bulan harus antara 1-12")
        if year < 2000 or year > 2100:
            raise HTTPException(status_code=400, detail="Tahun tidak valid")

        # Query dengan join untuk mendapatkan data lengkap
        submissions = db.query(
            SubmissionModel.ID,
            SubmissionModel.KodeUnik,
            SubmissionModel.CreatorID,
            models.User.NamaLengkap.label('CreatorName'),
            SubmissionModel.ReceiverID,
            models.User.NamaLengkap.label('ReceiverName'),
            SubmissionModel.TotalCashAdvance,
            SubmissionModel.VehicleID,
            models.Vehicle.Nama.label('VehicleName'),
            models.Vehicle.Plat.label('VehiclePlat'),
            SubmissionModel.Status,
            SubmissionModel.created_at
        ).join(
            models.User, SubmissionModel.CreatorID == models.User.ID
        ).join(
            models.Vehicle, SubmissionModel.VehicleID == models.Vehicle.ID
        ).filter(
            extract('month', SubmissionModel.created_at) == month,
            extract('year', SubmissionModel.created_at) == year
        ).order_by(SubmissionModel.created_at.desc()).all()

        # Untuk mendapatkan nama receiver, perlu query terpisah atau subquery
        # Cara sederhana: loop dan ambil receiver name
        details: List[SubmissionDetailResponse] = []
        for sub in submissions:
            receiver = db.query(models.User).filter(models.User.ID == sub.ReceiverID).first()
            receiver_name = str(receiver.NamaLengkap) if receiver else "Unknown"
            details.append(SubmissionDetailResponse(
                ID=sub.ID,
                KodeUnik=sub.KodeUnik,
                CreatorID=sub.CreatorID,
                CreatorName=sub.CreatorName,
                ReceiverID=sub.ReceiverID,
                ReceiverName=receiver_name,
                TotalCashAdvance=float(sub.TotalCashAdvance),
                VehicleID=sub.VehicleID,
                VehicleName=sub.VehicleName,
                VehiclePlat=sub.VehiclePlat,
                Status=sub.Status,
                created_at=sub.created_at
            ))

        return details
