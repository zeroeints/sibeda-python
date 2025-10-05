from typing import List, TypedDict, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
import model.models as models
from model.models import Vehicle as Vehicle
from schemas.schemas import VehicleCreate

class VehicleData(TypedDict, total=False):
    Nama: str
    Plat: str
    VehicleTypeID: int
    KapasitasMesin: Optional[int]
    Odometer: Optional[int]
    JenisBensin: Optional[str]
    Merek: Optional[str]
    FotoFisik: Optional[str]
    Status: str

def get_vehicle(db: Session) -> List[Vehicle]:
    return db.query(Vehicle).all()

def create_vehicle(db: Session, payload: VehicleCreate) -> Vehicle:
    if not db.query(models.VehicleType).filter(models.VehicleType.ID == payload.VehicleTypeID).first():
        raise HTTPException(status_code=400, detail="VehicleTypeID tidak ditemukan")

    # Pre-check unique Plat for friendlier error vs DB constraint
    existing = db.query(models.Vehicle).filter(models.Vehicle.Plat == payload.Plat).first()
    if existing:
        raise HTTPException(status_code=400, detail="Plat sudah terdaftar")

    data: VehicleData = {
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

    vehicle = models.Vehicle(**data)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle
