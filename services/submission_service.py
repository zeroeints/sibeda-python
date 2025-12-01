from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract
from fastapi import HTTPException
import model.models as models
from model.models import Submission as SubmissionModel, SubmissionLog
import schemas.schemas as schemas

class SubmissionService:
    @staticmethod
    def _get_base_query(db: Session):
        """Query helper dengan eager loading untuk response object lengkap"""
        # HAPUS joinedload ke vehicle
        return db.query(SubmissionModel).options(
            joinedload(SubmissionModel.creator),
            joinedload(SubmissionModel.receiver),
            joinedload(SubmissionModel.logs).joinedload(SubmissionLog.updater)
        )

    @staticmethod
    def list(
        db: Session, 
        creator_id: int | None = None, 
        receiver_id: int | None = None, 
        # Vehicle filter dihapus karena tidak ada relasi
        status: str | None = None,
        limit: int | None = None,
        offset: int = 0
    ) -> List[SubmissionModel]:
        q = SubmissionService._get_base_query(db)
        
        if creator_id is not None:
            q = q.filter(SubmissionModel.CreatorID == creator_id)
        if receiver_id is not None:
            q = q.filter(SubmissionModel.ReceiverID == receiver_id)
        if status is not None:
            q = q.filter(SubmissionModel.Status == status)
        
        q = q.order_by(SubmissionModel.created_at.desc())
        
        if offset > 0:
            q = q.offset(offset)
        if limit is not None:
            q = q.limit(limit)
        
        return q.all()
    
    @staticmethod
    def count_all(
        db: Session,
        creator_id: int | None = None,
        receiver_id: int | None = None,
        status: str | None = None
    ) -> int:
        q = db.query(SubmissionModel)
        if creator_id is not None:
            q = q.filter(SubmissionModel.CreatorID == creator_id)
        if receiver_id is not None:
            q = q.filter(SubmissionModel.ReceiverID == receiver_id)
        if status is not None:
            q = q.filter(SubmissionModel.Status == status)
        return q.count()

    @staticmethod
    def get(db: Session, submission_id: int) -> Optional[SubmissionModel]:
        return SubmissionService._get_base_query(db).filter(SubmissionModel.ID == submission_id).first()

    @staticmethod
    def _create_log(db: Session, submission_id: int, status: str, user_id: int | None, notes: str | None):
        log = SubmissionLog(
            SubmissionID=submission_id,
            Status=status,
            UpdatedByUserID=user_id,
            Notes=notes
        )
        db.add(log)

    @staticmethod
    def create(db: Session, payload: schemas.SubmissionCreate) -> SubmissionModel:
        if not db.query(models.User).filter(models.User.ID == payload.CreatorID).first():
            raise HTTPException(status_code=400, detail="CreatorID tidak ditemukan")
        if not db.query(models.User).filter(models.User.ID == payload.ReceiverID).first():
            raise HTTPException(status_code=400, detail="ReceiverID tidak ditemukan")
        
        status_value = (
            payload.Status.value if payload.Status is not None 
            else models.SubmissionStatusEnum.Pending.value
        )
        
        # VehicleID dihapus dari constructor
        sub = SubmissionModel(
            KodeUnik=payload.KodeUnik,
            CreatorID=payload.CreatorID,
            ReceiverID=payload.ReceiverID,
            TotalCashAdvance=payload.TotalCashAdvance,
            Status=status_value,
        )
        db.add(sub)
        db.flush() 

        SubmissionService._create_log(db, sub.ID, status_value, payload.CreatorID, "Submission dibuat")

        db.commit()
        # Refresh via get untuk load semua relasi
        return SubmissionService.get(db, sub.ID) # type: ignore

    @staticmethod
    def update(db: Session, submission_id: int, payload: schemas.SubmissionUpdate, user_id: int) -> SubmissionModel:
        s = db.query(SubmissionModel).filter(SubmissionModel.ID == submission_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Submission tidak ditemukan")
        
        if payload.KodeUnik is not None: setattr(s, "KodeUnik", payload.KodeUnik)
        if payload.TotalCashAdvance is not None: setattr(s, "TotalCashAdvance", payload.TotalCashAdvance)
        if payload.CreatorID is not None: setattr(s, "CreatorID", payload.CreatorID)
        if payload.ReceiverID is not None: setattr(s, "ReceiverID", payload.ReceiverID)

        old_status = s.Status.value
        new_status = payload.Status.value if payload.Status else old_status
        
        if payload.Status is not None:
            setattr(s, "Status", payload.Status.value)
        
        if old_status != new_status:
            SubmissionService._create_log(db, s.ID, new_status, user_id, f"Status berubah dari {old_status} ke {new_status}")
        else:
            SubmissionService._create_log(db, s.ID, new_status, user_id, "Update data submission")

        db.commit()
        return SubmissionService.get(db, s.ID) # type: ignore

    @staticmethod
    def delete(db: Session, submission_id: int) -> None:
        s = db.query(SubmissionModel).filter(SubmissionModel.ID == submission_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Submission tidak ditemukan")
        db.delete(s)
        db.commit()

    @staticmethod
    def get_monthly_summary(db: Session, month: int, year: int) -> schemas.SubmissionSummary:
        submissions = db.query(SubmissionModel).filter(
            extract('month', SubmissionModel.created_at) == month,
            extract('year', SubmissionModel.created_at) == year
        ).all()

        total = len(submissions)
        total_money = sum(float(s.TotalCashAdvance) for s in submissions)
        total_pending = sum(1 for s in submissions if s.Status.value == models.SubmissionStatusEnum.Pending.value)
        total_accepted = sum(1 for s in submissions if s.Status.value == models.SubmissionStatusEnum.Accepted.value)
        total_rejected = sum(1 for s in submissions if s.Status.value == models.SubmissionStatusEnum.Rejected.value)
        
        total_accepted_money = sum(float(s.TotalCashAdvance) for s in submissions if s.Status.value == models.SubmissionStatusEnum.Accepted.value)
        total_rejected_money = sum(float(s.TotalCashAdvance) for s in submissions if s.Status.value == models.SubmissionStatusEnum.Rejected.value)
        total_pending_money = sum(float(s.TotalCashAdvance) for s in submissions if s.Status.value == models.SubmissionStatusEnum.Pending.value)

        return schemas.SubmissionSummary(
            month=month, year=year, 
            total_submissions=total, 
            total_cash_advance=total_money,
            total_pending=total_pending, 
            total_accepted=total_accepted, 
            total_rejected=total_rejected,
            total_cash_advance_accepted=total_accepted_money, 
            total_cash_advance_rejected=total_rejected_money, 
            total_cash_advance_pending=total_pending_money
        )