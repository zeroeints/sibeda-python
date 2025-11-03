from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session
import model.models as models
from model.models import WalletType as WalletTypeModel
from schemas.schemas import WalletTypeBase

class WalletTypeService:
    @staticmethod
    def list(db: Session) -> List[WalletTypeModel]:
        return db.query(WalletTypeModel).all()

    @staticmethod
    def create(db: Session, payload: WalletTypeBase) -> WalletTypeModel:
        wt = models.WalletType(Nama=payload.Nama)
        db.add(wt)
        db.commit()
        db.refresh(wt)
        return wt
