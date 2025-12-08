from __future__ import annotations
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
import model.models as models
from schemas.schemas import WalletCreate, WalletUpdate

class WalletService:
    @staticmethod
    def list(db: Session) -> List[models.Wallet]:
        return db.query(models.Wallet).all()

    @staticmethod
    def get(db: Session, wallet_id: int) -> Optional[models.Wallet]:
        return db.query(models.Wallet).options(joinedload(models.Wallet.user)).filter(models.Wallet.id == wallet_id).first()

    @staticmethod
    def get_by_user(db: Session, user_id: int) -> Optional[models.Wallet]:
        return db.query(models.Wallet).filter(models.Wallet.user_id == user_id).first()

    @staticmethod
    def create(db: Session, payload: WalletCreate) -> models.Wallet:
        # Check User Exists
        if not db.query(models.User).filter(models.User.id == payload.user_id).first():
            raise HTTPException(status_code=400, detail="User ID tidak ditemukan")
        
        # Check Wallet Type Exists
        if not db.query(models.WalletType).filter(models.WalletType.id == payload.wallet_type_id).first():
            raise HTTPException(status_code=400, detail="Wallet Type ID tidak ditemukan")
        
        # Check Uniqueness
        if db.query(models.Wallet).filter(models.Wallet.user_id == payload.user_id).first():
            raise HTTPException(status_code=400, detail="User sudah memiliki wallet")
        
        wallet = models.Wallet(
            user_id=payload.user_id, 
            wallet_type_id=payload.wallet_type_id, 
            saldo=payload.saldo
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
        return wallet

    @staticmethod
    def update(db: Session, wallet_id: int, payload: WalletCreate | WalletUpdate) -> models.Wallet:
        wallet = db.query(models.Wallet).filter(models.Wallet.id == wallet_id).first()
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet tidak ditemukan")
        
        if payload.user_id is not None:
             if payload.user_id != wallet.user_id:
                raise HTTPException(status_code=400, detail="User ID tidak boleh diubah")
        
        if payload.wallet_type_id is not None:
            if not db.query(models.WalletType).filter(models.WalletType.id == payload.wallet_type_id).first():
                raise HTTPException(status_code=400, detail="Wallet Type ID tidak ditemukan")
            wallet.wallet_type_id = payload.wallet_type_id

        if payload.saldo is not None:
            wallet.saldo = payload.saldo

        db.commit()
        db.refresh(wallet)
        return wallet

    @staticmethod
    def delete(db: Session, wallet_id: int) -> None:
        wallet = db.query(models.Wallet).filter(models.Wallet.id == wallet_id).first()
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet tidak ditemukan")
        db.delete(wallet)
        db.commit()