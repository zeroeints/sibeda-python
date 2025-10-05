from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException
import model.models as models
import schemas.schemas as schemas

class DinasService:
    @staticmethod
    def list(db: Session) -> List[models.Dinas]:
        return db.query(models.Dinas).all()

    @staticmethod
    def create(db: Session, dinas_in: schemas.DinasBase) -> models.Dinas:
        d = models.Dinas(Nama=dinas_in.Nama)
        db.add(d)
        db.commit()
        db.refresh(d)
        return d

    @staticmethod
    def delete(db: Session, dinas_id: int) -> None:
        d = db.query(models.Dinas).filter(models.Dinas.ID == dinas_id).first()
        if not d:
            raise HTTPException(status_code=404, detail="Dinas tidak ditemukan")
        db.delete(d)
        db.commit()
