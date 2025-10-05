from pydantic import BaseModel
from enum import Enum
from typing import Generic, TypeVar
from pydantic.generics import GenericModel

T = TypeVar("T")

class SuccessResponse(GenericModel, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None

class SuccessListResponse(SuccessResponse[list[T]], Generic[T]):  # convenience alias for lists
    pass

class RoleEnum(str, Enum):
    admin = "admin"
    kepala_dinas = "kepala_dinas"
    pic = "pic"

class VehicleStatusEnum(str, Enum):
    Active = "Active"
    Nonactive = "Nonactive"

class UserBase(BaseModel):
    NIP: str
    NamaLengkap: str
    Email: str
    NoTelepon: str | None = None

class UserCreate(UserBase):
    Password: str
    DinasID: int | None = None

class UserResponse(UserBase):
    ID: int
    Role: RoleEnum

    class Config:
        from_attributes = True 

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenClaims(BaseModel):
    sub: str
    ID: int | None = None
    NIP: str | None = None
    Role: str | None = None
    NamaLengkap: str | None = None
    Email: str | None = None
    NoTelepon: str | None = None
    DinasID: int | None = None
    exp: int | None = None  # epoch seconds

class TokenVerifyData(BaseModel):
    valid: bool
    claims: TokenClaims | None = None
    reason: str | None = None

class DinasBase(BaseModel):
    Nama: str

class DinasResponse(DinasBase):
    ID: int
    class Config:
        from_attributes = True    

class WalletTypeBase(BaseModel):
    Nama: str

class WalletTypeResponse(WalletTypeBase):
    ID: int
    class Config:
        from_attributes = True
  
class WalletBase(BaseModel):
    UserID: int
    Saldo: float
    WalletTypeID: int

class WalletCreate(WalletBase):
    pass
class WalletResponse(WalletBase):
    ID: int
    class Config:
        from_attributes = True

class DinasListResponse(BaseModel):
    status_code: int
    message: str
    data: list[DinasResponse]

class vehicleTypeBase(BaseModel):
    Nama: str

class VehicleTypeResponse(vehicleTypeBase):
    ID: int
    class Config:
        from_attributes = True

class VehicleCreate(BaseModel):
    Nama: str
    Plat: str
    VehicleTypeID: int
    KapasitasMesin: int | None = None
    Odometer: int | None = None
    Status: VehicleStatusEnum | None = None  # opsional (default DB: Active)
    JenisBensin: str | None = None
    Merek: str | None = None
    FotoFisik: str | None = None

class VehicleResponse(BaseModel):
    ID: int
    Nama: str
    Plat: str
    VehicleTypeID: int
    KapasitasMesin: int | None = None
    Odometer: int | None = None
    Status: VehicleStatusEnum
    JenisBensin: str | None = None
    Merek: str | None = None
    FotoFisik: str | None = None

    class Config:
        from_attributes = True

class Message(BaseModel):
    detail: str