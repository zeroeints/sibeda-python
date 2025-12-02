from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import controller.auth as auth
import schemas.schemas as schemas
from database.database import get_db
from model.models import User as UserModel
from services.dinas_service import DinasService

router = APIRouter(prefix="/dinas", tags=["Dinas"])


@router.get(
    "",
    response_model=schemas.SuccessListResponse[schemas.DinasResponse],
    summary="List Dinas",
    description="Mendapatkan daftar seluruh Dinas/Instansi.",
)
def read_dinas(
    db: Session = Depends(get_db),
) -> schemas.SuccessListResponse[schemas.DinasResponse]:
    data = DinasService.list(db)
    return schemas.SuccessListResponse[schemas.DinasResponse](data=data)


@router.post(
    "",
    response_model=schemas.SuccessResponse[schemas.DinasResponse],
    summary="Create Dinas",
    description="Membuat data Dinas baru.",
)
def create_dinas(
    dinas: schemas.DinasBase,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.DinasResponse]:
    created = DinasService.create(db, dinas)
    return schemas.SuccessResponse[schemas.DinasResponse](data=created)


@router.delete(
    "/{dinas_id}",
    response_model=schemas.SuccessResponse[schemas.Message],
    summary="Delete Dinas",
    description="Menghapus data Dinas.",
)
def delete_dinas(
    dinas_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.Message]:
    DinasService.delete(db, dinas_id)
    return schemas.SuccessResponse[schemas.Message](
        data=schemas.Message(detail="Dinas berhasil dihapus")
    )