from __future__ import annotations
from enum import Enum
from typing import Generic, TypeVar, List, Dict, Annotated
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator, ConfigDict, PlainSerializer


def serialize_datetime_utc(dt: datetime | None) -> str | None:
    """Serialize datetime to ISO format with 'Z' suffix for UTC."""
    if dt is None:
        return None
    # If naive datetime, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Convert to UTC and format with 'Z'
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# Custom datetime type that serializes to UTC with 'Z' suffix
DateTimeUTC = Annotated[datetime, PlainSerializer(serialize_datetime_utc, return_type=str)]

T = TypeVar("T")

# --- Enums ---

class RoleEnum(str, Enum):
    admin = "admin"
    kepala_dinas = "kepala_dinas"
    pic = "pic"

class VehicleStatusEnum(str, Enum):
    active = "Active"
    nonactive = "Nonactive"

class SubmissionStatusEnum(str, Enum):
    accepted = "Accepted"
    rejected = "Rejected"
    pending = "Pending"

class ReportStatusEnum(str, Enum):
    pending = "Pending"
    reviewed = "Reviewed"
    accepted = "Accepted"
    rejected = "Rejected"


# --- Base Response Wrappers ---

class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None

class PagedListData(BaseModel, Generic[T]):
    list: List[T]
    limit: int
    offset: int
    has_more: bool
    month: int | None = None
    year: int | None = None
    stat: Dict[str, int] = Field(default_factory=dict)

class SuccessListResponse(SuccessResponse[List[T]], Generic[T]):
    pass

class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    message: str | None = None
    pagination: Dict[str, int | bool]

class Message(BaseModel):
    detail: str


# --- Simple Models (Nested Responses) ---

class UserSimpleResponse(BaseModel):
    id: int
    nip: str
    nama_lengkap: str
    role: RoleEnum
    email: str
    no_telepon: str | None = None
    
    model_config = ConfigDict(from_attributes=True)

class VehicleTypeResponse(BaseModel):
    id: int
    nama: str
    
    model_config = ConfigDict(from_attributes=True)

class DinasSimpleResponse(BaseModel):
    id: int
    nama: str
    
    model_config = ConfigDict(from_attributes=True)

class VehicleSimpleResponse(BaseModel):
    id: int
    nama: str
    plat: str
    status: VehicleStatusEnum
    
    # Nested Relationships
    vehicle_type: VehicleTypeResponse | None = None
    
    asset_icon_name: str | None = None
    asset_icon_color: str | None = None
    
    model_config = ConfigDict(from_attributes=True)


# --- Log Models ---

class SubmissionLogResponse(BaseModel):
    id: int
    status: SubmissionStatusEnum
    timestamp: DateTimeUTC
    updated_by_user_id: int | None = None
    notes: str | None = None
    
    model_config = ConfigDict(from_attributes=True)

class ReportLogResponse(BaseModel):
    id: int
    status: ReportStatusEnum
    timestamp: DateTimeUTC
    updated_by_user_id: int | None = None
    notes: str | None = None
    
    model_config = ConfigDict(from_attributes=True)


# --- User Schemas ---

class UserBase(BaseModel):
    nip: str = Field(..., min_length=18, max_length=50)
    nama_lengkap: str
    email: str
    no_telepon: str | None = None

    @field_validator("nip")
    @classmethod
    def nip_strip(cls, v: str) -> str:
        return v.strip()

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    nip: str | None = None
    nama_lengkap: str | None = None
    email: str | None = None
    no_telepon: str | None = None
    password: str | None = None
    role: RoleEnum | None = None
    dinas_id: int | None = None

class UserResponse(UserBase):
    id: int
    role: RoleEnum
    is_verified: bool | None = None
    
    # Relationships
    dinas: DinasSimpleResponse | None = None
    
    model_config = ConfigDict(from_attributes=True)

class UserDetailResponse(UserResponse):
    # Field tambahan hasil query manual (tetap butuh alias jika query mengembalikan nama spesifik, 
    # tapi jika query di service sudah disesuaikan ke snake_case, alias bisa dihapus).
    # Kita asumsikan Service juga akan diperbaiki untuk return dict dengan key snake_case.
    wallet_id: int | None = None
    wallet_saldo: float | None = None
    wallet_type: str | None = None
    
    total_submissions_created: int = 0
    total_submissions_received: int = 0
    
    model_config = ConfigDict(from_attributes=True)

class UserBalanceResponse(BaseModel):
    user: UserSimpleResponse
    dinas_nama: str | None = None
    wallet_id: int
    saldo: float
    wallet_type: str | None = None
    
    model_config = ConfigDict(from_attributes=True)


# --- Auth Schemas ---

class LoginJSON(BaseModel):
    nip: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenClaims(BaseModel):
    sub: str | None = None
    id: int | None = None
    role: List[str] | str | None = None
    exp: int | None = None

class TokenVerifyData(BaseModel):
    valid: bool
    claims: TokenClaims | None = None
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
    nama: str

