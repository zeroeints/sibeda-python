from __future__ import annotations

from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from sqlalchemy.orm import Session

import controller.auth as auth
import schemas.schemas as schemas
from database.database import get_db
from i18n.messages import get_message
from model.models import User as UserModel
from services.report_service import ReportService

router = APIRouter(prefix="/report", tags=["Report"])


@router.get(
    "",
    response_model=schemas.SuccessResponse[schemas.PagedListData[schemas.ReportResponse]],
    summary="List Reports (Paged)",
)
def list_reports(
    user_id: int | None = None,
    vehicle_id: int | None = None,
    status: str | None = Query(None),
    dinas_id: int | None = Query(None, description="Filter by Dinas ID"),
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2000, le=2100),
    limit: int = Query(10, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.PagedListData[schemas.ReportResponse]]:
    
    result = ReportService.list(
        db, user_id, vehicle_id, month, year, dinas_id, limit, offset, current_user, status
    )
    return schemas.SuccessResponse[schemas.PagedListData[schemas.ReportResponse]](
        data=result, message="Data report berhasil diambil"
    )


@router.get(
    "/my/reports",
    response_model=schemas.SuccessResponse[schemas.PagedListData[schemas.MyReportResponse]],
    summary="Get My Reports (Paged)",
)
def get_my_reports(
    vehicle_id: int | None = None,
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2000, le=2100),
    limit: int = Query(10, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.PagedListData[schemas.MyReportResponse]]:
    
    result = ReportService.get_my_reports(
        db, current_user.id, vehicle_id, month, year, limit, offset
    )
    return schemas.SuccessResponse[schemas.PagedListData[schemas.MyReportResponse]](
        data=result, message="Daftar laporan saya berhasil diambil"
    )


@router.get(
    "/{report_id}",
    response_model=schemas.SuccessResponse[schemas.ReportResponse],
    summary="Get Report",
    description="Mendapatkan satu report berdasarkan ID.",
)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.ReportResponse]:
    r = ReportService.get(db, report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Report tidak ditemukan")
    return schemas.SuccessResponse[schemas.ReportResponse](
        data=r, message=get_message("create_success", None)
    )


@router.post(
    "",
    response_model=schemas.SuccessResponse[schemas.ReportResponse],
    summary="Create Report with Photos",
    description="Membuat laporan penggunaan dana/BBM dengan upload bukti foto.",
)
async def create_report(
    kode_unik: str = Form(...),
    user_id: int = Form(...),
    vehicle_id: int = Form(...),
    amount_rupiah: float = Form(...),
    amount_liter: float = Form(...),
    description: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    odometer: Optional[int] = Form(None),
    vehicle_physical_photo: Optional[UploadFile] = File(None),
    odometer_photo: Optional[UploadFile] = File(None),
    invoice_photo: Optional[UploadFile] = File(None),
    my_pertamina_photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.ReportResponse]:
    created = await ReportService.create_with_upload(
        db=db,
        kode_unik=kode_unik,
        user_id=user_id,
        vehicle_id=vehicle_id,
        amount_rupiah=amount_rupiah,
        amount_liter=amount_liter,
        description=description,
        latitude=latitude,
        longitude=longitude,
        odometer=odometer,
        vehicle_photo=vehicle_physical_photo,
        odometer_photo=odometer_photo,
        invoice_photo=invoice_photo,
        mypertamina_photo=my_pertamina_photo,
    )
    return schemas.SuccessResponse[schemas.ReportResponse](
        data=created, message="Report berhasil dibuat dengan foto"
    )


@router.patch(
    "/{report_id}",
    response_model=schemas.SuccessResponse[schemas.ReportResponse],
    summary="Update Report",
    description="Mengupdate data report, termasuk mengganti foto bukti jika diperlukan.",
)
async def update_report(
    report_id: int,
    kode_unik: Optional[str] = Form(None),
    user_id: Optional[int] = Form(None),
    vehicle_id: Optional[int] = Form(None),
    amount_rupiah: Optional[float] = Form(None),
    amount_liter: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    odometer: Optional[int] = Form(None),
    vehicle_physical_photo: Optional[UploadFile] = File(None),
    odometer_photo: Optional[UploadFile] = File(None),
    invoice_photo: Optional[UploadFile] = File(None),
    my_pertamina_photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.ReportResponse]:
    # Note: ReportService.update_with_upload needs to be defined in your service
    # assuming it accepts similar args to create
    updated = await ReportService.update_with_upload(
        db=db,
        report_id=report_id,
        kode_unik=kode_unik,
        user_id=user_id,
        vehicle_id=vehicle_id,
        amount_rupiah=amount_rupiah,
        amount_liter=amount_liter,
        description=description,
        latitude=latitude,
        longitude=longitude,
        odometer=odometer,
        vehicle_photo=vehicle_physical_photo,
        odometer_photo=odometer_photo,
        invoice_photo=invoice_photo,
        mypertamina_photo=my_pertamina_photo,
    )
    return schemas.SuccessResponse[schemas.ReportResponse](
        data=updated, message="Report berhasil diupdate"
    )


@router.delete(
    "/{report_id}",
    response_model=schemas.SuccessResponse[schemas.Message],
    summary="Delete Report",
    description="Menghapus report secara permanen.",
)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.Message]:
    ReportService.delete(db, report_id)
    return schemas.SuccessResponse[schemas.Message](
        data=schemas.Message(detail="Report dihapus"),
        message=get_message("report_delete_success", None),
    )


@router.get(
    "/my/reports/{report_id}",
    response_model=schemas.SuccessResponse[schemas.ReportResponse],
    summary="Get My Report Detail",
)
def get_my_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.ReportResponse]:
    r = ReportService.get(db, report_id)
    if not r:
        raise HTTPException(404, "Report tidak ditemukan")

    if r.user_id != current_user.id:
        raise HTTPException(403, "Bukan laporan anda")

    return schemas.SuccessResponse[schemas.ReportResponse](
        data=r, message="Detail report ditemukan"
    )


@router.put(
    "/{report_id}/status",
    response_model=schemas.SuccessResponse[schemas.ReportResponse],
    summary="Update Report Status",
    description="Mengubah status report (Approve/Reject) oleh Admin/Kadis.",
)
def update_report_status(
    report_id: int,
    status_update: schemas.ReportStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.ReportResponse]:
    updated_report = ReportService.update_status(
        db=db,
        report_id=report_id,
        new_status=status_update.status.value,
        updated_by_user_id=current_user.id,  # type: ignore
        notes=status_update.notes,
    )
    return schemas.SuccessResponse[schemas.ReportResponse](
        data=updated_report,
        message=f"Status report berhasil diubah menjadi {status_update.status.value}",
    )


@router.patch(
    "/{report_id}/status",
    response_model=schemas.SuccessResponse[schemas.ReportResponse],
    summary="Patch Report Status",
)
def patch_report_status(
    report_id: int,
    status_update: schemas.ReportStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.ReportResponse]:
    return update_report_status(report_id, status_update, db, current_user)


@router.get(
    "/{report_id}/logs",
    response_model=schemas.SuccessListResponse[schemas.ReportLogResponse],
    summary="Get Report Logs",
)
def get_report_logs(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessListResponse[schemas.ReportLogResponse]:
    logs = ReportService.get_report_logs(db, report_id)
    return schemas.SuccessListResponse[schemas.ReportLogResponse](
        data=logs, message=f"Ditemukan {len(logs)} log entries"
    )