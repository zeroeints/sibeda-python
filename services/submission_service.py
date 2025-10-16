from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
import model.models as models
from model.models import Submission as SubmissionModel
from schemas.schemas import SubmissionCreate, SubmissionUpdate


class SubmissionService:
    @staticmethod
    def list(db: Session, creator_id: int | None = None, receiver_id: int | None = None, vehicle_id: int | None = None) -> List[SubmissionModel]:
        q = db.query(SubmissionModel)
        if creator_id is not None:
            q = q.filter(SubmissionModel.CreatorID == creator_id)
        if receiver_id is not None:
            q = q.filter(SubmissionModel.ReceiverID == receiver_id)
        if vehicle_id is not None:
            q = q.filter(SubmissionModel.VehicleID == vehicle_id)
        return q.order_by(SubmissionModel.ID.desc()).all()

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
