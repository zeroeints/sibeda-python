from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import controller.auth as auth
import schemas.schemas as schemas
from database.database import get_db
from i18n.messages import get_message
from model.models import User as UserModel
from services.vehicle_service import VehicleService

router = APIRouter(prefix="/vehicle", tags=["Vehicle"])


@router.get(
    "",
    response_model=schemas.SuccessResponse[schemas.PagedListData[schemas.VehicleResponse]],
    summary="List Vehicles (Paged)",
)
def list_vehicles(
    limit: int = Query(10, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.PagedListData[schemas.VehicleResponse]]:
    
    result = VehicleService.list(db, limit, offset)
    return schemas.SuccessResponse[schemas.PagedListData[schemas.VehicleResponse]](
        data=result, message="Success"
    )


@router.post(
    "",
    response_model=schemas.SuccessResponse[schemas.VehicleResponse],
    summary="Create Vehicle",
    description="Menambahkan kendaraan baru ke dalam sistem.",
)
def create_vehicle(
    payload: schemas.VehicleCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.VehicleResponse]:
    created = VehicleService.create(db, payload)
    return schemas.SuccessResponse[schemas.VehicleResponse](
        data=created, message=get_message("vehicle_create_success", None)
    )


@router.put(
    "/{vehicle_id}",
    response_model=schemas.SuccessResponse[schemas.VehicleResponse],
    summary="Update Vehicle",
    description="Memperbarui informasi kendaraan.",
)
def update_vehicle(
    vehicle_id: int,
    payload: schemas.VehicleCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.VehicleResponse]:
    v = VehicleService.update(db, vehicle_id, payload)
    return schemas.SuccessResponse[schemas.VehicleResponse](
        data=v, message=get_message("update_success", None)
    )


@router.patch(
    "/{vehicle_id}",
    response_model=schemas.SuccessResponse[schemas.VehicleResponse],
    summary="Patch Vehicle",
    description="Memperbarui informasi kendaraan secara parsial.",
)
def patch_vehicle(
    vehicle_id: int,
    payload: schemas.VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.VehicleResponse]:
    v = VehicleService.update(db, vehicle_id, payload)
    return schemas.SuccessResponse[schemas.VehicleResponse](
        data=v, message=get_message("update_success", None)
    )


@router.delete(
    "/{vehicle_id}",
    response_model=schemas.SuccessResponse[schemas.Message],
    summary="Delete Vehicle",
    description="Menghapus kendaraan dari sistem.",
)
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.Message]:
    VehicleService.delete(db, vehicle_id)
    return schemas.SuccessResponse[schemas.Message](
        data=schemas.Message(detail="Vehicle dihapus"),
        message=get_message("vehicle_delete_success", None),
    )


@router.get(
    "/my/vehicles",
    response_model=schemas.SuccessResponse[List[schemas.MyVehicleResponse]],
)
def get_my_vehicles(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
):
    vehicles = VehicleService.get_my_vehicles(db, current_user.ID)
    return schemas.SuccessResponse[List[schemas.MyVehicleResponse]](
        data=vehicles, message=f"Ditemukan {len(vehicles)} kendaraan milik anda"
    )


@router.get(
    "/user/{user_id}",
    response_model=schemas.SuccessResponse[List[schemas.VehicleResponse]],
    summary="Get Vehicles Assigned to User",
    description="Melihat daftar kendaraan yang di-assign ke user tertentu.",
)
def get_vehicles_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
):
    vehicles = VehicleService.get_by_user_id(db, user_id)
    return schemas.SuccessResponse[List[schemas.VehicleResponse]](
        data=vehicles, message=f"Ditemukan {len(vehicles)} kendaraan pada user {user_id}"
    )


@router.get(
    "/my/vehicles/{vehicle_id}",
    response_model=schemas.SuccessResponse[schemas.VehicleDetailResponse],
    summary="Get My Vehicle Detail",
    description="Detail kendaraan user termasuk riwayat 10 pengisian bensin terakhir.",
)
def get_my_vehicle_detail(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.VehicleDetailResponse]:
    vehicle_detail = VehicleService.get_vehicle_detail(db, vehicle_id, current_user.ID)
    return schemas.SuccessResponse[schemas.VehicleDetailResponse](
        data=vehicle_detail, message="Detail kendaraan berhasil ditemukan"
    )


@router.get(
    "/dinas/{dinas_id}",
    response_model=schemas.SuccessResponse[schemas.PagedListData[schemas.VehicleResponse]],
    summary="Get Vehicles by Dinas",
)
def get_vehicles_by_dinas(
    dinas_id: int,
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
):
    result = VehicleService.get_by_dinas(db, dinas_id, limit, offset)
    return schemas.SuccessResponse[schemas.PagedListData[schemas.VehicleResponse]](
        data=result,
        message=f"Ditemukan {result['stat']['total_data']} kendaraan dinas",
    )


@router.post(
    "/{vehicle_id}/assign",
    response_model=schemas.SuccessResponse[schemas.Message],
    summary="Assign User to Vehicle",
    description="Menambahkan user sebagai pemegang/pengguna kendaraan ini (Many-to-Many).",
)
def assign_user_to_vehicle(
    vehicle_id: int,
    payload: schemas.VehicleAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.Message]:
    VehicleService.assign_user(db, vehicle_id, payload.user_id) # snake_case schema
    return schemas.SuccessResponse[schemas.Message](
        data=schemas.Message(detail="User berhasil di-assign ke kendaraan"),
        message="Success",
    )


@router.post(
    "/{vehicle_id}/unassign",
    response_model=schemas.SuccessResponse[schemas.Message],
    summary="Unassign User from Vehicle",
    description="Menghapus user dari daftar pemegang kendaraan ini.",
)
def unassign_user_from_vehicle(
    vehicle_id: int,
    payload: schemas.VehicleAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessResponse[schemas.Message]:
    VehicleService.unassign_user(db, vehicle_id, payload.user_id) # snake_case schema
    return schemas.SuccessResponse[schemas.Message](
        data=schemas.Message(detail="User berhasil di-unassign dari kendaraan"),
        message="Success",
    )