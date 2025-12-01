from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database.database import SessionLocal
import controller.auth as auth
import schemas.schemas as schemas
from model.models import User as UserModel
from services.vehicle_type_service import VehicleTypeService
from i18n.messages import get_message
from utils.responses import detect_lang

router = APIRouter(prefix="/vehicle-type", tags=["VehicleType"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get(
    "/", 
    response_model=schemas.SuccessListResponse[schemas.VehicleTypeResponse],
    summary="List Vehicle Types",
    description="Mendapatkan daftar tipe kendaraan (Mobil, Motor, Truk, dll)."
)
def list_vehicle_types(request: Request, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)):
    data = VehicleTypeService.list(db)
    lang = detect_lang(request)
    return schemas.SuccessListResponse[schemas.VehicleTypeResponse](data=data, message=get_message("create_success", lang))

@router.get(
    "/{vt_id}", 
    response_model=schemas.SuccessResponse[schemas.VehicleTypeResponse],
    summary="Get Vehicle Type",
    description="Mendapatkan detail tipe kendaraan."
)
def get_vehicle_type(vt_id: int, request: Request, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)):
    vt = VehicleTypeService.get(db, vt_id)
    if not vt:
        raise HTTPException(status_code=404, detail="VehicleType tidak ditemukan")
    lang = detect_lang(request)
    return schemas.SuccessResponse[schemas.VehicleTypeResponse](data=vt, message=get_message("create_success", lang))

@router.post(
    "/", 
    response_model=schemas.SuccessResponse[schemas.VehicleTypeResponse],
    summary="Create Vehicle Type",
    description="Membuat tipe kendaraan baru."
)
def create_vehicle_type(payload: schemas.VehicleCreate, request: Request, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)):
    created = VehicleTypeService.create(db, payload.Nama)
    lang = detect_lang(request)
    return schemas.SuccessResponse[schemas.VehicleTypeResponse](data=created, message=get_message("vehicle_type_create_success", lang))

@router.put(
    "/{vt_id}", 
    response_model=schemas.SuccessResponse[schemas.VehicleTypeResponse],
    summary="Update Vehicle Type",
    description="Mengupdate nama tipe kendaraan."
)
def update_vehicle_type(vt_id: int, payload: schemas.VehicleUpdate, request: Request, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)):
    updated = VehicleTypeService.update(db, vt_id, payload.Nama)
    lang = detect_lang(request)
    return schemas.SuccessResponse[schemas.VehicleTypeResponse](data=updated, message=get_message("vehicle_type_update_success", lang))

@router.delete(
    "/{vt_id}", 
    response_model=schemas.SuccessResponse[schemas.Message],
    summary="Delete Vehicle Type",
    description="Menghapus tipe kendaraan."
)
def delete_vehicle_type(vt_id: int, request: Request, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)):
    VehicleTypeService.delete(db, vt_id)
    lang = detect_lang(request)
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="VehicleType dihapus"), message=get_message("vehicle_type_delete_success", lang))