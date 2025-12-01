# pyright: reportGeneralTypeIssues=false, reportUnknownMemberType=false
# type: ignore
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.database import SessionLocal
import controller.auth as auth
import schemas.schemas as schemas
from model.models import User as UserModel
from services.submission_service import SubmissionService
from i18n.messages import get_message

router = APIRouter(prefix="/submission", tags=["Submission"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get(
    "/", 
    response_model=schemas.SuccessListResponse[schemas.SubmissionResponse],
    summary="List Submissions",
    description="Mendapatkan daftar submission lengkap dengan objek nested User."
)
def list_submissions(
    creator_id: int | None = None,
    receiver_id: int | None = None,
    # VehicleID filter removed
    status: str | None = Query(None),
    limit: int | None = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessListResponse[schemas.SubmissionResponse]:
    data = SubmissionService.list(db, creator_id, receiver_id, status=status, limit=limit, offset=offset)
    return schemas.SuccessListResponse[schemas.SubmissionResponse](
        data=data, 
        message=f"Ditemukan {len(data)} submission"
    )

@router.get(
    "/{submission_id}", 
    response_model=schemas.SuccessResponse[schemas.SubmissionResponse],
    summary="Get Submission"
)
def get_submission(submission_id: int, db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.SubmissionResponse]:
    s = SubmissionService.get(db, submission_id)
    if not s:
        raise HTTPException(status_code=404, detail="Submission tidak ditemukan")
    return schemas.SuccessResponse[schemas.SubmissionResponse](data=s, message="Success")

@router.post(
    "/", 
    response_model=schemas.SuccessResponse[schemas.SubmissionResponse],
    summary="Create Submission"
)
def create_submission(payload: schemas.SubmissionCreate, db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.SubmissionResponse]:
    created = SubmissionService.create(db, payload)
    return schemas.SuccessResponse[schemas.SubmissionResponse](data=created, message="Created")

@router.put(
    "/{submission_id}", 
    response_model=schemas.SuccessResponse[schemas.SubmissionResponse],
    summary="Update Submission"
)
def update_submission(
    submission_id: int, 
    payload: schemas.SubmissionUpdate, 
    db: Session = Depends(get_db), 
    _user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.SubmissionResponse]:
    updated = SubmissionService.update(db, submission_id, payload, user_id=_user.ID)
    return schemas.SuccessResponse[schemas.SubmissionResponse](data=updated, message="Updated")

@router.delete(
    "/{submission_id}", 
    response_model=schemas.SuccessResponse[schemas.Message],
    summary="Delete Submission"
)
def delete_submission(submission_id: int, db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.Message]:
    SubmissionService.delete(db, submission_id)
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="Submission dihapus"), message="Deleted")

@router.get(
    "/monthly/summary", 
    response_model=schemas.SuccessResponse[schemas.SubmissionSummary]
)
def get_monthly_summary(
    month: int = Query(...),
    year: int = Query(...),
    db: Session = Depends(get_db),
    _user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.SubmissionSummary]:
    summary = SubmissionService.get_monthly_summary(db, month, year)
    return schemas.SuccessResponse[schemas.SubmissionSummary](data=summary, message="Summary")

@router.get(
    "/monthly/details", 
    response_model=schemas.SuccessListResponse[schemas.SubmissionResponse] 
)
def get_monthly_details(
    month: int = Query(...),
    year: int = Query(...),
    db: Session = Depends(get_db),
    _user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessListResponse[schemas.SubmissionResponse]:
    all_subs = SubmissionService.list(db)
    filtered = [s for s in all_subs if s.created_at.month == month and s.created_at.year == year]
    return schemas.SuccessListResponse[schemas.SubmissionResponse](
        data=filtered,
        message=f"Detail pengajuan bulan {month}/{year}"
    )