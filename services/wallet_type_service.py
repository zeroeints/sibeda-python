from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session
import model.models as models
from schemas.schemas import WalletTypeBase

class WalletTypeService:
    @staticmethod
    def list(db: Session) -> List[models.WalletType]:
        return db.query(models.WalletType).all()

    @staticmethod
    def create(db: Session, payload: WalletTypeBase) -> models.WalletType:
        wt = models.WalletType(nama=payload.nama)
        db.add(wt)
        db.commit()
        db.refresh(wt)
        return wt