from __future__ import annotations
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
from typing import Generic, TypeVar, List, Optional, Any
from datetime import datetime

T = TypeVar("T")

# --- Enums ---
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

class ReportStatusEnum(str, Enum):
    Pending = "Pending"
    Reviewed = "Reviewed"
    Accepted = "Accepted"
    Rejected = "Rejected"

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
    exp: int | None = None


# --- Base Response Wrappers ---
class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None

class SuccessListResponse(SuccessResponse[List[T]], Generic[T]):
    pass

class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    message: str | None = None
    pagination: dict[str, int | bool]

class Message(BaseModel):
    detail: str

# --- Simple Models untuk Nesting (Mencegah Circular Dependency) ---
class UserSimpleResponse(BaseModel):
    ID: int
    NIP: str
    NamaLengkap: str
    Role: RoleEnum
    Email: str
    NoTelepon: str | None = None
    model_config = ConfigDict(from_attributes=True)

class VehicleTypeResponse(BaseModel):
    ID: int
    Nama: str
    model_config = ConfigDict(from_attributes=True)

class VehicleSimpleResponse(BaseModel):
    ID: int
    Nama: str
    Plat: str
    Status: VehicleStatusEnum
    VehicleType: VehicleTypeResponse | None = None # Nested Object
    AssetIconName: str | None = None
    AssetIconColor: str | None = None
    model_config = ConfigDict(from_attributes=True)

# --- Log Models ---
class SubmissionLogResponse(BaseModel):
    ID: int
    Status: SubmissionStatusEnum
    Timestamp: datetime
    UpdatedByUserID: int | None = None
    UpdatedByUser: UserSimpleResponse | None = None # Field baru: User Object
    Notes: str | None = None
    model_config = ConfigDict(from_attributes=True)

class ReportLogResponse(BaseModel):
    ID: int
    Status: ReportStatusEnum
    Timestamp: datetime
    UpdatedByUserID: int | None = None
    UpdatedByUser: UserSimpleResponse | None = None # Field baru: User Object
    Notes: str | None = None
    model_config = ConfigDict(from_attributes=True)

# --- User Schemas ---
class UserBase(BaseModel):
    NIP: str = Field(..., min_length=18, max_length=50)
    NamaLengkap: str
    Email: str
    NoTelepon: str | None = None

    @field_validator("NIP")
    @classmethod
    def nip_strip(cls, v: str) -> str:
        return v.strip()

class UserCreate(UserBase):
    Password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    NIP: str | None = None
    NamaLengkap: str | None = None
    Email: str | None = None
    NoTelepon: str | None = None
    Password: str | None = None
    Role: RoleEnum | None = None
    DinasID: int | None = None

class UserResponse(UserBase):
    ID: int
    Role: RoleEnum
    isVerified: bool | None = None
    model_config = ConfigDict(from_attributes=True)

class UserDetailResponse(BaseModel):
    ID: int
    NIP: str
    NamaLengkap: str
    Email: str
    Role: RoleEnum
    DinasID: int | None = None
    DinasNama: str | None = None
    # Wallet info nested
    WalletID: int | None = None
    WalletSaldo: float | None = None
    WalletType: str | None = None
    TotalSubmissionsCreated: int = 0
    TotalSubmissionsReceived: int = 0
    model_config = ConfigDict(from_attributes=True)

class UserBalanceResponse(BaseModel):
    User: UserSimpleResponse
    DinasNama: str | None = None
    WalletID: int
    Saldo: float
    WalletType: str | None = None
    model_config = ConfigDict(from_attributes=True)

# --- Auth Schemas ---
class LoginJSON(BaseModel):
    NIP: str
    Password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenClaims(BaseModel):
    sub: str
    ID: int | None = None
    NIP: str | None = None
    Role: list[str] | None = None
    # ... claims lain

class TokenVerifyData(BaseModel):
    valid: bool
    claims: dict | None = None
    reason: str | None = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

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

# --- Dinas & Wallet Type ---
class DinasBase(BaseModel):
    Nama: str

class DinasResponse(DinasBase):
    ID: int
    model_config = ConfigDict(from_attributes=True)

class WalletTypeBase(BaseModel):
    Nama: str

class WalletTypeResponse(WalletTypeBase):
    ID: int
    model_config = ConfigDict(from_attributes=True)

class WalletCreate(BaseModel):
    UserID: int
    WalletTypeID: int
    Saldo: float = 0

class WalletResponse(BaseModel):
    ID: int
    User: UserSimpleResponse
    WalletType: WalletTypeResponse
    Saldo: float
    model_config = ConfigDict(from_attributes=True)

# --- Vehicle Schemas ---
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
    AssetIconName: str | None = None
    AssetIconColor: str | None = None
    TipeTransmisi: str | None = None  # Baru: untuk "Tipe Transmisi" (Matic/Manual)
    TotalFuelBar: int | None = None   # Baru: untuk "Jumlah Fuelmeter Bar"
    CurrentFuelBar: int | None = None # Baru: untuk "Fuelmeter saat ini"

class VehicleUpdate(BaseModel):
    Nama: str
    Plat: str
    VehicleTypeID: int
    KapasitasMesin: int | None = None
    Odometer: int | None = None
    Status: VehicleStatusEnum | None = None
    JenisBensin: str | None = None
    Merek: str | None = None
    FotoFisik: str | None = None
    AssetIconName: str | None = None
    AssetIconColor: str | None = None

class VehicleResponse(BaseModel):
    ID: int
    Nama: str
    Plat: str
    VehicleType: VehicleTypeResponse | None = None # Nested
    KapasitasMesin: int | None = None
    Odometer: int | None = None
    Status: VehicleStatusEnum
    JenisBensin: str | None = None
    Merek: str | None = None
    FotoFisik: str | None = None
    AssetIconName: str | None = None
    AssetIconColor: str | None = None
    model_config = ConfigDict(from_attributes=True)

class RefuelHistoryItem(BaseModel):
    ID: int
    KodeUnik: str
    AmountRupiah: float
    AmountLiter: float
    Timestamp: datetime
    Odometer: int | None = None
    model_config = ConfigDict(from_attributes=True)

class MyVehicleResponse(VehicleResponse):
    # TotalSubmissions tidak relevan lagi karena vehicle tidak ada di submission
    # TotalSubmissions: int = 0 
    TotalReports: int = 0
    TotalFuelLiters: float = 0.0
    TotalRupiahSpent: float = 0.0
    LastRefuelDate: datetime | None = None
    
class VehicleDetailResponse(MyVehicleResponse):
    RecentRefuelHistory: List[RefuelHistoryItem] = []

# --- Submission Schemas ---
class SubmissionCreate(BaseModel):
    KodeUnik: str
    CreatorID: int
    ReceiverID: int
    TotalCashAdvance: float
    Description: str | None = None
    Date: datetime 
    # VehicleID REMOVED
    Status: SubmissionStatusEnum | None = None

class SubmissionUpdate(BaseModel):
    KodeUnik: str | None = None
    CreatorID: int | None = None
    ReceiverID: int | None = None
    TotalCashAdvance: float | None = None
    # VehicleID REMOVED
    Status: SubmissionStatusEnum | None = None

class SubmissionResponse(BaseModel):
    ID: int
    KodeUnik: str
    Creator: UserSimpleResponse # Nested User
    Receiver: UserSimpleResponse # Nested User
    # Vehicle REMOVED
    TotalCashAdvance: float
    Status: SubmissionStatusEnum
    created_at: datetime
    Logs: List[SubmissionLogResponse] = Field(default_factory=list) # Array of Logs

    model_config = ConfigDict(from_attributes=True)

