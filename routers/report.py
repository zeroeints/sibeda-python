from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.database import SessionLocal
import controller.auth as auth
import schemas.schemas as schemas
from model.models import User as UserModel
from services.report_service import ReportService
from i18n.messages import get_message

router = APIRouter(prefix="/report", tags=["Report"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=schemas.SuccessListResponse[schemas.ReportResponse])
def list_reports(user_id: int | None = None, vehicle_id: int | None = None, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessListResponse[schemas.ReportResponse]:
    data = ReportService.list(db, user_id=user_id, vehicle_id=vehicle_id)
    return schemas.SuccessListResponse[schemas.ReportResponse](data=data, message=get_message("create_success", None))

@router.get("/{report_id}", response_model=schemas.SuccessResponse[schemas.ReportResponse])
def get_report(report_id: int, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.ReportResponse]:
    r = ReportService.get(db, report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Report tidak ditemukan")
    return schemas.SuccessResponse[schemas.ReportResponse](data=r, message=get_message("create_success", None))

@router.post("", response_model=schemas.SuccessResponse[schemas.ReportResponse])
def create_report(payload: schemas.ReportCreate, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.ReportResponse]:
    created = ReportService.create(db, payload)
    return schemas.SuccessResponse[schemas.ReportResponse](data=created, message=get_message("report_create_success", None))

@router.put("/{report_id}", response_model=schemas.SuccessResponse[schemas.ReportResponse])
def update_report(report_id: int, payload: schemas.ReportUpdate, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.ReportResponse]:
    updated = ReportService.update(db, report_id, payload)
    return schemas.SuccessResponse[schemas.ReportResponse](data=updated, message=get_message("report_update_success", None))

@router.delete("/{report_id}", response_model=schemas.SuccessResponse[schemas.Message])
def delete_report(report_id: int, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.Message]:
    ReportService.delete(db, report_id)
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="Report dihapus"), message=get_message("report_delete_success", None))

@router.get("/my/reports", response_model=schemas.PaginatedResponse[schemas.MyReportResponse])
def get_my_reports(
    vehicle_id: int | None = Query(None, description="Filter berdasarkan ID kendaraan"),
    limit: int = Query(100, ge=1, le=1000, description="Limit jumlah data (default 100, max 1000)"),
    offset: int = Query(0, ge=0, description="Offset untuk pagination"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user)
) -> schemas.PaginatedResponse[schemas.MyReportResponse]:
    """
    Mendapatkan semua report/pelaporan pengisian bensin milik user
    
    - **vehicle_id**: Filter berdasarkan kendaraan tertentu (optional)
    - **limit**: Batasi jumlah data (default 100)
    - **offset**: Skip sejumlah data untuk pagination
    
    Returns:
    - List report dengan detail lengkap:
      - Info report (KodeUnik, Jumlah Liter, Rupiah, Waktu, Lokasi)
      - Info kendaraan (Nama, Plat, Tipe)
      - Info submission terkait (Status, Total)
      - Foto-foto bukti
    - Pagination info
    """
    reports, total = ReportService.get_my_reports(
        db,
        user_id=current_user.ID,  # type: ignore
        vehicle_id=vehicle_id,
        limit=limit,
        offset=offset
    )
    
    has_more = (offset + len(reports)) < total
    
    return schemas.PaginatedResponse[schemas.MyReportResponse](
        data=reports,  # type: ignore
        message=f"Ditemukan {len(reports)} dari {total} report",
        pagination={
            "total": total,
            "limit": limit,
            "offset": offset,
            "returned": len(reports),
            "has_more": has_more
        }
    )

@router.get("/my/reports/{report_id}", response_model=schemas.SuccessResponse[schemas.ReportDetailResponse])
def get_my_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.ReportDetailResponse]:
    """
    Mendapatkan detail lengkap sebuah report pengisian bensin
    
    - **report_id**: ID report yang ingin dilihat detailnya
    
    Returns:
    - Detail lengkap report termasuk:
      - Info user pelapor (Nama, NIP)
      - Info kendaraan lengkap (Nama, Plat, Merek, Kapasitas, dll)
      - Detail pengisian (Liter, Rupiah, Odometer, Lokasi)
      - Semua foto bukti (Kendaraan, Odometer, Invoice, MyPertamina)
      - Info submission terkait (Status, Total, Creator, Receiver)
    """
    report_detail = ReportService.get_report_detail(db, report_id, current_user.ID)  # type: ignore
    return schemas.SuccessResponse[schemas.ReportDetailResponse](
        data=report_detail,  # type: ignore
        message="Detail report berhasil ditemukan"
    )
