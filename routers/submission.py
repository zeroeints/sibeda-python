from fastapi import APIRouter, Depends, HTTPException
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


@router.get("/", response_model=schemas.SuccessListResponse[schemas.SubmissionResponse])
def list_submissions(
    creator_id: int | None = None,
    receiver_id: int | None = None,
    vehicle_id: int | None = None,
    db: Session = Depends(get_db),
    _user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessListResponse[schemas.SubmissionResponse]:
    data = SubmissionService.list(db, creator_id=creator_id, receiver_id=receiver_id, vehicle_id=vehicle_id)
    return schemas.SuccessListResponse[schemas.SubmissionResponse](data=data, message=get_message("create_success", None))


@router.get("/{submission_id}", response_model=schemas.SuccessResponse[schemas.SubmissionResponse])
def get_submission(submission_id: int, db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.SubmissionResponse]:
    s = SubmissionService.get(db, submission_id)
    if not s:
        raise HTTPException(status_code=404, detail="Submission tidak ditemukan")
    return schemas.SuccessResponse[schemas.SubmissionResponse](data=s, message=get_message("create_success", None))


@router.post("/", response_model=schemas.SuccessResponse[schemas.SubmissionResponse])
def create_submission(payload: schemas.SubmissionCreate, db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.SubmissionResponse]:
    created = SubmissionService.create(db, payload)
    return schemas.SuccessResponse[schemas.SubmissionResponse](data=created, message=get_message("create_success", None))


@router.put("/{submission_id}", response_model=schemas.SuccessResponse[schemas.SubmissionResponse])
def update_submission(submission_id: int, payload: schemas.SubmissionUpdate, db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.SubmissionResponse]:
    updated = SubmissionService.update(db, submission_id, payload)
    return schemas.SuccessResponse[schemas.SubmissionResponse](data=updated, message=get_message("update_success", None))


@router.delete("/{submission_id}", response_model=schemas.SuccessResponse[schemas.Message])
def delete_submission(submission_id: int, db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.Message]:
    SubmissionService.delete(db, submission_id)
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="Submission dihapus"), message=get_message("delete_success", None))
