from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, relationship

from database.database import Base

# --- Enums ---
# Menggunakan (str, enum.Enum) agar otomatis serialize sebagai string di API

class RoleEnum(str, enum.Enum):
    admin = "admin"
    kepala_dinas = "kepala_dinas"
    pic = "pic"


class VehicleStatusEnum(str, enum.Enum):
    active = "Active"
    nonactive = "Nonactive"


class SubmissionStatusEnum(str, enum.Enum):
    accepted = "Accepted"
    rejected = "Rejected"
    pending = "Pending"


class ReportStatusEnum(str, enum.Enum):
    pending = "Pending"
    reviewed = "Reviewed"
    accepted = "Accepted"
    rejected = "Rejected"


class PurposeEnum(str, enum.Enum):
    register = "register"
    password_reset = "password_reset"
    otp = "otp"


# --- Association Tables ---

user_vehicle_association = Table(
    "user_vehicles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("vehicle_id", Integer, ForeignKey("vehicles.id"), primary_key=True),
)


# --- Reference Models ---

class WalletType(Base):
    """Model untuk jenis dompet (e.g. Cash, Gopay)."""
    __tablename__ = "wallet_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nama = Column(String(100), nullable=False)

    # Relationships
    wallets = relationship("Wallet", back_populates="wallet_type")


class VehicleType(Base):
    """Model untuk jenis kendaraan (e.g. Mobil Dinas, Motor)."""
    __tablename__ = "vehicle_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nama = Column(String(100), nullable=False)

    # Relationships
    vehicles = relationship("Vehicle", back_populates="vehicle_type")


class Dinas(Base):
    """Model untuk Dinas/Instansi."""
    __tablename__ = "dinas"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nama = Column(String(255), nullable=False)

    # Relationships
    users = relationship("User", back_populates="dinas")
    vehicles = relationship("Vehicle", back_populates="dinas")


# --- User & Auth Models ---

