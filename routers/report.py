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

@router.get(
    "", 
    response_model=schemas.SuccessResponse[schemas.PagedListData[schemas.ReportResponse]],
    summary="List Reports (Paged)"
)
def list_reports(
    user_id: int | None = None, 
    vehicle_id: int | None = None, 
    dinas_id: int | None = Query(None, description="Filter by Dinas ID"), # [UPDATED] Param baru
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2000, le=2100),
    limit: int = Query(10, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db), 
    _u: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.PagedListData[schemas.ReportResponse]]:
    
    result = ReportService.list(
        db, user_id, vehicle_id, month, year, dinas_id, limit, offset
    )
    return schemas.SuccessResponse[schemas.PagedListData[schemas.ReportResponse]](
        data=result, 
        message="Data report berhasil diambil"
    )

@router.get(
    "/my/reports",
    response_model=schemas.SuccessResponse[schemas.PagedListData[schemas.MyReportResponse]],
    summary="Get My Reports (Paged)"
)
def get_my_reports(
    vehicle_id: int | None = None,
    month: int | None = Query(None, ge=1, le=12), # [UPDATED] Param baru
    year: int | None = Query(None, ge=2000, le=2100), # [UPDATED] Param baru
    limit: int = Query(10, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _u: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.PagedListData[schemas.MyReportResponse]]:
    result = ReportService.get_my_reports(db, _u.ID, vehicle_id, month, year, limit, offset)
    return schemas.SuccessResponse[schemas.PagedListData[schemas.MyReportResponse]](
        data=result,
        message="Daftar laporan saya berhasil diambil"
    )
@router.get(
    "/{report_id}", 
    response_model=schemas.SuccessResponse[schemas.ReportResponse],
    summary="Get Report",
    description="Mendapatkan satu report berdasarkan ID."
)
def get_report(report_id: int, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.ReportResponse]:
    r = ReportService.get(db, report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Report tidak ditemukan")
    return schemas.SuccessResponse[schemas.ReportResponse](data=r, message=get_message("create_success", None))

@router.post(
    "", 
    response_model=schemas.SuccessResponse[schemas.ReportResponse],
    summary="Create Report with Photos",
    description="Membuat laporan penggunaan dana/BBM dengan mengupload bukti foto (Fisik, Odometer, Struk, MyPertamina)."
)
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
    created = await ReportService.create_with_upload(
        db=db, kode_unik=KodeUnik, user_id=UserID, vehicle_id=VehicleID,
        amount_rupiah=AmountRupiah, amount_liter=AmountLiter, description=Description,
        latitude=Latitude, longitude=Longitude, odometer=Odometer,
        vehicle_photo=VehiclePhysicalPhoto, odometer_photo=OdometerPhoto,
        invoice_photo=InvoicePhoto, mypertamina_photo=MyPertaminaPhoto
    )
    return schemas.SuccessResponse[schemas.ReportResponse](data=created, message="Report berhasil dibuat dengan foto")

@router.patch(
    "/{report_id}", 
    response_model=schemas.SuccessResponse[schemas.ReportResponse],
    summary="Update Report",
    description="Mengupdate data report, termasuk mengganti foto bukti jika diperlukan."
)
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
    updated = await ReportService.update_with_upload(
        db=db, report_id=report_id, kode_unik=KodeUnik, user_id=UserID, vehicle_id=VehicleID,
        amount_rupiah=AmountRupiah, amount_liter=AmountLiter, description=Description,
        latitude=Latitude, longitude=Longitude, odometer=Odometer,
        vehicle_photo=VehiclePhysicalPhoto, odometer_photo=OdometerPhoto,
        invoice_photo=InvoicePhoto, mypertamina_photo=MyPertaminaPhoto
    )
    return schemas.SuccessResponse[schemas.ReportResponse](data=updated, message="Report berhasil diupdate")

@router.delete(
    "/{report_id}", 
    response_model=schemas.SuccessResponse[schemas.Message],
    summary="Delete Report",
    description="Menghapus report secara permanen."
)
def delete_report(report_id: int, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.Message]:
    ReportService.delete(db, report_id)
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="Report dihapus"), message=get_message("report_delete_success", None))


@router.get(
    "/my/reports/{report_id}", 
    response_model=schemas.SuccessResponse[schemas.ReportResponse], # Bisa ReportResponse biasa karena detail tidak butuh extra field list
    summary="Get My Report Detail"
)
def get_my_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.ReportResponse]:
    # Reuse get() standard karena detail submission sudah ada di schema jika menggunakan joinedload
    # Jika Anda ingin nested submission penuh, gunakan ReportDetailResponse di schema
    r = ReportService.get(db, report_id)
    if not r: raise HTTPException(404, "Report tidak ditemukan")
    
    # Validasi kepemilikan
    if r.UserID != current_user.ID:
        raise HTTPException(403, "Bukan laporan anda")
        
    return schemas.SuccessResponse[schemas.ReportResponse](data=r, message="Detail report ditemukan")

@router.put(
    "/{report_id}/status", 
    response_model=schemas.SuccessResponse[schemas.ReportResponse],
    summary="Update Report Status",
    description="Mengubah status report (Approve/Reject) oleh Admin/Kadis. Otomatis membuat log."
)
def update_report_status(
    report_id: int,
    status_update: schemas.ReportStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.ReportResponse]:
    updated_report = ReportService.update_status(
        db=db, report_id=report_id, new_status=status_update.Status,
        updated_by_user_id=current_user.ID, notes=status_update.Notes # type: ignore
    )
    return schemas.SuccessResponse[schemas.ReportResponse](
        data=updated_report, # type: ignore
        message=f"Status report berhasil diubah menjadi {status_update.Status.value}"
    )

@router.patch(
    "/{report_id}/status", 
    response_model=schemas.SuccessResponse[schemas.ReportResponse],
    summary="Patch Report Status",
    description="Alias untuk mengubah status report."
)
def patch_report_status(
    report_id: int,
    status_update: schemas.ReportStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.ReportResponse]:
    return update_report_status(report_id, status_update, db, current_user)

@router.get(
    "/{report_id}/logs", 
    response_model=schemas.SuccessResponse[schemas.ReportLogResponse],
    summary="Get Report Logs",
    description="Melihat riwayat perubahan status pada sebuah laporan."
)
def get_report_logs(
    report_id: int,
    db: Session = Depends(get_db),
    _u: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.ReportLogResponse]:
    logs = ReportService.get_report_logs(db, report_id)
    return schemas.SuccessResponse[schemas.ReportLogResponse](data=logs, message=f"Ditemukan {len(logs)} log entries") # type: ignore