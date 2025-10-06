from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
import model.models as models
from model.models import Report as ReportModel
from schemas.schemas import ReportCreate, ReportUpdate

class ReportService:
    @staticmethod
    def list(db: Session, user_id: int | None = None, vehicle_id: int | None = None) -> List[ReportModel]:
        q = db.query(ReportModel)
        if user_id is not None:
            q = q.filter(ReportModel.UserID == user_id)
        if vehicle_id is not None:
            q = q.filter(ReportModel.VehicleID == vehicle_id)
        return q.order_by(ReportModel.ID.desc()).all()

    @staticmethod
    def get(db: Session, report_id: int) -> Optional[ReportModel]:
        return db.query(ReportModel).filter(ReportModel.ID == report_id).first()

    @staticmethod
    def create(db: Session, payload: ReportCreate) -> ReportModel:
        # basic FK validation
        if not db.query(models.User).filter(models.User.ID == payload.UserID).first():
            raise HTTPException(status_code=400, detail="UserID tidak ditemukan")
        if not db.query(models.Vehicle).filter(models.Vehicle.ID == payload.VehicleID).first():
            raise HTTPException(status_code=400, detail="VehicleID tidak ditemukan")
        report = ReportModel(
            KodeUnik=payload.KodeUnik,
            UserID=payload.UserID,
            VehicleID=payload.VehicleID,
            AmountRupiah=payload.AmountRupiah,
            AmountLiter=payload.AmountLiter,
            Description=payload.Description,
            Latitude=payload.Latitude,
            Longitude=payload.Longitude,
            VehiclePhysicalPhotoPath=payload.VehiclePhysicalPhotoPath,
            OdometerPhotoPath=payload.OdometerPhotoPath,
            InvoicePhotoPath=payload.InvoicePhotoPath,
            MyPertaminaPhotoPath=payload.MyPertaminaPhotoPath,
            Odometer=payload.Odometer,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def update(db: Session, report_id: int, payload: ReportUpdate) -> ReportModel:
        r = db.query(ReportModel).filter(ReportModel.ID == report_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Report tidak ditemukan")
        # optional FK validations if changed
        if payload.UserID is not None and payload.UserID != r.UserID:
            if not db.query(models.User).filter(models.User.ID == payload.UserID).first():
                raise HTTPException(status_code=400, detail="UserID tidak ditemukan")
            setattr(r, "UserID", payload.UserID)  # avoid static type checker complaining
        if payload.VehicleID is not None and payload.VehicleID != r.VehicleID:
            if not db.query(models.Vehicle).filter(models.Vehicle.ID == payload.VehicleID).first():
                raise HTTPException(status_code=400, detail="VehicleID tidak ditemukan")
            setattr(r, "VehicleID", payload.VehicleID)  # avoid static type checker complaining
        mutable_fields = [
            "KodeUnik","AmountRupiah","AmountLiter","Description","Latitude","Longitude",
            "VehiclePhysicalPhotoPath","OdometerPhotoPath","InvoicePhotoPath","MyPertaminaPhotoPath","Odometer"
        ]
        for field in mutable_fields:
            value = getattr(payload, field, None)
            if value is not None:
                setattr(r, field, value)
        db.commit()
        db.refresh(r)
        return r

    @staticmethod
    def delete(db: Session, report_id: int) -> None:
        r = db.query(ReportModel).filter(ReportModel.ID == report_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Report tidak ditemukan")
        db.delete(r)
        db.commit()
