from typing import List
from sqlalchemy.orm import Session
from model import models

def get_wallet_type(db: Session) -> List[models.WalletType]:
    return db.query(models.WalletType).all()

def create_wallet_type(db: Session, wallet_type: models.WalletType) -> models.WalletType:   
    db.add(wallet_type)
    db.commit()
    db.refresh(wallet_type)
    return wallet_type