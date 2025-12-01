from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import SessionLocal
import controller.auth as auth
import schemas.schemas as schemas
from model.models import User as UserModel
from services.wallet_service import WalletService
from services.wallet_type_service import WalletTypeService
from i18n.messages import get_message

router = APIRouter(prefix="/wallet", tags=["Wallet"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Wallet Type endpoints
@router.get("/type", response_model=schemas.SuccessListResponse[schemas.WalletTypeResponse])
def list_wallet_types(db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessListResponse[schemas.WalletTypeResponse]:
    data = WalletTypeService.list(db)
    return schemas.SuccessListResponse[schemas.WalletTypeResponse](data=data, message=get_message("create_success", None))  # type: ignore

@router.post("/types", response_model=schemas.SuccessResponse[schemas.WalletTypeResponse])
def create_wallet_type(payload: schemas.WalletTypeBase, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.WalletTypeResponse]:
    created = WalletTypeService.create(db, payload)
    return schemas.SuccessResponse[schemas.WalletTypeResponse](data=created, message=get_message("create_success", None))

# Wallet endpoints
@router.get("/", response_model=schemas.SuccessListResponse[schemas.WalletResponse])
def list_wallets(db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessListResponse[schemas.WalletResponse]:
    data = WalletService.list(db)
    return schemas.SuccessListResponse[schemas.WalletResponse](data=data, message=get_message("create_success", None))  # type: ignore

@router.get("/{wallet_id}", response_model=schemas.SuccessResponse[schemas.WalletResponse])
def get_wallet(wallet_id: int, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.WalletResponse]:
    w = WalletService.get(db, wallet_id)
    if not w:
        raise HTTPException(status_code=404, detail="Wallet tidak ditemukan")
    return schemas.SuccessResponse[schemas.WalletResponse](data=w, message=get_message("create_success", None))

@router.get("/user/{user_id}", response_model=schemas.SuccessResponse[schemas.WalletResponse])
def get_wallet_by_user(user_id: int, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.WalletResponse]:
    w = WalletService.get_by_user(db, user_id)
    if not w:
        raise HTTPException(status_code=404, detail="Wallet user tidak ditemukan")
    return schemas.SuccessResponse[schemas.WalletResponse](data=w, message=get_message("create_success", None))

@router.post("/", response_model=schemas.SuccessResponse[schemas.WalletResponse])
def create_wallet(payload: schemas.WalletCreate, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.WalletResponse]:
    created = WalletService.create(db, payload)
    return schemas.SuccessResponse[schemas.WalletResponse](data=created, message=get_message("create_success", None))

@router.put("/{wallet_id}", response_model=schemas.SuccessResponse[schemas.WalletResponse])
def update_wallet(wallet_id: int, payload: schemas.WalletCreate, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.WalletResponse]:
    updated = WalletService.update(db, wallet_id, payload)
    return schemas.SuccessResponse[schemas.WalletResponse](data=updated, message=get_message("update_success", None))

@router.delete("/{wallet_id}", response_model=schemas.SuccessResponse[schemas.Message])
def delete_wallet(wallet_id: int, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.Message]:
    WalletService.delete(db, wallet_id)
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="Wallet dihapus"), message=get_message("wallet_delete_success", None))
