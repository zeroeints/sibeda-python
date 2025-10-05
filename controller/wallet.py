from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from model.models import Wallet as WalletModel
import model.models as models
from schemas.schemas import WalletCreate

def get_wallet(db: Session) -> list[WalletModel]:
    return db.query(WalletModel).all()

def get_wallet_by_id(db: Session, wallet_id: int) -> Optional[WalletModel]:
    return db.query(WalletModel).filter(WalletModel.ID == wallet_id).first()

def get_wallet_by_user_id(db: Session, user_id: int) -> Optional[WalletModel]:
    return db.query(WalletModel).filter(WalletModel.UserID == user_id).first()

def create_wallet(db: Session, wallet_in: WalletCreate) -> WalletModel:
    # Validate user exists
    user = db.query(models.User).filter(models.User.ID == wallet_in.UserID).first()
    if not user:
        raise HTTPException(status_code=400, detail="UserID tidak ditemukan")

    # Validate wallet type exists
    wallet_type = db.query(models.WalletType).filter(models.WalletType.ID == wallet_in.WalletTypeID).first()
    if not wallet_type:
        raise HTTPException(status_code=400, detail="WalletTypeID tidak ditemukan")

    # Ensure user doesn't already have a wallet
    existing = db.query(WalletModel).filter(WalletModel.UserID == wallet_in.UserID).first()
    if existing:
        raise HTTPException(status_code=400, detail="User sudah memiliki wallet")

    db_wallet = WalletModel(
        UserID=wallet_in.UserID,
        WalletTypeID=wallet_in.WalletTypeID,
        Saldo=getattr(wallet_in, "Saldo", 0),
    )
    db.add(db_wallet)
    db.commit()
    db.refresh(db_wallet)
    return db_wallet