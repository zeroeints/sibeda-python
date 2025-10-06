from fastapi import APIRouter, Depends, HTTPException
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

@router.post("/", response_model=schemas.SuccessResponse[schemas.ReportResponse])
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
