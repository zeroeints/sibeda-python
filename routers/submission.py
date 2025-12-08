from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import controller.auth as auth
import schemas.schemas as schemas
from database.database import get_db
from model.models import User as UserModel
from services.submission_service import SubmissionService

router = APIRouter(prefix="/submission", tags=["Submission"])


@router.get(
    "",
    response_model=schemas.SuccessResponse[schemas.PagedListData[schemas.SubmissionResponse]],
    summary="List Submissions (Paged)",
)
def list_submissions(
    creator_id: int | None = None,
    receiver_id: int | None = None,
    status: str | None = Query(None),
    dinas_id: int | None = Query(None, description="Filter by Dinas ID"),
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2000, le=2100),
    limit: int = Query(10, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.PagedListData[schemas.SubmissionResponse]]:
    
    result = SubmissionService.list(
        db, creator_id, receiver_id, status, month, year, dinas_id, limit, offset, current_user
    )
    return schemas.SuccessResponse[schemas.PagedListData[schemas.SubmissionResponse]](
        data=result, message="Data pengajuan berhasil diambil"
    )


@router.get(
    "/my/submissions",
    response_model=schemas.SuccessResponse[schemas.PagedListData[schemas.SubmissionResponse]],
    summary="Get My Submissions (Paged)",
)
def get_my_submissions(
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2000, le=2100),
    limit: int = Query(10, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.PagedListData[schemas.SubmissionResponse]]:
    result = SubmissionService.get_my_submissions(
        db, current_user.id, month, year, limit, offset
    )
    return schemas.SuccessResponse[schemas.PagedListData[schemas.SubmissionResponse]](
        data=result, message="Daftar pengajuan saya berhasil diambil"
    )


@router.get(
    "/{submission_id}",
    response_model=schemas.SuccessResponse[schemas.SubmissionResponse],
    summary="Get Submission Detail",
)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.SubmissionResponse]:
    s = SubmissionService.get(db, submission_id)
    if not s:
        raise HTTPException(status_code=404, detail="Submission tidak ditemukan")
    return schemas.SuccessResponse[schemas.SubmissionResponse](
        data=s, message="Success"
    )


@router.post(
    "",
    response_model=schemas.SuccessResponse[schemas.SubmissionResponse],
    summary="Create Submission",
)
def create_submission(
    payload: schemas.SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.SubmissionResponse]:
    created = SubmissionService.create(db, payload)
    return schemas.SuccessResponse[schemas.SubmissionResponse](
        data=created, message="Submission berhasil dibuat"
    )


@router.put(
    "/{submission_id}",
    response_model=schemas.SuccessResponse[schemas.SubmissionResponse],
    summary="Update Submission",
)
def update_submission(
    submission_id: int,
    payload: schemas.SubmissionUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.SubmissionResponse]:
    updated = SubmissionService.update(
        db, submission_id, payload, user_id=current_user.id
    )
    return schemas.SuccessResponse[schemas.SubmissionResponse](
        data=updated, message="Submission berhasil diupdate"
    )


@router.patch(
    "/{submission_id}",
    response_model=schemas.SuccessResponse[schemas.SubmissionResponse],
    summary="Patch Submission",
)
def patch_submission(
    submission_id: int,
    payload: schemas.SubmissionUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.SubmissionResponse]:
    updated = SubmissionService.update(
        db, submission_id, payload, user_id=current_user.id
    )
    return schemas.SuccessResponse[schemas.SubmissionResponse](
        data=updated, message="Submission berhasil diupdate"
    )


@router.delete(
    "/{submission_id}",
    response_model=schemas.SuccessResponse[schemas.Message],
    summary="Delete Submission",
)
def delete_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.Message]:
    SubmissionService.delete(db, submission_id)
    return schemas.SuccessResponse[schemas.Message](
        data=schemas.Message(detail="Submission dihapus"), message="Deleted"
    )


@router.get(
    "/monthly/summary",
    response_model=schemas.SuccessResponse[schemas.SubmissionSummary],
    summary="Get Monthly Summary Stats",
)
def get_monthly_summary(
    month: int = Query(...),
    year: int = Query(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.SubmissionSummary]:
    summary = SubmissionService.get_monthly_summary(db, month, year)
    return schemas.SuccessResponse[schemas.SubmissionSummary](
        data=summary, message="Ringkasan bulanan berhasil diambil"
    )


@router.get(
    "/monthly/details",
    response_model=schemas.SuccessListResponse[schemas.SubmissionResponse],
    summary="Get Monthly Details List (No Pagination)",
)
def get_monthly_details(
    month: int = Query(...),
    year: int = Query(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessListResponse[schemas.SubmissionResponse]:
    data = SubmissionService.get_monthly_details_optimized(db, month, year)
    return schemas.SuccessListResponse[schemas.SubmissionResponse](
        data=data, message=f"Detail pengajuan bulan {month}/{year} berhasil diambil"
    )