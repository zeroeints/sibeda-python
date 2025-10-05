from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import SessionLocal
import controller.auth as auth
import controller.WalletType as wallet_type_controller
import schemas.schemas as schemas
import model.models as models
from model.models import User as UserModel
from services.wallet_service import WalletService

router = APIRouter(prefix="/wallet", tags=["Wallet"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Wallet Type endpoints
@router.get("/types", response_model=schemas.SuccessListResponse[schemas.WalletTypeResponse])
def list_wallet_types(db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessListResponse[schemas.WalletTypeResponse]:
    data = wallet_type_controller.get_wallet_type(db)
    return schemas.SuccessListResponse[schemas.WalletTypeResponse](data=data)

@router.post("/types", response_model=schemas.SuccessResponse[schemas.WalletTypeResponse])
def create_wallet_type(payload: schemas.WalletTypeBase, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.WalletTypeResponse]:
    wt = models.WalletType(Nama=payload.Nama)
    created = wallet_type_controller.create_wallet_type(db, wt)
    return schemas.SuccessResponse[schemas.WalletTypeResponse](data=created)

# Wallet endpoints
@router.get("/", response_model=schemas.SuccessListResponse[schemas.WalletResponse])
def list_wallets(db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessListResponse[schemas.WalletResponse]:
    data = WalletService.list(db)
    return schemas.SuccessListResponse[schemas.WalletResponse](data=data)

@router.get("/{wallet_id}", response_model=schemas.SuccessResponse[schemas.WalletResponse])
def get_wallet(wallet_id: int, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.WalletResponse]:
    w = WalletService.get(db, wallet_id)
    if not w:
        raise HTTPException(status_code=404, detail="Wallet tidak ditemukan")
    return schemas.SuccessResponse[schemas.WalletResponse](data=w)

@router.get("/user/{user_id}", response_model=schemas.SuccessResponse[schemas.WalletResponse])
def get_wallet_by_user(user_id: int, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.WalletResponse]:
    w = WalletService.get_by_user(db, user_id)
    if not w:
        raise HTTPException(status_code=404, detail="Wallet user tidak ditemukan")
    return schemas.SuccessResponse[schemas.WalletResponse](data=w)

@router.post("/", response_model=schemas.SuccessResponse[schemas.WalletResponse])
def create_wallet(payload: schemas.WalletCreate, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.WalletResponse]:
    created = WalletService.create(db, payload)
    return schemas.SuccessResponse[schemas.WalletResponse](data=created)

@router.put("/{wallet_id}", response_model=schemas.SuccessResponse[schemas.WalletResponse])
def update_wallet(wallet_id: int, payload: schemas.WalletCreate, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.WalletResponse]:
    updated = WalletService.update(db, wallet_id, payload)
    return schemas.SuccessResponse[schemas.WalletResponse](data=updated)

@router.delete("/{wallet_id}", response_model=schemas.SuccessResponse[schemas.Message])
def delete_wallet(wallet_id: int, db: Session = Depends(get_db), _u: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.Message]:
    WalletService.delete(db, wallet_id)
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="Wallet dihapus"))
