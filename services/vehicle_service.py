from __future__ import annotations
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
import model.models as models
from model.models import Vehicle as VehicleModel
from schemas.schemas import VehicleCreate

class VehicleService:
    @staticmethod
    def list(db: Session) -> List[VehicleModel]:
        return db.query(VehicleModel).all()

    @staticmethod
    def create(db: Session, payload: VehicleCreate) -> VehicleModel:
        # Ensure vehicle type exists
        if not db.query(models.VehicleType).filter(models.VehicleType.ID == payload.VehicleTypeID).first():
            raise HTTPException(status_code=400, detail="VehicleTypeID tidak ditemukan")
        # Unique plat
        if db.query(VehicleModel).filter(VehicleModel.Plat == payload.Plat).first():
            raise HTTPException(status_code=400, detail="Plat sudah terdaftar")
        data: Dict[str, Any] = {
            "Nama": payload.Nama,
            "Plat": payload.Plat,
            "VehicleTypeID": payload.VehicleTypeID,
            "KapasitasMesin": payload.KapasitasMesin,
            "Odometer": payload.Odometer,
            "JenisBensin": payload.JenisBensin,
            "Merek": payload.Merek,
            "FotoFisik": payload.FotoFisik,
        }
        if payload.Status:
            data["Status"] = payload.Status.value
        v = models.Vehicle(**data)
        db.add(v)
        db.commit()
        db.refresh(v)
        return v

    @staticmethod
    def update(db: Session, vehicle_id: int, payload: VehicleCreate) -> VehicleModel:
        v = db.query(VehicleModel).filter(VehicleModel.ID == vehicle_id).first()
        if not v:
            raise HTTPException(status_code=404, detail="Vehicle tidak ditemukan")
        if payload.Plat != v.Plat and db.query(VehicleModel).filter(VehicleModel.Plat == payload.Plat).first():
            raise HTTPException(status_code=400, detail="Plat sudah terdaftar")
        # ensure vehicle type still valid
        if not db.query(models.VehicleType).filter(models.VehicleType.ID == payload.VehicleTypeID).first():
            raise HTTPException(status_code=400, detail="VehicleTypeID tidak ditemukan")
        update_map: Dict[str, Any] = {
            "Nama": payload.Nama,
            "Plat": payload.Plat,
            "VehicleTypeID": payload.VehicleTypeID,
            "KapasitasMesin": payload.KapasitasMesin,
            "Odometer": payload.Odometer,
            "JenisBensin": payload.JenisBensin,
            "Merek": payload.Merek,
            "FotoFisik": payload.FotoFisik,
        }
        if payload.Status:
            update_map["Status"] = payload.Status.value
        for field, value in update_map.items():
            setattr(v, field, value)
        db.commit()
        db.refresh(v)
        return v

    @staticmethod
    def delete(db: Session, vehicle_id: int) -> None:
        v = db.query(VehicleModel).filter(VehicleModel.ID == vehicle_id).first()
        if not v:
            raise HTTPException(status_code=404, detail="Vehicle tidak ditemukan")
        db.delete(v)
        db.commit()
