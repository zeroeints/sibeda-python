from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from model.models import VehicleType

class VehicleTypeService:
    @staticmethod
    def list(db: Session) -> List[VehicleType]:
        return db.query(VehicleType).order_by(VehicleType.id.asc()).all()

    @staticmethod
    def get(db: Session, vt_id: int) -> Optional[VehicleType]:
        return db.query(VehicleType).filter(VehicleType.id == vt_id).first()

    @staticmethod
    def create(db: Session, nama: str) -> VehicleType:
        existing = db.query(VehicleType).filter(VehicleType.nama == nama).first()
        if existing:
            raise HTTPException(status_code=400, detail="VehicleType sudah ada")
        
        vt = VehicleType(nama=nama)
        db.add(vt)
        db.commit()
        db.refresh(vt)
        return vt

    @staticmethod
    def update(db: Session, vt_id: int, nama: str) -> VehicleType:
        vt = db.query(VehicleType).filter(VehicleType.id == vt_id).first()
        if not vt:
            raise HTTPException(status_code=404, detail="VehicleType tidak ditemukan")
        
        if nama != vt.nama:
            dup = db.query(VehicleType).filter(VehicleType.nama == nama).first()
            if dup:
                raise HTTPException(status_code=400, detail="Nama sudah dipakai")
            vt.nama = nama
            
        db.commit()
        db.refresh(vt)
        return vt

    @staticmethod
    def delete(db: Session, vt_id: int) -> None:
        vt = db.query(VehicleType).filter(VehicleType.id == vt_id).first()
        if not vt:
            raise HTTPException(status_code=404, detail="VehicleType tidak ditemukan")
        db.delete(vt)
        db.commit()