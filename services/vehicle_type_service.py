from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from model.models import VehicleType as VehicleTypeModel

class VehicleTypeService:
    @staticmethod
    def list(db: Session) -> List[VehicleTypeModel]:
        return db.query(VehicleTypeModel).order_by(VehicleTypeModel.ID.asc()).all()

    @staticmethod
    def get(db: Session, vt_id: int) -> Optional[VehicleTypeModel]:
        return db.query(VehicleTypeModel).filter(VehicleTypeModel.ID == vt_id).first()

    @staticmethod
    def create(db: Session, nama: str) -> VehicleTypeModel:
        # simple duplicate check by name (optional, remove if not required)
        existing = db.query(VehicleTypeModel).filter(VehicleTypeModel.Nama == nama).first()
        if existing:
            raise HTTPException(status_code=400, detail="VehicleType sudah ada")
        vt = VehicleTypeModel(Nama=nama)
        db.add(vt)
        db.commit()
        db.refresh(vt)
        return vt

    @staticmethod
    def update(db: Session, vt_id: int, nama: str) -> VehicleTypeModel:
        vt = db.query(VehicleTypeModel).filter(VehicleTypeModel.ID == vt_id).first()
        if not vt:
            raise HTTPException(status_code=404, detail="VehicleType tidak ditemukan")
        if nama != vt.Nama:
            dup = db.query(VehicleTypeModel).filter(VehicleTypeModel.Nama == nama).first()
            if dup:
                raise HTTPException(status_code=400, detail="Nama sudah dipakai")
            # gunakan setattr agar tidak diperingatkan static type checker (Column vs str)
            setattr(vt, "Nama", nama)
        db.commit()
        db.refresh(vt)
        return vt

    @staticmethod
    def delete(db: Session, vt_id: int) -> None:
        vt = db.query(VehicleTypeModel).filter(VehicleTypeModel.ID == vt_id).first()
        if not vt:
            raise HTTPException(status_code=404, detail="VehicleType tidak ditemukan")
        db.delete(vt)
        db.commit()
