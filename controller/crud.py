from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import model.models as models, schemas.schemas as schemas
import controller.auth as auth 

def create_user(db: Session, user: schemas.UserCreate):
    db_user: models.User = models.User(
        NIP=user.NIP,
        Role=models.RoleEnum.pic,
        NamaLengkap=user.NamaLengkap,
        Email=user.Email,
        NoTelepon=user.NoTelepon,
        Password=auth.get_password_hash(user.Password), 
        DinasID=user.DinasID
    )
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
       
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="NIP atau Email sudah terdaftar")
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_dinas(db: Session):
    return db.query(models.Dinas).all()

def create_dinas(db: Session, dinas: schemas.DinasBase):
    db_dinas = models.Dinas(
        Nama=dinas.Nama
    )
    db.add(db_dinas)
    db.commit()
    db.refresh(db_dinas)
    return db_dinas