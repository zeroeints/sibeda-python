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
    def create(db: Session, payload: schemas.DinasBase) -> models.Dinas:
        # PEP8: Keyword arguments lowercase
        dinas = models.Dinas(nama=payload.nama)
        db.add(dinas)
        db.commit()
        db.refresh(dinas)
        return dinas

    @staticmethod
    def delete(db: Session, dinas_id: int) -> None:
        dinas = db.query(models.Dinas).filter(models.Dinas.id == dinas_id).first()
        if not dinas:
            raise HTTPException(status_code=404, detail="Dinas tidak ditemukan")
        db.delete(dinas)
        db.commit()