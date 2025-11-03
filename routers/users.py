from fastapi import APIRouter, Depends, Query
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

@router.post("/", response_model=schemas.SuccessResponse[schemas.UserResponse])
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)) -> schemas.SuccessResponse[schemas.UserResponse]:
    settings = get_settings()
    created = UserService.create(db, user)
    msg = get_message("user_create_success", None)
    # Jangan expose OTP di production
    if settings.debug and hasattr(created, "_registration_otp"):
        msg = f"{msg} | OTP={getattr(created, '_registration_otp')}"
    return schemas.SuccessResponse[schemas.UserResponse](data=created, message=msg)

@router.post("/register", response_model=schemas.SuccessResponse[schemas.UserResponse])
def register_user_alias(user: schemas.UserCreate, db: Session = Depends(get_db)) -> schemas.SuccessResponse[schemas.UserResponse]:
    return register_user(user, db)  # reuse logic


@router.get("/", response_model=schemas.SuccessListResponse[schemas.UserResponse])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), _current_user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessListResponse[schemas.UserResponse]:
    users = UserService.list(db, skip=skip, limit=limit)
    return schemas.SuccessListResponse[schemas.UserResponse](data=users, message=get_message("create_success", None))

@router.get("/{user_id}", response_model=schemas.SuccessResponse[schemas.UserResponse])
def get_user(user_id: int, db: Session = Depends(get_db), _current_user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.UserResponse]:
    """Get user by ID"""
    user = UserService.get_by_id(db, user_id)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return schemas.SuccessResponse[schemas.UserResponse](data=user, message="User berhasil ditemukan")

@router.put("/{user_id}", response_model=schemas.SuccessResponse[schemas.UserResponse])
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db), _current_user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.UserResponse]:
    """Update user by ID. Hanya field yang diisi yang akan diupdate."""
    updated_user = UserService.update(db, user_id, user_update)
    return schemas.SuccessResponse[schemas.UserResponse](data=updated_user, message=get_message("update_success", None))

@router.patch("/{user_id}", response_model=schemas.SuccessResponse[schemas.UserResponse])
def patch_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db), _current_user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.UserResponse]:
    """Alias untuk update user (PATCH method)"""
    return update_user(user_id, user_update, db, _current_user)

@router.get("/stats/count-by-dinas", response_model=schemas.SuccessListResponse[schemas.UserCountByDinas])
def get_user_count_by_dinas(db: Session = Depends(get_db), _current_user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessListResponse[schemas.UserCountByDinas]:
    """
    Mendapatkan total pengguna per dinas.
    
    Returns list berisi:
    - dinas_id: ID dinas (null jika user tidak punya dinas)
    - dinas_nama: Nama dinas atau "Tidak Ada Dinas"
    - total_users: Jumlah user di dinas tersebut
    
    Diurutkan dari dinas dengan user terbanyak.
    """
    user_counts = UserService.get_user_count_by_dinas(db)
    return schemas.SuccessListResponse[schemas.UserCountByDinas](
        data=user_counts, 
        message="Berhasil mendapatkan total pengguna per dinas"
    )


@router.get("/detailed/search", response_model=schemas.PaginatedResponse[schemas.UserDetailResponse])
def search_users_detailed(
    search: str | None = Query(None, description="Cari berdasarkan NIP, Nama, atau Email"),
    role: str | None = Query(None, description="Filter berdasarkan role: admin, kepala_dinas, pic"),
    dinas_id: int | None = Query(None, description="Filter berdasarkan ID dinas"),
    is_verified: bool | None = Query(None, description="Filter berdasarkan status verifikasi"),
    limit: int = Query(100, ge=1, le=1000, description="Limit jumlah data (default 100, max 1000)"),
    offset: int = Query(0, ge=0, description="Offset untuk pagination"),
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(auth.get_current_user)
) -> schemas.PaginatedResponse[schemas.UserDetailResponse]:
    """
    Mencari dan mendapatkan detail lengkap pengguna dengan wallet dan dinas
    
    - **search**: Cari berdasarkan NIP, Nama Lengkap, atau Email (case-insensitive)
    - **role**: Filter berdasarkan role (admin, kepala_dinas, pic)
    - **dinas_id**: Filter berdasarkan ID dinas
    - **is_verified**: Filter berdasarkan status verifikasi (true/false)
    - **limit**: Batasi jumlah data (default 100)
    - **offset**: Skip sejumlah data untuk pagination
    
    Returns:
    - Detail user termasuk:
      - Data user lengkap (NIP, Nama, Email, Role, dll)
      - Wallet info (ID, Saldo, Type)
      - Dinas info (ID, Nama)
      - Total submission yang dibuat dan diterima
    - Pagination info (total, has_more, dll)
    """
    # Get total count
    total = UserService.count_users(
        db,
        search=search,
        role=role,
        dinas_id=dinas_id,
        is_verified=is_verified
    )
    
    # Get data
    data = UserService.search_users_detailed(
        db,
        search=search,
        role=role,
        dinas_id=dinas_id,
        is_verified=is_verified,
        limit=limit,
        offset=offset
    )
    
    # Calculate pagination info
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
