from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.database import SessionLocal
import controller.auth as auth
from model.models import User as UserModel
from services.stat_service import StatService
import schemas.schemas as schemas

router = APIRouter(prefix="/stat", tags=["Statistics"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get(
    "/pic", 
    response_model=schemas.SuccessResponse[schemas.PicStatResponse],
    summary="Get PIC Dashboard Statistics",
    description="Mendapatkan ringkasan statistik untuk dashboard PIC, termasuk jumlah kendaraan, laporan, dan grafik penggunaan dana per bulan."
)
def get_pic_stats(
    db: Session = Depends(get_db),
    _user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.PicStatResponse]:
    data = StatService.get_pic_stats(db, _user.ID)
    return schemas.SuccessResponse[schemas.PicStatResponse](
        data=data,
        message="Statistik PIC berhasil diambil"
    )

@router.get(
    "/kadis", 
    response_model=schemas.SuccessResponse[schemas.KadisStatResponse],
    summary="Get Kepala Dinas Dashboard Statistics",
    description="Mendapatkan statistik untuk Kepala Dinas. Data mencakup total proposal yang ditinjau, total laporan dari staff dinas, dan grafik tren bulanan dalam lingkup dinas tersebut."
)
def get_kadis_stats(
    db: Session = Depends(get_db),
    _user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.KadisStatResponse]:
    
    if not _user.DinasID:
        raise HTTPException(status_code=400, detail="User tidak terdaftar dalam dinas manapun")

    data = StatService.get_kadis_stats(db, _user.DinasID)
    return schemas.SuccessResponse[schemas.KadisStatResponse](
        data=data,
        message="Statistik Kadis berhasil diambil"
    )

@router.get(
    "/admin", 
    response_model=schemas.SuccessResponse[schemas.AdminStatResponse],
    summary="Get Admin Dashboard Statistics",
    description="Mendapatkan statistik global atau spesifik dinas untuk Admin. Mencakup total kendaraan, user, laporan pending, dan ringkasan submission."
)
def get_admin_stats(
    dinas_id: int | None = Query(None, description="ID Dinas target. Jika kosong, menggunakan Dinas ID admin (jika ada)."),
    db: Session = Depends(get_db),
    _user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.AdminStatResponse]:
    
    # Tentukan Dinas ID target
    target_dinas = dinas_id if dinas_id else _user.DinasID
    
    if not target_dinas:
        raise HTTPException(status_code=400, detail="Harap spesifikasikan dinas_id")

    data = StatService.get_admin_stats(db, target_dinas)
    return schemas.SuccessResponse[schemas.AdminStatResponse](
        data=data,
        message="Statistik Admin berhasil diambil"
    )