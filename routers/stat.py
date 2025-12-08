from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import controller.auth as auth
import schemas.schemas as schemas
from database.database import get_db
from model.models import User as UserModel
from services.stat_service import StatService

router = APIRouter(prefix="/stat", tags=["Statistics"])


@router.get(
    "/pic",
    response_model=schemas.SuccessResponse[schemas.PicStatResponse],
    summary="Get PIC Dashboard Statistics",
)
def get_pic_stats(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.PicStatResponse]:
    data = StatService.get_pic_stats(db, current_user.id)
    return schemas.SuccessResponse[schemas.PicStatResponse](
        data=data, message="Statistik PIC berhasil diambil"
    )


@router.get(
    "/kadis",
    response_model=schemas.SuccessResponse[schemas.KadisStatResponse],
    summary="Get Kepala Dinas Dashboard Statistics",
)
def get_kadis_stats(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.KadisStatResponse]:
    if not current_user.dinas_id:
        raise HTTPException(
            status_code=400, detail="User tidak terdaftar dalam dinas manapun"
        )

    data = StatService.get_kadis_stats(db, current_user.dinas_id)
    return schemas.SuccessResponse[schemas.KadisStatResponse](
        data=data, message="Statistik Kadis berhasil diambil"
    )


@router.get(
    "/admin",
    response_model=schemas.SuccessResponse[schemas.AdminStatResponse],
    summary="Get Admin Dashboard Statistics",
)
def get_admin_stats(
    dinas_id: int | None = Query(None, description="ID Dinas target."),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.AdminStatResponse]:
    target_dinas = dinas_id if dinas_id else current_user.dinas_id
    
    if not target_dinas:
        raise HTTPException(status_code=400, detail="Harap spesifikasikan dinas_id")

    data = StatService.get_admin_stats(db, target_dinas)
    return schemas.SuccessResponse[schemas.AdminStatResponse](
        data=data, message="Statistik Admin berhasil diambil"
    )