class User(Base):
    """Model untuk Pengguna Sistem."""
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("nip", name="uq_users_nip"),)

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nip = Column(String(50), nullable=False, unique=True)
    role = Column(SAEnum(RoleEnum), nullable=False)
    nama_lengkap = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    no_telepon = Column(String(20))
    password = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False, server_default="0", nullable=False)
    dinas_id = Column(Integer, ForeignKey("dinas.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    dinas = relationship("Dinas", back_populates="users")
    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Submission Relationships
    created_submissions = relationship(
        "Submission", 
        back_populates="creator", 
        foreign_keys="Submission.creator_id"
    )
    received_submissions = relationship(
        "Submission", 
        back_populates="receiver", 
        foreign_keys="Submission.receiver_id"
    )
    
    reports = relationship("Report", back_populates="user")
    unique_codes = relationship("UniqueCodeGenerator", back_populates="user", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", secondary=user_vehicle_association, back_populates="owners")


class Wallet(Base):
    """Model untuk Dompet Digital."""
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    saldo = Column(Numeric(15, 2), nullable=False, server_default="0.00")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    wallet_type_id = Column(Integer, ForeignKey("wallet_types.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="wallet")
    wallet_type = relationship("WalletType", back_populates="wallets")


class UniqueCodeGenerator(Base):
    """Model untuk Kode OTP/QR/Reset Password."""
    __tablename__ = "unique_code_generators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    kode_unik = Column(String(100), nullable=False)
    expired_at = Column(DateTime(timezone=True), nullable=False)
    purpose = Column(SAEnum(PurposeEnum), nullable=False)

    # Relationships
    user = relationship("User", back_populates="unique_codes")


# --- Asset Models ---

class Vehicle(Base):
    """Model untuk Kendaraan Dinas."""
    __tablename__ = "vehicles"
    __table_args__ = (UniqueConstraint("plat", name="uq_vehicles_plat"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    nama = Column(String(255), nullable=False)
    plat = Column(String(15), nullable=False, unique=True)
    kapasitas_mesin = Column(Integer)
    vehicle_type_id = Column(Integer, ForeignKey("vehicle_types.id"), nullable=False)
    odometer = Column(BigInteger, server_default="0")
    status = Column(
        SAEnum(VehicleStatusEnum), 
        nullable=False, 
        server_default=VehicleStatusEnum.active.value
    )
    
    # Detail Spesifikasi
    jenis_bensin = Column(String(50))
    merek = Column(String(100))
    tipe_transmisi = Column(String(50), nullable=True) 
    total_fuel_bar = Column(Integer, default=8)
    current_fuel_bar = Column(Integer, default=0)
    
    # Assets & UI Config
    foto_fisik = Column(Text)
    asset_icon_name = Column(String(50), nullable=True)
    asset_icon_color = Column(String(50), nullable=True)
    
    # Ownership
    dinas_id = Column(Integer, ForeignKey("dinas.id"), nullable=True)
   
    # Relationships
    dinas = relationship("Dinas", back_populates="vehicles")
    vehicle_type = relationship("VehicleType", back_populates="vehicles")
    reports = relationship("Report", back_populates="vehicle")
    owners = relationship("User", secondary=user_vehicle_association, back_populates="vehicles")


# --- Transaction Models ---

class Submission(Base):
    """Model untuk Pengajuan Anggaran/BBM."""
    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("kode_unik", name="uq_submissions_kode_unik"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    kode_unik = Column(String(100), nullable=False, unique=True)
    status = Column(
        SAEnum(SubmissionStatusEnum), 
        nullable=False, 
        server_default=SubmissionStatusEnum.pending.value
    )
    
    # Actors
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dinas_id = Column(Integer, ForeignKey("dinas.id"), nullable=True)

    # Details
    total_cash_advance = Column(Numeric(15, 2), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    dinas = relationship("Dinas", foreign_keys=[dinas_id])
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_submissions")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_submissions")
    logs = relationship(
        "SubmissionLog", 
        back_populates="submission", 
        cascade="all, delete-orphan", 
        order_by="SubmissionLog.timestamp"
    )


class Report(Base):
    """Model Laporan Realisasi (Struk BBM)."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kode_unik = Column(String(100), nullable=False) 
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    dinas_id = Column(Integer, ForeignKey("dinas.id"), nullable=True)

    # Financial & Metrics
    amount_rupiah = Column(Numeric(15, 2), nullable=False)
    amount_liter = Column(Numeric(10, 3), nullable=False)
    odometer = Column(BigInteger)
    
    # Meta
    description = Column(Text)
    status = Column(
        SAEnum(ReportStatusEnum), 
        nullable=False, 
        server_default=ReportStatusEnum.pending.value
    )
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Location
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    
    # Evidence Photos
    vehicle_physical_photo_path = Column(Text)
    odometer_photo_path = Column(Text)
    invoice_photo_path = Column(Text)
    my_pertamina_photo_path = Column(Text)

    # Relationships
    dinas = relationship("Dinas", foreign_keys=[dinas_id])
    user = relationship("User", back_populates="reports")
    vehicle = relationship("Vehicle", back_populates="reports")
    logs = relationship(
        "ReportLog", 
        back_populates="report", 
        cascade="all, delete-orphan", 
        order_by="ReportLog.timestamp"
    )


# --- History/Log Models ---

class SubmissionLog(Base):
    """Model Log History untuk Submission."""
    __tablename__ = "submission_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    status = Column(SAEnum(SubmissionStatusEnum), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    submission = relationship("Submission", back_populates="logs")
    updater = relationship("User", foreign_keys=[updated_by_user_id])


class ReportLog(Base):
    """Model Log History untuk Report."""
    __tablename__ = "report_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    status = Column(SAEnum(ReportStatusEnum), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    report = relationship("Report", back_populates="logs")
    updater = relationship("User", foreign_keys=[updated_by_user_id])