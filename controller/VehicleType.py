from typing import List
from sqlalchemy.orm import Session
from model import models

def get_vehicle_type(db: Session) -> List[models.VehicleType]:
    return db.query(models.VehicleType).all()

def create_vehicle_type(db: Session, vehicle_type: models.VehicleType) -> models.VehicleType:   
    db.add(vehicle_type)
    db.commit()
    db.refresh(vehicle_type)
    return vehicle_type