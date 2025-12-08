from __future__ import annotations
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract, func
from fastapi import HTTPException
import model.models as models
import schemas.schemas as schemas
from pydantic import BaseModel

class SubmissionService:
    @staticmethod
    def _get_base_query(db: Session):
        return db.query(models.Submission).options(
            joinedload(models.Submission.creator),
            joinedload(models.Submission.receiver).joinedload(models.User.vehicles).joinedload(models.Vehicle.vehicle_type),
            joinedload(models.Submission.dinas),
            joinedload(models.Submission.logs).joinedload(models.SubmissionLog.updater)
        )

    @staticmethod
    def list(
        db: Session, 
        creator_id: int | None = None, 
        receiver_id: int | None = None, 
        status: str | None = None,
        month: int | None = None,
        year: int | None = None,
        dinas_id: int | None = None,
        limit: int = 10,
        offset: int = 0,
        current_user: models.User | None = None
    ) -> Dict[str, Any]:
        
        q = SubmissionService._get_base_query(db)
        
        if creator_id: q = q.filter(models.Submission.creator_id == creator_id)
        if receiver_id: q = q.filter(models.Submission.receiver_id == receiver_id)
        if status: q = q.filter(models.Submission.status == status)
        if month: q = q.filter(extract('month', models.Submission.created_at) == month)
        if year: q = q.filter(extract('year', models.Submission.created_at) == year)
        if dinas_id: q = q.filter(models.Submission.dinas_id == dinas_id)
        
        q = q.order_by(models.Submission.created_at.desc()).filter(models.Submission.dinas_id == current_user.dinas_id)
        data = q.offset(offset).limit(limit).all()

        # Manually attach vehicles to each submission for serialization
        for submission in data:
            submission.vehicles = submission.receiver.vehicles if submission.receiver else []
        
        # Count Query
        count_q = db.query(func.count(models.Submission.id))
        if creator_id: count_q = count_q.filter(models.Submission.creator_id == creator_id)
        if receiver_id: count_q = count_q.filter(models.Submission.receiver_id == receiver_id)
        if status: count_q = count_q.filter(models.Submission.status == status)
        if month: count_q = count_q.filter(extract('month', models.Submission.created_at) == month)
        if year: count_q = count_q.filter(extract('year', models.Submission.created_at) == year)
        if dinas_id: count_q = count_q.filter(models.Submission.dinas_id == dinas_id)
        
        total_records = count_q.scalar() or 0
        has_more = (offset + len(data)) < total_records

        # Statistics
        stat_q = db.query(models.Submission.status, func.count(models.Submission.id))
        if creator_id: stat_q = stat_q.filter(models.Submission.creator_id == creator_id)
        if receiver_id: stat_q = stat_q.filter(models.Submission.receiver_id == receiver_id)
        if month: stat_q = stat_q.filter(extract('month', models.Submission.created_at) == month)
        if year: stat_q = stat_q.filter(extract('year', models.Submission.created_at) == year)
        if dinas_id: stat_q = stat_q.filter(models.Submission.dinas_id == dinas_id)
        
        stats_result = stat_q.group_by(models.Submission.status).all()
        
        stat_dict = {"total_data": total_records}
        for s in models.SubmissionStatusEnum:
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
    def get(db: Session, submission_id: int) -> Optional[models.Submission]:
        submission = SubmissionService._get_base_query(db).filter(models.Submission.id == submission_id).first()
        if submission:
            # Manually attach vehicles to the submission object for serialization
            submission.vehicles = submission.receiver.vehicles if submission.receiver else []
        return submission

    @staticmethod
    def _create_log(db: Session, submission_id: int, status: str, user_id: int | None, notes: str | None):
        log = models.SubmissionLog(
            submission_id=submission_id, status=status, updated_by_user_id=user_id, notes=notes
        )
        db.add(log)

    @staticmethod
    def create(db: Session, payload: schemas.SubmissionCreate) -> models.Submission:
        creator = db.query(models.User).filter(models.User.id == payload.creator_id).first()
        if not creator:
            raise HTTPException(status_code=400, detail="Creator ID tidak ditemukan")
        if not db.query(models.User).filter(models.User.id == payload.receiver_id).first():
            raise HTTPException(status_code=400, detail="Receiver ID tidak ditemukan")
        
        status_value = payload.status.value if payload.status else models.SubmissionStatusEnum.pending.value
        
        sub = models.Submission(
            kode_unik=payload.kode_unik, 
            creator_id=payload.creator_id, 
            receiver_id=payload.receiver_id,
            total_cash_advance=payload.total_cash_advance, 
            status=status_value,
            description=payload.description, 
            date=payload.date,
            dinas_id=creator.dinas_id 
        )
        db.add(sub)
        db.flush() 
        SubmissionService._create_log(db, sub.id, status_value, payload.creator_id, "Submission dibuat")
        db.commit()
        return SubmissionService.get(db, sub.id) # type: ignore

    @staticmethod
    def update(db: Session, submission_id: int, payload: schemas.SubmissionUpdate, user_id: int) -> models.Submission:
        s = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
        if not s: raise HTTPException(404, "Submission tidak ditemukan")

        if payload.kode_unik is not None: s.kode_unik = payload.kode_unik
        if payload.total_cash_advance is not None: s.total_cash_advance = payload.total_cash_advance
        if payload.creator_id is not None: s.creator_id = payload.creator_id
        if payload.receiver_id is not None: s.receiver_id = payload.receiver_id

        old_status = s.status.value
        new_status = payload.status.value if payload.status else old_status
        if payload.status is not None: s.status = payload.status.value
        
        if old_status != new_status:
            SubmissionService._create_log(db, s.id, new_status, user_id, f"Status berubah dari {old_status} ke {new_status}")
        else:
            SubmissionService._create_log(db, s.id, new_status, user_id, "Update data submission")

        db.commit()
        return SubmissionService.get(db, s.id) # type: ignore

    @staticmethod
    def delete(db: Session, submission_id: int) -> None:
        s = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
        if not s: raise HTTPException(404, "Submission tidak ditemukan")
        db.delete(s)
        db.commit()

    @staticmethod
    def get_monthly_summary(db: Session, month: int, year: int) -> schemas.SubmissionSummary:
        submissions = db.query(models.Submission.status, models.Submission.total_cash_advance).filter(
            extract('month', models.Submission.created_at) == month,
            extract('year', models.Submission.created_at) == year
        ).all()

        total = len(submissions)
        total_money = sum(float(s.total_cash_advance) for s in submissions)
        
        total_pending = sum(1 for s in submissions if s.status == models.SubmissionStatusEnum.pending)
        total_accepted = sum(1 for s in submissions if s.status == models.SubmissionStatusEnum.accepted)
        total_rejected = sum(1 for s in submissions if s.status == models.SubmissionStatusEnum.rejected)
        
        total_accepted_money = sum(float(s.total_cash_advance) for s in submissions if s.status == models.SubmissionStatusEnum.accepted)
        total_rejected_money = sum(float(s.total_cash_advance) for s in submissions if s.status == models.SubmissionStatusEnum.rejected)
        total_pending_money = sum(float(s.total_cash_advance) for s in submissions if s.status == models.SubmissionStatusEnum.pending)

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
    def get_monthly_details_optimized(db: Session, month: int, year: int) -> List[models.Submission]:
        q = SubmissionService._get_base_query(db)
        q = q.filter(extract('month', models.Submission.created_at) == month)
        q = q.filter(extract('year', models.Submission.created_at) == year)
        return q.order_by(models.Submission.created_at.desc()).all()
    
    @staticmethod
    def get_my_submissions(
        db: Session, 
        user_id: int, 
        month: int | None = None, 
        year: int | None = None, 
        limit: int = 10, 
        offset: int = 0
    ) -> Dict[str, Any]:
        q = SubmissionService._get_base_query(db)
        q = q.filter(models.Submission.receiver_id == user_id)
        
        if month: q = q.filter(extract('month', models.Submission.created_at) == month)
        if year: q = q.filter(extract('year', models.Submission.created_at) == year)
        
        q = q.order_by(models.Submission.created_at.desc())
        
        total_records = db.query(func.count(models.Submission.id)).filter(models.Submission.receiver_id == user_id)
        if month: total_records = total_records.filter(extract('month', models.Submission.created_at) == month)
        if year: total_records = total_records.filter(extract('year', models.Submission.created_at) == year)
        total_count = total_records.scalar() or 0
        total_amounted = q.filter(models.Submission.status == models.SubmissionStatusEnum.accepted).with_entities(func.coalesce(func.sum(models.Submission.total_cash_advance), 0.0)).scalar() or 0.0
        total_accepted = q.filter(models.Submission.status == models.SubmissionStatusEnum.accepted).count() or 0
        total_pending = q.filter(models.Submission.status == models.SubmissionStatusEnum.pending).count() or 0
        total_rejected = q.filter(models.Submission.status == models.SubmissionStatusEnum.rejected).count() or 0
        
        data = q.offset(offset).limit(limit).all()

        # Manually attach vehicles to each submission for serialization
        for submission in data:
            submission.vehicles = submission.receiver.vehicles if submission.receiver else []

        has_more = (offset + len(data)) < total_count
        
        return {
            "list": data,
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
            "month": month,
            "year": year,
            "stat": {"total_data": total_count, "total_accepted": total_accepted, "total_pending": total_pending, "total_rejected": total_rejected, "total_amounted": total_amounted}
        }