class DinasResponse(DinasBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class WalletTypeBase(BaseModel):
    nama: str

class WalletTypeResponse(WalletTypeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class WalletCreate(BaseModel):
    user_id: int
    wallet_type_id: int
    saldo: float = 0

class WalletResponse(BaseModel):
    id: int
    user: UserSimpleResponse
    wallet_type: WalletTypeResponse
    saldo: float
    
    model_config = ConfigDict(from_attributes=True)

class WalletUpdate(BaseModel):
    user_id: int | None = None
    wallet_type_id: int | None = None
    saldo: float | None = None


# --- Vehicle Schemas ---

class VehicleCreate(BaseModel):
    nama: str
    plat: str
    vehicle_type_id: int
    dinas_id: int | None = None
    
    kapasitas_mesin: int | None = None
    odometer: int | None = None
    status: VehicleStatusEnum | None = None
    jenis_bensin: str | None = None
    merek: str | None = None
    
    foto_fisik: str | None = None
    asset_icon_name: str | None = None
    asset_icon_color: str | None = None
    tipe_transmisi: str | None = None
    total_fuel_bar: int | None = None
    current_fuel_bar: int | None = None

class VehicleUpdate(BaseModel):
    nama: str | None = None
    plat: str | None = None
    vehicle_type_id: int | None = None
    dinas_id: int | None = None
    
    kapasitas_mesin: int | None = None
    odometer: int | None = None
    status: VehicleStatusEnum | None = None
    jenis_bensin: str | None = None
    merek: str | None = None
    
    foto_fisik: str | None = None
    asset_icon_name: str | None = None
    asset_icon_color: str | None = None

class VehicleTypeUpdate(BaseModel):
    nama: str | None = None

class VehicleResponse(BaseModel):
    id: int
    nama: str
    plat: str
    status: VehicleStatusEnum
    
    # Relations
    vehicle_type: VehicleTypeResponse | None = None
    dinas: DinasSimpleResponse | None = None
    
    kapasitas_mesin: int | None = None
    odometer: int | None = None
    jenis_bensin: str | None = None
    merek: str | None = None
    
    # Visuals
    foto_fisik: str | None = None
    asset_icon_name: str | None = None
    asset_icon_color: str | None = None
    
    tipe_transmisi: str | None = None
    total_fuel_bar: int | None = None
    current_fuel_bar: int | None = None
    dinas_id: int | None = None

    model_config = ConfigDict(from_attributes=True)

class VehicleAssignmentRequest(BaseModel):
    user_id: int

class UserAssignmentRequest(BaseModel):
    vehicle_id: int

class RefuelHistoryItem(BaseModel):
    id: int
    kode_unik: str
    amount_rupiah: float
    amount_liter: float
    timestamp: DateTimeUTC
    odometer: int | None = None
    
    model_config = ConfigDict(from_attributes=True)

class MyVehicleResponse(VehicleResponse):
    total_submissions: int = 0
    total_reports: int = 0
    total_fuel_liters: float = 0.0
    total_rupiah_spent: float = 0.0
    last_refuel_date: DateTimeUTC | None = None
    
class VehicleDetailResponse(MyVehicleResponse):
    recent_refuel_history: List[RefuelHistoryItem] = Field(default_factory=list)


# --- Submission Schemas ---

class SubmissionCreate(BaseModel):
    kode_unik: str
    creator_id: int
    receiver_id: int
    total_cash_advance: float
    description: str | None = None
    date: DateTimeUTC 
    status: SubmissionStatusEnum | None = None

class SubmissionUpdate(BaseModel):
    kode_unik: str | None = None
    creator_id: int | None = None
    receiver_id: int | None = None
    total_cash_advance: float | None = None
    status: SubmissionStatusEnum | None = None

class SubmissionResponse(BaseModel):
    id: int
    kode_unik: str
    
    # Relations
    creator: UserSimpleResponse
    receiver: UserSimpleResponse
    dinas: DinasSimpleResponse | None = None
    
    description: str | None = None
    date: DateTimeUTC | None = None
    
    total_cash_advance: float
    status: SubmissionStatusEnum
    created_at: DateTimeUTC
    
    logs: List[SubmissionLogResponse] = Field(default_factory=list)
    
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
    kode_unik: str
    user_id: int
    vehicle_id: int
    amount_rupiah: float
    amount_liter: float
    
    description: str | None = None
    status: ReportStatusEnum | None = None
    latitude: float | None = None
    longitude: float | None = None
    odometer: int | None = None
    
    vehicle_physical_photo_path: str | None = None
    odometer_photo_path: str | None = None
    invoice_photo_path: str | None = None
    my_pertamina_photo_path: str | None = None

class ReportUpdate(BaseModel):
    kode_unik: str | None = None
    user_id: int | None = None
    vehicle_id: int | None = None
    amount_rupiah: float | None = None
    amount_liter: float | None = None
    description: str | None = None
    status: ReportStatusEnum | None = None
    latitude: float | None = None
    longitude: float | None = None
    odometer: int | None = None
    
    vehicle_physical_photo_path: str | None = None
    odometer_photo_path: str | None = None
    invoice_photo_path: str | None = None
    my_pertamina_photo_path: str | None = None

class ReportResponse(BaseModel):
    id: int
    kode_unik: str
    
    # Relations
    user: UserSimpleResponse
    vehicle: VehicleSimpleResponse
    dinas: DinasSimpleResponse | None = None
    
    amount_rupiah: float
    amount_liter: float
    description: str | None = None
    status: ReportStatusEnum
    timestamp: DateTimeUTC
    latitude: float | None = None
    longitude: float | None = None
    
    # Photos
    vehicle_physical_photo_path: str | None = None
    odometer_photo_path: str | None = None
    invoice_photo_path: str | None = None
    my_pertamina_photo_path: str | None = None
    odometer: int | None = None
    
    logs: List[ReportLogResponse] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)

class ReportStatusUpdateRequest(BaseModel):
    status: ReportStatusEnum
    notes: str | None = None

class MyReportResponse(ReportResponse):
    submission_status: str | None = None
    submission_total: float | None = None

class ReportDetailResponse(ReportResponse):
    submission: SubmissionResponse | None = None


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
    nip: str
    unique_code: str
    dinas_id: int

class QRGetResponse(BaseModel):
    code: str | None = None
    expires_at: str | None = Field(default=None, serialization_alias="expiresAt") # camelCase untuk frontend

class QRScanRequest(BaseModel):
    kode_unik: str