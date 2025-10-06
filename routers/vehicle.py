from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.database import SessionLocal
import controller.auth as auth
from services.vehicle_service import VehicleService
import schemas.schemas as schemas
from model.models import User as UserModel
from i18n.messages import get_message

router = APIRouter(prefix="/vehicle", tags=["Vehicle"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=schemas.SuccessListResponse[schemas.VehicleResponse])
def list_vehicles(db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessListResponse[schemas.VehicleResponse]:
    data = VehicleService.list(db)
    return schemas.SuccessListResponse[schemas.VehicleResponse](data=data, message=get_message("create_success", None))

@router.post("/", response_model=schemas.SuccessResponse[schemas.VehicleResponse])
def create_vehicle(payload: schemas.VehicleCreate, db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.VehicleResponse]:
    created = VehicleService.create(db, payload)
    return schemas.SuccessResponse[schemas.VehicleResponse](data=created, message=get_message("vehicle_create_success", None))

@router.put("/{vehicle_id}", response_model=schemas.SuccessResponse[schemas.VehicleResponse])
def update_vehicle(vehicle_id: int, payload: schemas.VehicleCreate, db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.VehicleResponse]:
    v = VehicleService.update(db, vehicle_id, payload)
    return schemas.SuccessResponse[schemas.VehicleResponse](data=v, message=get_message("update_success", None))

@router.delete("/{vehicle_id}", response_model=schemas.SuccessResponse[schemas.Message])
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.Message]:
    VehicleService.delete(db, vehicle_id)
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="Vehicle dihapus"), message=get_message("vehicle_delete_success", None))
