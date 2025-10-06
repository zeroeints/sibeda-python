from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import controller.auth as auth
import schemas.schemas as schemas
from database.database import SessionLocal
from model.models import User as UserModel
from services.user_service import UserService
from i18n.messages import get_message

router = APIRouter(prefix="/users", tags=["Users"]) 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.SuccessResponse[schemas.UserResponse])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)) -> schemas.SuccessResponse[schemas.UserResponse]:
    created = UserService.create(db, user)
    return schemas.SuccessResponse[schemas.UserResponse](data=created, message=get_message("user_create_success", None))

@router.get("/", response_model=schemas.SuccessListResponse[schemas.UserResponse])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), _current_user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessListResponse[schemas.UserResponse]:
    users = UserService.list(db, skip=skip, limit=limit)
    return schemas.SuccessListResponse[schemas.UserResponse](data=users, message=get_message("create_success", None))
