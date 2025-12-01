# pyright: reportGeneralTypeIssues=false, reportUnknownMemberType=false
# type: ignore
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from database.database import SessionLocal
import controller.auth as auth
import schemas.schemas as schemas
from model.models import User as UserModel
from services.report_service import ReportService
from typing import Optional

router = APIRouter(prefix="/report", tags=["Report"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get(
    "/", 
    response_model=schemas.SuccessListResponse[schemas.ReportResponse],
    summary="List Reports"
)
def list_reports(
    user_id: int | None = None, 
    vehicle_id: int | None = None, 
    db: Session = Depends(get_db), 
    _u: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessListResponse[schemas.ReportResponse]:
    data = ReportService.list(db, user_id=user_id, vehicle_id=vehicle_id)
    return schemas.SuccessListResponse[schemas.ReportResponse](data=data, message="Success")

@router.get(
    "/{report_id}", 
    response_model=schemas.SuccessResponse[schemas.ReportResponse],
    summary="Get Report"
)
def get_report(report_id: int, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.ReportResponse]:
    r = ReportService.get(db, report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Report tidak ditemukan")
    return schemas.SuccessResponse[schemas.ReportResponse](data=r, message="Success")

@router.post(
    "", 
    response_model=schemas.SuccessResponse[schemas.ReportResponse]
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
        db, KodeUnik, UserID, VehicleID, AmountRupiah, AmountLiter, Description,
        Latitude, Longitude, Odometer, VehiclePhysicalPhoto, OdometerPhoto,
        InvoicePhoto, MyPertaminaPhoto
    )
    return schemas.SuccessResponse[schemas.ReportResponse](data=created, message="Created")

@router.put(
    "/{report_id}/status", 
    response_model=schemas.SuccessResponse[schemas.ReportResponse]
)
def update_report_status(
    report_id: int,
    status_update: schemas.ReportStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.ReportResponse]:
    updated = ReportService.update_status(
        db, report_id, status_update.Status, current_user.ID, status_update.Notes
    )
    return schemas.SuccessResponse[schemas.ReportResponse](data=updated, message="Updated")