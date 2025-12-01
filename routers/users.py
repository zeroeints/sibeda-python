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
    response_model=schemas.SuccessResponse[schemas.PagedListData[schemas.UserResponse]],
    summary="List Users (Paged)"
)
def read_users(
    skip: int = Query(0, ge=0), 
    limit: int = Query(10, ge=1, le=1000), 
    db: Session = Depends(get_db), 
    _current_user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.PagedListData[schemas.UserResponse]]:
    
    result = UserService.list(db, skip=skip, limit=limit)
    return schemas.SuccessResponse[schemas.PagedListData[schemas.UserResponse]](
        data=result, 
        message=get_message("create_success", None)
    )
@router.get(
    "/{user_id}", 
    # [UPDATED] Menggunakan Detail Response agar lebih lengkap infonya
    response_model=schemas.SuccessResponse[schemas.UserDetailResponse], 
    summary="Get User Detail Complete"
)
def get_user(user_id: int, db: Session = Depends(get_db), _current_user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.UserDetailResponse]:
    # Menggunakan method optimized
    user_detail = UserService.get_user_detail_complete(db, user_id)
    if not user_detail:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return schemas.SuccessResponse[schemas.UserDetailResponse](data=user_detail, message="User berhasil ditemukan")

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
    response_model=schemas.SuccessResponse[schemas.UserCountByDinas],
    summary="Count Users per Dinas",
    description="Mendapatkan statistik jumlah pengguna yang terdaftar di setiap dinas."
)
def get_user_count_by_dinas(db: Session = Depends(get_db), _current_user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.UserCountByDinas]:
    user_counts = UserService.get_user_count_by_dinas(db)
    return schemas.SuccessResponse[schemas.UserCountByDinas](
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
    response_model=schemas.SuccessResponse[schemas.PagedListData[schemas.UserDetailResponse]],
    summary="Search Users Detailed (Paged)"
)
def search_users_detailed(
    search: str | None = Query(None),
    role: str | None = Query(None),
    dinas_id: int | None = Query(None),
    is_verified: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.PagedListData[schemas.UserDetailResponse]]:
    
    total = UserService.count_users(db, search, role, dinas_id, is_verified)
    data = UserService.search_users_detailed(db, search, role, dinas_id, is_verified, None, limit, offset)
    
    has_more = (offset + len(data)) < total
    
    # Construct standard PagedListData
    result = {
        "list": data,
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
        "stat": {"total_data": total}
    }
    
    return schemas.SuccessResponse[schemas.PagedListData[schemas.UserDetailResponse]](
        data=result, 
        message=f"Ditemukan {len(data)} dari {total} pengguna"
    )