class SubmissionSummary(BaseModel):
    month: int
    year: int
    total_submissions: int
    total_pending: int
    total_accepted: int
    total_rejected: int
    total_cash_advance: float
    total_cash_advance_accepted: float
    total_cash_advance_rejected: float
    total_cash_advance_pending: float

class SubmissionMonthlyReport(BaseModel):
    summary: SubmissionSummary
    details: List[SubmissionResponse]

# --- Report Schemas ---
class ReportCreate(BaseModel):
    KodeUnik: str
    UserID: int
    VehicleID: int
    AmountRupiah: float
    AmountLiter: float
    Description: str | None = None
    Status: ReportStatusEnum | None = None
    Latitude: float | None = None
    Longitude: float | None = None
    VehiclePhysicalPhotoPath: str | None = None
    OdometerPhotoPath: str | None = None
    InvoicePhotoPath: str | None = None
    MyPertaminaPhotoPath: str | None = None
    Odometer: int | None = None

class ReportUpdate(BaseModel):
    KodeUnik: str | None = None
    UserID: int | None = None
    VehicleID: int | None = None
    AmountRupiah: float | None = None
    AmountLiter: float | None = None
    Description: str | None = None
    Status: ReportStatusEnum | None = None
    Latitude: float | None = None
    Longitude: float | None = None
    VehiclePhysicalPhotoPath: str | None = None
    OdometerPhotoPath: str | None = None
    InvoicePhotoPath: str | None = None
    MyPertaminaPhotoPath: str | None = None
    Odometer: int | None = None

class ReportResponse(BaseModel):
    ID: int
    KodeUnik: str
    User: UserSimpleResponse # Nested
    Vehicle: VehicleSimpleResponse # Nested
    AmountRupiah: float
    AmountLiter: float
    Description: str | None = None
    Status: ReportStatusEnum
    Timestamp: datetime
    Latitude: float | None = None
    Longitude: float | None = None
    VehiclePhysicalPhotoPath: str | None = None
    OdometerPhotoPath: str | None = None
    InvoicePhotoPath: str | None = None
    MyPertaminaPhotoPath: str | None = None
    Odometer: int | None = None
    Logs: List[ReportLogResponse] = Field(default_factory=list) # Array of Logs

    model_config = ConfigDict(from_attributes=True)

class ReportStatusUpdateRequest(BaseModel):
    Status: ReportStatusEnum
    Notes: str | None = None

class MyReportResponse(ReportResponse):
    SubmissionStatus: str | None = None
    SubmissionTotal: float | None = None

class ReportDetailResponse(ReportResponse):
    Submission: SubmissionResponse | None = None # Full Nested Submission

# --- Stats Schemas ---
class MonthlyData(BaseModel):
    month: int
    value: float

class PicStatResponse(BaseModel):
    vehicle_count: int
    report_count: int
    average: float
    money_usage: List[MonthlyData]

class KadisStatResponse(BaseModel):
    dinas_proposal_count: int
    dinas_report_count: int
    dinas_proposal_monthly: List[MonthlyData]
    dinas_proposal_average: float
    dinas_money_usage_monthly: List[MonthlyData]
    dinas_money_usage_average: float

class AdminStatResponse(BaseModel):
    dinas_vehicle_count: int
    dinas_users_count: int
    dinas_report_pending_count: int
    dinas_proposal_made_count: int
    dinas_proposal_monthly: List[MonthlyData]
    dinas_proposal_average: float
    dinas_money_usage_monthly: List[MonthlyData]

class UserCountByDinas(BaseModel):
    dinas_id: int | None
    dinas_nama: str
    total_users: int

# --- QR Schemas ---
class QRAssignRequest(BaseModel):
    NIP: str
    UniqueCode: str
    DinasID: int

class QRGetResponse(BaseModel):
    code: str | None = None
    expiresAt: str | None = None

class QRScanRequest(BaseModel):
    kode_unik: str