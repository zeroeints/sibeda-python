from fastapi import APIRouter, Depends
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
