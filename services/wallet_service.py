from __future__ import annotations
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
import model.models as models
from model.models import Wallet as WalletModel
from schemas.schemas import WalletCreate

class WalletService:
    @staticmethod
    def list(db: Session) -> List[WalletModel]:
        return db.query(WalletModel).all()

    @staticmethod
    def get(db: Session, wallet_id: int) -> Optional[WalletModel]:
        return db.query(WalletModel).filter(WalletModel.ID == wallet_id).first()

    @staticmethod
    def get_by_user(db: Session, user_id: int) -> Optional[WalletModel]:
        return db.query(WalletModel).filter(WalletModel.UserID == user_id).first()

    @staticmethod
    def create(db: Session, payload: WalletCreate) -> WalletModel:
        # user exists
        if not db.query(models.User).filter(models.User.ID == payload.UserID).first():
            raise HTTPException(status_code=400, detail="UserID tidak ditemukan")
        # wallet type exists
        if not db.query(models.WalletType).filter(models.WalletType.ID == payload.WalletTypeID).first():
            raise HTTPException(status_code=400, detail="WalletTypeID tidak ditemukan")
        # uniqueness (1 wallet per user)
        if db.query(WalletModel).filter(WalletModel.UserID == payload.UserID).first():
            raise HTTPException(status_code=400, detail="User sudah memiliki wallet")
        w = WalletModel(UserID=payload.UserID, WalletTypeID=payload.WalletTypeID, Saldo=getattr(payload, "Saldo", 0))
        db.add(w)
        db.commit()
        db.refresh(w)
        return w

    @staticmethod
    def update(db: Session, wallet_id: int, payload: WalletCreate) -> WalletModel:
        w = db.query(WalletModel).filter(WalletModel.ID == wallet_id).first()
        if not w:
            raise HTTPException(status_code=404, detail="Wallet tidak ditemukan")
        if payload.UserID != w.UserID:
            raise HTTPException(status_code=400, detail="UserID tidak boleh diubah")
        if not db.query(models.WalletType).filter(models.WalletType.ID == payload.WalletTypeID).first():
            raise HTTPException(status_code=400, detail="WalletTypeID tidak ditemukan")
        setattr(w, "WalletTypeID", payload.WalletTypeID)
        setattr(w, "Saldo", payload.Saldo)
        db.commit()
        db.refresh(w)
        return w

    @staticmethod
    def delete(db: Session, wallet_id: int) -> None:
        w = db.query(WalletModel).filter(WalletModel.ID == wallet_id).first()
        if not w:
            raise HTTPException(status_code=404, detail="Wallet tidak ditemukan")
        db.delete(w)
        db.commit()
