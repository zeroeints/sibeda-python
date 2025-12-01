# pyright: reportGeneralTypeIssues=false, reportUnknownMemberType=false
# type: ignore
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from database.database import SessionLocal
import controller.auth as auth
import schemas.schemas as schemas
from model.models import User as UserModel, ReportStatusEnum
from services.report_service import ReportService
from i18n.messages import get_message
from typing import Optional

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
async def create_report(
    KodeUnik: str = Form(...),
    UserID: int = Form(...),
    VehicleID: int = Form(...),
    AmountRupiah: float = Form(...),
    AmountLiter: float = Form(...),
    Description: Optional[str] = Form(None),
    Latitude: Optional[float] = Form(None),
    Longitude: Optional[float] = Form(None),
    Odometer: Optional[int] = Form(None),
    VehiclePhysicalPhoto: Optional[UploadFile] = File(None),
    OdometerPhoto: Optional[UploadFile] = File(None),
    InvoicePhoto: Optional[UploadFile] = File(None),
    MyPertaminaPhoto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _u: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.ReportResponse]:
    """
    Create report dengan upload foto
    
    Request:
    - Form Data (multipart/form-data)
    - Files (optional):
      - VehiclePhysicalPhoto: Foto fisik kendaraan
      - OdometerPhoto: Foto odometer
      - InvoicePhoto: Foto invoice/struk
      - MyPertaminaPhoto: Foto MyPertamina
    
    Response:
    - Report baru dengan path foto tersimpan di database
    - Foto tersimpan di folder assets/reports/
    """
    created = await ReportService.create_with_upload(
        db=db,
        kode_unik=KodeUnik,
        user_id=UserID,
        vehicle_id=VehicleID,
        amount_rupiah=AmountRupiah,
        amount_liter=AmountLiter,
        description=Description,
        latitude=Latitude,
        longitude=Longitude,
        odometer=Odometer,
        vehicle_photo=VehiclePhysicalPhoto,
        odometer_photo=OdometerPhoto,
        invoice_photo=InvoicePhoto,
        mypertamina_photo=MyPertaminaPhoto
    )
    return schemas.SuccessResponse[schemas.ReportResponse](
        data=created,
        message="Report berhasil dibuat dengan foto"
    )

@router.patch("/{report_id}", response_model=schemas.SuccessResponse[schemas.ReportResponse])
async def update_report(
    report_id: int,
    KodeUnik: Optional[str] = Form(None),
    UserID: Optional[int] = Form(None),
    VehicleID: Optional[int] = Form(None),
    AmountRupiah: Optional[float] = Form(None),
    AmountLiter: Optional[float] = Form(None),
    Description: Optional[str] = Form(None),
    Latitude: Optional[float] = Form(None),
    Longitude: Optional[float] = Form(None),
    Odometer: Optional[int] = Form(None),
    VehiclePhysicalPhoto: Optional[UploadFile] = File(None),
    OdometerPhoto: Optional[UploadFile] = File(None),
    InvoicePhoto: Optional[UploadFile] = File(None),
    MyPertaminaPhoto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _u: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.ReportResponse]:
    """
    Update report (partial update) dengan opsi upload foto baru
    
    Request:
    - Form Data (multipart/form-data)
    - Semua field optional
    - Files (optional):
      - VehiclePhysicalPhoto: Foto fisik kendaraan baru
      - OdometerPhoto: Foto odometer baru
      - InvoicePhoto: Foto invoice/struk baru
      - MyPertaminaPhoto: Foto MyPertamina baru
    
    Response:
    - Report yang sudah diupdate
    """
    updated = await ReportService.update_with_upload(
        db=db,
        report_id=report_id,
        kode_unik=KodeUnik,
        user_id=UserID,
        vehicle_id=VehicleID,
        amount_rupiah=AmountRupiah,
        amount_liter=AmountLiter,
        description=Description,
        latitude=Latitude,
        longitude=Longitude,
        odometer=Odometer,
        vehicle_photo=VehiclePhysicalPhoto,
        odometer_photo=OdometerPhoto,
        invoice_photo=InvoicePhoto,
        mypertamina_photo=MyPertaminaPhoto
    )
    return schemas.SuccessResponse[schemas.ReportResponse](
        data=updated,
        message="Report berhasil diupdate"
    )

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
      - History logs perubahan status
    """
    report_detail = ReportService.get_report_detail(db, report_id, current_user.ID)  # type: ignore
    return schemas.SuccessResponse[schemas.ReportDetailResponse](
        data=report_detail,  # type: ignore
        message="Detail report berhasil ditemukan"
    )

@router.put("/{report_id}/status", response_model=schemas.SuccessResponse[schemas.ReportResponse])
def update_report_status(
    report_id: int,
    status_update: schemas.ReportStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.ReportResponse]:
    """
    Update status report (untuk Admin/Kepala Dinas)
    
    - **report_id**: ID report yang akan diupdate statusnya
    - **Status**: Status baru (Pending, Reviewed, Accepted, Rejected)
    - **Notes**: Catatan optional untuk perubahan status
    
    Returns:
    - Report yang sudah diupdate
    - Otomatis membuat log entry untuk tracking history
    """
    updated_report = ReportService.update_status(
        db=db,
        report_id=report_id,
        new_status=status_update.Status,
        updated_by_user_id=current_user.ID,  # type: ignore
        notes=status_update.Notes
    )
    return schemas.SuccessResponse[schemas.ReportResponse](
        data=updated_report,  # type: ignore
        message=f"Status report berhasil diubah menjadi {status_update.Status.value}"
    )

@router.get("/{report_id}/logs", response_model=schemas.SuccessListResponse[schemas.ReportLogResponse])
def get_report_logs(
    report_id: int,
    db: Session = Depends(get_db),
    _u: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessListResponse[schemas.ReportLogResponse]:
    """
    Mendapatkan history log perubahan status report
    
    - **report_id**: ID report yang ingin dilihat historynya
    
    Returns:
    - List semua perubahan status dengan detail:
      - Status
      - Timestamp
      - User yang melakukan perubahan
      - Catatan perubahan
    """
    logs = ReportService.get_report_logs(db, report_id)
    return schemas.SuccessListResponse[schemas.ReportLogResponse](
        data=logs,  # type: ignore
        message=f"Ditemukan {len(logs)} log entries untuk report #{report_id}"
    )

