from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Generic, TypeVar
from pydantic.generics import GenericModel
from datetime import datetime

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

class SubmissionStatusEnum(str, Enum):
    Accepted = "Accepted"
    Rejected = "Rejected"
    Pending = "Pending"

class UserBase(BaseModel):
    NIP: str = Field(..., min_length=18, max_length=50, description="Nomor Induk Pegawai minimal 18 karakter")
    NamaLengkap: str
    Email: str
    NoTelepon: str | None = None

    @field_validator("NIP")
    @classmethod
    def nip_strip(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 18:
            raise ValueError("NIP minimal 18 karakter")
        return v

class UserCreate(UserBase):
    Password: str = Field(..., min_length=8, max_length=255, description="Password minimal 8 karakter")

    @field_validator("Password")
    @classmethod
    def password_strip(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 8:
            raise ValueError("Password minimal 8 karakter")
        return v

class UserUpdate(BaseModel):
    """Schema untuk update user. Semua field optional."""
    NIP: str | None = Field(None, min_length=18, max_length=50, description="Nomor Induk Pegawai minimal 18 karakter")
    NamaLengkap: str | None = None
    Email: str | None = None
    NoTelepon: str | None = None
    Password: str | None = Field(None, min_length=8, max_length=255, description="Password minimal 8 karakter")
    Role: RoleEnum | None = None
    DinasID: int | None = None
    
    @field_validator("NIP")
    @classmethod
    def nip_strip(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 18:
            raise ValueError("NIP minimal 18 karakter")
        return v
    
    @field_validator("Password")
    @classmethod
    def password_strip(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 8:
            raise ValueError("Password minimal 8 karakter")
        return v

class LoginJSON(BaseModel):
    NIP: str
    Password: str

class UserResponse(UserBase):
    ID: int
    Role: RoleEnum
    isVerified: bool | None = None  # tambahkan agar pydantic bisa serialize kolom baru

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
    Role: list[str] | None = None
    NamaLengkap: str | None = None
    Email: str | None = None
    NoTelepon: str | None = None
    DinasID: int | None = None
    Dinas: dict[str, int | str | None] | None = None
    isVerified: bool | None = None
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

class VehicleTypeBase(BaseModel):
    Nama: str

class VehicleTypeResponse(VehicleTypeBase):
    ID: int
    class Config:
        from_attributes = True

class VehicleCreate(BaseModel):
    Nama: str
    Plat: str
    VehicleTypeID: int
    KapasitasMesin: int | None = None
    Odometer: int | None = None
    Status: VehicleStatusEnum | None = None  
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

# ------------------- Report Schemas -------------------
class ReportBase(BaseModel):
    KodeUnik: str
    UserID: int
    VehicleID: int
    AmountRupiah: float
    AmountLiter: float
    Description: str | None = None
    Latitude: float | None = None
    Longitude: float | None = None
    VehiclePhysicalPhotoPath: str | None = None
    OdometerPhotoPath: str | None = None
    InvoicePhotoPath: str | None = None
    MyPertaminaPhotoPath: str | None = None
    Odometer: int | None = None

class ReportCreate(ReportBase):
    pass

class ReportUpdate(BaseModel):
    # semua optional agar partial update bisa dilakukan (PUT/POST semantics kept simple)
    KodeUnik: str | None = None
    UserID: int | None = None
    VehicleID: int | None = None
    AmountRupiah: float | None = None
    AmountLiter: float | None = None
    Description: str | None = None
    Latitude: float | None = None
    Longitude: float | None = None
    VehiclePhysicalPhotoPath: str | None = None
    OdometerPhotoPath: str | None = None
    InvoicePhotoPath: str | None = None
    MyPertaminaPhotoPath: str | None = None
    Odometer: int | None = None

class ReportResponse(ReportBase):
    ID: int
    Timestamp: str | None = None  # serialized ISO datetime

    class Config:
        from_attributes = True

# ------------------- Submission Schemas -------------------
class SubmissionBase(BaseModel):
    KodeUnik: str
    CreatorID: int
    ReceiverID: int
    TotalCashAdvance: float
    VehicleID: int
    Status: SubmissionStatusEnum | None = None

class SubmissionCreate(SubmissionBase):
    pass

class SubmissionUpdate(BaseModel):
    KodeUnik: str | None = None
    CreatorID: int | None = None
    ReceiverID: int | None = None
    TotalCashAdvance: float | None = None
    VehicleID: int | None = None
    Status: SubmissionStatusEnum | None = None

class SubmissionResponse(BaseModel):
    ID: int
    KodeUnik: str
    CreatorID: int
    ReceiverID: int
    TotalCashAdvance: float
    VehicleID: int
    Status: SubmissionStatusEnum  # concrete in response
    created_at: datetime | None = None

    class Config:
        from_attributes = True

# ------------------- Password Reset / OTP Schemas -------------------
class ForgotPasswordRequest(BaseModel):
    email: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str

class OTPVerifyResponse(BaseModel):
    valid: bool
    reason: str | None = None

# ------------------- QR Schemas -------------------
class QRAssignRequest(BaseModel):
    NIP: str
    UniqueCode: str
    DinasID: int

class QRGetResponse(BaseModel):
    code: str | None = None
    expiresAt: str | None = None

class QRScanRequest(BaseModel):
    kode_unik: str = Field(..., description="QR code input (signed token atau raw code)")
