from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import model.models as models
import controller.auth as auth
import schemas.schemas as schemas

class UserService:
    @staticmethod
    def create(db: Session, user_in: schemas.UserCreate) -> models.User:
        user = models.User(
            NIP=user_in.NIP,
            Role=models.RoleEnum.pic,
            NamaLengkap=user_in.NamaLengkap,
            Email=user_in.Email,
            NoTelepon=user_in.NoTelepon,
            Password=auth.get_password_hash(user_in.Password),
            DinasID=user_in.DinasID,
        )
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="NIP atau Email sudah terdaftar")
        db.refresh(user)
        return user

    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 10) -> List[models.User]:
        return db.query(models.User).offset(skip).limit(limit).all()
