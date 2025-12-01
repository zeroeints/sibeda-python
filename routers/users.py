# pyright: reportGeneralTypeIssues=false, reportUnknownMemberType=false
# type: ignore
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import controller.auth as auth
import schemas.schemas as schemas
from database.database import SessionLocal
from model.models import User as UserModel
from services.user_service import UserService
from config import get_settings
from i18n.messages import get_message

router = APIRouter(prefix="/users", tags=["Users"]) 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/", 
    response_model=schemas.SuccessResponse[schemas.UserResponse],
    summary="Register New User",
    description="Mendaftarkan pengguna baru ke dalam sistem. OTP verifikasi akan dikirimkan ke email."
)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)) -> schemas.SuccessResponse[schemas.UserResponse]:
    settings = get_settings()
    created = UserService.create(db, user)
    msg = get_message("user_create_success", None)
    if settings.debug and hasattr(created, "_registration_otp"):
        msg = f"{msg} | OTP={getattr(created, '_registration_otp')}"
    return schemas.SuccessResponse[schemas.UserResponse](data=created, message=msg)

@router.post(
    "/register", 
    response_model=schemas.SuccessResponse[schemas.UserResponse],
    summary="Register Alias",
    description="Alias untuk endpoint registrasi user."
)
def register_user_alias(user: schemas.UserCreate, db: Session = Depends(get_db)) -> schemas.SuccessResponse[schemas.UserResponse]:
    return register_user(user, db)

@router.get(
    "/", 
    response_model=schemas.SuccessListResponse[schemas.UserResponse],
    summary="List Users",
    description="Mendapatkan daftar pengguna dengan pagination sederhana."
)
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), _current_user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessListResponse[schemas.UserResponse]:
    users = UserService.list(db, skip=skip, limit=limit)
    return schemas.SuccessListResponse[schemas.UserResponse](data=users, message=get_message("create_success", None))

@router.get(
    "/{user_id}", 
    response_model=schemas.SuccessResponse[schemas.UserResponse],
    summary="Get User Detail",
    description="Mendapatkan informasi dasar pengguna berdasarkan ID."
)
def get_user(user_id: int, db: Session = Depends(get_db), _current_user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.UserResponse]:
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return schemas.SuccessResponse[schemas.UserResponse](data=user, message="User berhasil ditemukan")

@router.put(
    "/{user_id}", 
    response_model=schemas.SuccessResponse[schemas.UserResponse],
    summary="Update User",
    description="Memperbarui data pengguna. Hanya field yang dikirim yang akan diupdate."
)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db), _current_user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.UserResponse]:
    updated_user = UserService.update(db, user_id, user_update)
    return schemas.SuccessResponse[schemas.UserResponse](data=updated_user, message=get_message("update_success", None))

@router.patch(
    "/{user_id}", 
    response_model=schemas.SuccessResponse[schemas.UserResponse],
    summary="Patch User",
    description="Alias untuk update user (metode PATCH)."
)
def patch_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db), _current_user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.UserResponse]:
    return update_user(user_id, user_update, db, _current_user)

@router.get(
    "/stats/count-by-dinas", 
    response_model=schemas.SuccessListResponse[schemas.UserCountByDinas],
    summary="Count Users per Dinas",
    description="Mendapatkan statistik jumlah pengguna yang terdaftar di setiap dinas."
)
def get_user_count_by_dinas(db: Session = Depends(get_db), _current_user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessListResponse[schemas.UserCountByDinas]:
    user_counts = UserService.get_user_count_by_dinas(db)
    return schemas.SuccessListResponse[schemas.UserCountByDinas](
        data=user_counts, 
        message="Berhasil mendapatkan total pengguna per dinas"
    )

@router.get(
    "/balance/{user_id}", 
    response_model=schemas.SuccessResponse[schemas.UserBalanceResponse],
    summary="Get User Balance",
    description="Mendapatkan saldo dompet pengguna beserta informasi lengkap User dan Dinas terkait."
)
def get_user_balance(
    user_id: int,
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.UserBalanceResponse]:
    balance_info = UserService.get_user_balance(db, user_id)
    return schemas.SuccessResponse[schemas.UserBalanceResponse](
        data=balance_info,  # type: ignore
        message="Berhasil mendapatkan saldo user"
    )

@router.get(
    "/detailed/search", 
    response_model=schemas.PaginatedResponse[schemas.UserDetailResponse],
    summary="Search Users Detailed",
    description="Mencari pengguna dengan filter lengkap (role, dinas, status) dan mendapatkan detail wallet serta statistik submission."
)
def search_users_detailed(
    search: str | None = Query(None, description="Cari berdasarkan NIP, Nama, atau Email"),
    role: str | None = Query(None, description="Filter berdasarkan role: admin, kepala_dinas, pic"),
    dinas_id: int | None = Query(None, description="Filter berdasarkan ID dinas"),
    is_verified: bool | None = Query(None, description="Filter berdasarkan status verifikasi"),
    limit: int = Query(100, ge=1, le=1000, description="Limit jumlah data"),
    offset: int = Query(0, ge=0, description="Offset pagination"),
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(auth.get_current_user)
) -> schemas.PaginatedResponse[schemas.UserDetailResponse]:
    
    total = UserService.count_users(
        db,
        search=search,
        role=role,
        dinas_id=dinas_id,
        is_verified=is_verified
    )
    
    data = UserService.search_users_detailed(
        db,
        search=search,
        role=role,
        dinas_id=dinas_id,
        is_verified=is_verified,
        limit=limit,
        offset=offset
    )
    
    has_more = (offset + len(data)) < total
    
    return schemas.PaginatedResponse[schemas.UserDetailResponse](
        data=data,  # type: ignore
        message=f"Ditemukan {len(data)} dari {total} pengguna",
        pagination={
            "total": total,
            "limit": limit,
            "offset": offset,
            "returned": len(data),
            "has_more": has_more
        }
    )