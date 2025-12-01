from __future__ import annotations
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract, func
from fastapi import HTTPException
import model.models as models
from model.models import Submission as SubmissionModel, SubmissionLog, SubmissionStatusEnum
import schemas.schemas as schemas

class SubmissionService:
    @staticmethod
    def _get_base_query(db: Session):
        """
        Query dasar dengan Eager Loading.
        Added: joinedload(SubmissionModel.dinas)
        """
        return db.query(SubmissionModel).options(
            joinedload(SubmissionModel.creator),
            joinedload(SubmissionModel.receiver),
            joinedload(SubmissionModel.dinas), # Load info Dinas
            joinedload(SubmissionModel.logs).joinedload(SubmissionLog.updater)
        )

    @staticmethod
    def list(
        db: Session, 
        creator_id: int | None = None, 
        receiver_id: int | None = None, 
        status: str | None = None,
        month: int | None = None,
        year: int | None = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        
        q = SubmissionService._get_base_query(db)
        
        # Filters
        if creator_id: q = q.filter(SubmissionModel.CreatorID == creator_id)
        if receiver_id: q = q.filter(SubmissionModel.ReceiverID == receiver_id)
        if status: q = q.filter(SubmissionModel.Status == status)
        if month: q = q.filter(extract('month', SubmissionModel.created_at) == month)
        if year: q = q.filter(extract('year', SubmissionModel.created_at) == year)
        
        q = q.order_by(SubmissionModel.created_at.desc())
        
        # Pagination Data
        data = q.offset(offset).limit(limit).all()
        
        # Count Query (Optimized: reuse filters logic ideally, but simplified here)
        count_q = db.query(func.count(SubmissionModel.ID))
        if creator_id: count_q = count_q.filter(SubmissionModel.CreatorID == creator_id)
        if receiver_id: count_q = count_q.filter(SubmissionModel.ReceiverID == receiver_id)
        if status: count_q = count_q.filter(SubmissionModel.Status == status)
        if month: count_q = count_q.filter(extract('month', SubmissionModel.created_at) == month)
        if year: count_q = count_q.filter(extract('year', SubmissionModel.created_at) == year)
        
        total_records = count_q.scalar() or 0
        has_more = (offset + len(data)) < total_records

        # Statistics
        stat_q = db.query(SubmissionModel.Status, func.count(SubmissionModel.ID))
        if creator_id: stat_q = stat_q.filter(SubmissionModel.CreatorID == creator_id)
        if receiver_id: stat_q = stat_q.filter(SubmissionModel.ReceiverID == receiver_id)
        # Apply date filter to stats as well
        if month: stat_q = stat_q.filter(extract('month', SubmissionModel.created_at) == month)
        if year: stat_q = stat_q.filter(extract('year', SubmissionModel.created_at) == year)
        
        stats_result = stat_q.group_by(SubmissionModel.Status).all()
        
        stat_dict = {"total_data": total_records}
        for s in SubmissionStatusEnum:
            stat_dict[f"total_{s.value.lower()}"] = 0
            
        for status_enum, count in stats_result:
            key = f"total_{status_enum.value.lower()}"
            stat_dict[key] = count

        return {
            "list": data,
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
            "month": month,
            "year": year,
            "stat": stat_dict
        }

    @staticmethod
    def get(db: Session, submission_id: int) -> Optional[SubmissionModel]:
        return SubmissionService._get_base_query(db).filter(SubmissionModel.ID == submission_id).first()

    @staticmethod
    def _create_log(db: Session, submission_id: int, status: str, user_id: int | None, notes: str | None):
        log = SubmissionLog(
            SubmissionID=submission_id, Status=status, UpdatedByUserID=user_id, Notes=notes
        )
        db.add(log)

    @staticmethod
    def create(db: Session, payload: schemas.SubmissionCreate) -> SubmissionModel:
        creator = db.query(models.User).filter(models.User.ID == payload.CreatorID).first()
        if not creator:
            raise HTTPException(status_code=400, detail="CreatorID tidak ditemukan")
        if not db.query(models.User).filter(models.User.ID == payload.ReceiverID).first():
            raise HTTPException(status_code=400, detail="ReceiverID tidak ditemukan")
        
        status_value = payload.Status.value if payload.Status else models.SubmissionStatusEnum.Pending.value
        
        # Auto-assign DinasID dari Creator
        sub = SubmissionModel(
            KodeUnik=payload.KodeUnik, CreatorID=payload.CreatorID, ReceiverID=payload.ReceiverID,
            TotalCashAdvance=payload.TotalCashAdvance, Status=status_value,
            Description=payload.Description, Date=payload.Date,
            DinasID=creator.DinasID 
        )
        db.add(sub)
        db.flush() 
        SubmissionService._create_log(db, sub.ID, status_value, payload.CreatorID, "Submission dibuat")
        db.commit()
        return SubmissionService.get(db, sub.ID) # type: ignore

    @staticmethod
    def update(db: Session, submission_id: int, payload: schemas.SubmissionUpdate, user_id: int) -> SubmissionModel:
        s = db.query(SubmissionModel).filter(SubmissionModel.ID == submission_id).first()
        if not s: raise HTTPException(404, "Submission tidak ditemukan")

        if payload.KodeUnik is not None: setattr(s, "KodeUnik", payload.KodeUnik)
        if payload.TotalCashAdvance is not None: setattr(s, "TotalCashAdvance", payload.TotalCashAdvance)
        if payload.CreatorID is not None: setattr(s, "CreatorID", payload.CreatorID)
        if payload.ReceiverID is not None: setattr(s, "ReceiverID", payload.ReceiverID)

        old_status = s.Status.value
        new_status = payload.Status.value if payload.Status else old_status
        if payload.Status is not None: setattr(s, "Status", payload.Status.value)
        
        if old_status != new_status:
            SubmissionService._create_log(db, s.ID, new_status, user_id, f"Status berubah dari {old_status} ke {new_status}")
        else:
            SubmissionService._create_log(db, s.ID, new_status, user_id, "Update data submission")

        db.commit()
        return SubmissionService.get(db, s.ID) # type: ignore

    @staticmethod
    def delete(db: Session, submission_id: int) -> None:
        s = db.query(SubmissionModel).filter(SubmissionModel.ID == submission_id).first()
        if not s: raise HTTPException(404, "Submission tidak ditemukan")
        db.delete(s)
        db.commit()

    @staticmethod
    def get_monthly_summary(db: Session, month: int, year: int) -> schemas.SubmissionSummary:
        # Optimized Summary Query
        submissions = db.query(SubmissionModel.Status, SubmissionModel.TotalCashAdvance).filter(
            extract('month', SubmissionModel.created_at) == month,
            extract('year', SubmissionModel.created_at) == year
        ).all()

        total = len(submissions)
        total_money = sum(float(s.TotalCashAdvance) for s in submissions)
        
        # Manual aggregation in python is okay for summary (usually < 1000 records per month)
        # but SQL aggregation is better if scaling up. Keeping Python for simplicity as logic requested.
        total_pending = sum(1 for s in submissions if s.Status == models.SubmissionStatusEnum.Pending)
        total_accepted = sum(1 for s in submissions if s.Status == models.SubmissionStatusEnum.Accepted)
        total_rejected = sum(1 for s in submissions if s.Status == models.SubmissionStatusEnum.Rejected)
        
        total_accepted_money = sum(float(s.TotalCashAdvance) for s in submissions if s.Status == models.SubmissionStatusEnum.Accepted)
        total_rejected_money = sum(float(s.TotalCashAdvance) for s in submissions if s.Status == models.SubmissionStatusEnum.Rejected)
        total_pending_money = sum(float(s.TotalCashAdvance) for s in submissions if s.Status == models.SubmissionStatusEnum.Pending)

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

    @staticmethod
    def get_monthly_details_optimized(db: Session, month: int, year: int) -> List[SubmissionModel]:
        """
        Pengganti logic lama yang fetch all then filter. 
        Sekarang filter langsung di SQL.
        """
        q = SubmissionService._get_base_query(db)
        q = q.filter(extract('month', SubmissionModel.created_at) == month)
        q = q.filter(extract('year', SubmissionModel.created_at) == year)
        return q.order_by(SubmissionModel.created_at.desc()).all()