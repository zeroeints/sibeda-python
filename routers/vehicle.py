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
    return schemas.SuccessListResponse[schemas.VehicleResponse](data=data, message=get_message("create_success", None))  # type: ignore

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

@router.get("/my/vehicles", response_model=schemas.SuccessListResponse[schemas.MyVehicleResponse])
def get_my_vehicles(db: Session = Depends(get_db), current_user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessListResponse[schemas.MyVehicleResponse]:
    """
    Mendapatkan semua kendaraan yang pernah digunakan oleh user
    
    Menampilkan kendaraan yang terkait dengan user melalui:
    - Submission (sebagai creator atau receiver)
    - Report (pengisian bensin)
    
    Response mencakup:
    - Data kendaraan lengkap (Nama, Plat, Merek, dll)
    - Tipe kendaraan
    - Statistik penggunaan (total submission, report, bensin, biaya)
    - Info pengisian bensin terakhir
    """
    vehicles = VehicleService.get_my_vehicles(db, current_user.ID)  # type: ignore
    return schemas.SuccessListResponse[schemas.MyVehicleResponse](
        data=vehicles,  # type: ignore
        message=f"Ditemukan {len(vehicles)} kendaraan"
    )

@router.get("/my/vehicles/{vehicle_id}", response_model=schemas.SuccessResponse[schemas.VehicleDetailResponse])
def get_my_vehicle_detail(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.VehicleDetailResponse]:
    """
    Mendapatkan detail lengkap kendaraan termasuk riwayat pengisian bensin
    
    - **vehicle_id**: ID kendaraan yang ingin dilihat detailnya
    
    Response mencakup:
    - Data kendaraan lengkap
    - Statistik penggunaan
    - Riwayat 10 pengisian bensin terakhir (tanggal, liter, rupiah, odometer)
    """
    vehicle_detail = VehicleService.get_vehicle_detail(db, vehicle_id, current_user.ID)  # type: ignore
    return schemas.SuccessResponse[schemas.VehicleDetailResponse](
        data=vehicle_detail,  # type: ignore
        message="Detail kendaraan berhasil ditemukan"
    )
