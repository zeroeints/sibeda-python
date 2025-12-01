from __future__ import annotations
import enum
from sqlalchemy import (
    Column, Integer, String, Text, BigInteger, Numeric, DateTime, 
    ForeignKey, Enum as SAEnum, UniqueConstraint, func, Boolean, Table
)
from sqlalchemy.orm import relationship
from database.database import Base

# Enums
class RoleEnum(enum.Enum):
    admin = "admin"
    kepala_dinas = "kepala_dinas"
    pic = "pic"

class VehicleStatusEnum(enum.Enum):
    Active = "Active"
    Nonactive = "Nonactive"

class SubmissionStatusEnum(enum.Enum):
    Accepted = "Accepted"
    Rejected = "Rejected"
    Pending = "Pending"

class ReportStatusEnum(enum.Enum):
    Pending = "Pending"
    Reviewed = "Reviewed"
    Accepted = "Accepted"
    Rejected = "Rejected"

class PurposeEnum(enum.Enum):
    register = "register"
    password_reset = "password_reset"
    otp = "otp"

# --- Tables ---

class WalletType(Base):
    __tablename__ = "WalletType"
    ID = Column(Integer, primary_key=True, autoincrement=True)
    Nama = Column(String(100), nullable=False)
    wallets = relationship("Wallet", back_populates="wallet_type")

class VehicleType(Base):
    __tablename__ = "VehicleType"
    ID = Column(Integer, primary_key=True, autoincrement=True)
    Nama = Column(String(100), nullable=False)
    vehicles = relationship("Vehicle", back_populates="vehicle_type")

class Dinas(Base):
    __tablename__ = "Dinas"
    ID = Column(Integer, primary_key=True, autoincrement=True, index=True)
    Nama = Column(String(255), nullable=False)
    users = relationship("User", back_populates="dinas")
    vehicles = relationship("Vehicle", back_populates="dinas")

user_vehicle_association = Table(
    "user_vehicle",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("User.ID"), primary_key=True),
    Column("vehicle_id", Integer, ForeignKey("Vehicle.ID"), primary_key=True),
)

class User(Base):
    __tablename__ = "User"
    __table_args__ = (UniqueConstraint("NIP", name="uq_user_nip"),)

    ID = Column(Integer, primary_key=True, autoincrement=True, index=True)
    NIP = Column(String(50), nullable=False, unique=True)
    Role = Column(SAEnum(RoleEnum), nullable=False)
    NamaLengkap = Column(String(255), nullable=False)
    Email = Column(String(255), nullable=False)
    NoTelepon = Column(String(20))
    Password = Column(String(255), nullable=False)
    isVerified = Column(Boolean, default=False, server_default="0", nullable=False)
    DinasID = Column(Integer, ForeignKey("Dinas.ID", ondelete="SET NULL"), nullable=True)

    dinas = relationship("Dinas", back_populates="users")
    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Submissions
    created_submissions = relationship("Submission", back_populates="creator", foreign_keys="Submission.CreatorID")
    received_submissions = relationship("Submission", back_populates="receiver", foreign_keys="Submission.ReceiverID")
    
    reports = relationship("Report", back_populates="user")
    unique_codes = relationship("UniqueCodeGenerator", back_populates="user", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", secondary=user_vehicle_association, back_populates="owners")

class Wallet(Base):
    __tablename__ = "Wallet"
    ID = Column(Integer, primary_key=True, autoincrement=True)
    Saldo = Column(Numeric(15, 2), nullable=False, server_default="0.00")
    UserID = Column(Integer, ForeignKey("User.ID", ondelete="CASCADE"), nullable=False, unique=True)
    WalletTypeID = Column(Integer, ForeignKey("WalletType.ID"), nullable=False)

    user = relationship("User", back_populates="wallet")
    wallet_type = relationship("WalletType", back_populates="wallets")

class Vehicle(Base):
    __tablename__ = "Vehicle"
    __table_args__ = (UniqueConstraint("Plat", name="uq_vehicle_plat"),)

    ID = Column(Integer, primary_key=True, autoincrement=True)
    Nama = Column(String(255), nullable=False)
    Plat = Column(String(15), nullable=False, unique=True)
    KapasitasMesin = Column(Integer)
    VehicleTypeID = Column(Integer, ForeignKey("VehicleType.ID"), nullable=False)
    Odometer = Column(BigInteger, server_default="0")
    Status = Column(SAEnum(VehicleStatusEnum), nullable=False, server_default=VehicleStatusEnum.Active.value)
    JenisBensin = Column(String(50))
    Merek = Column(String(100))
    FotoFisik = Column(Text)
    AssetIconName = Column(String(50), nullable=True)
    AssetIconColor = Column(String(50), nullable=True)
    TipeTransmisi = Column(String(50), nullable=True) # atau Enum
    TotalFuelBar = Column(Integer, default=8)         # Default 8 bar misal
    CurrentFuelBar = Column(Integer, default=0)
    DinasID = Column(Integer, ForeignKey("Dinas.ID"), nullable=True) # Nullable jika ada kendaraan umum/pool
   
    dinas = relationship("Dinas", back_populates="vehicles")
    vehicle_type = relationship("VehicleType", back_populates="vehicles")
    reports = relationship("Report", back_populates="vehicle")
    # Submissions relationship removed
    owners = relationship("User", secondary=user_vehicle_association, back_populates="vehicles")

class UniqueCodeGenerator(Base):
    __tablename__ = "UniqueCodeGenerator"
    ID = Column(Integer, primary_key=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey("User.ID", ondelete="CASCADE"), nullable=False)
    KodeUnik = Column(String(100), nullable=False)
    expired_at = Column(DateTime(timezone=True), nullable=False)
    Purpose = Column(SAEnum(PurposeEnum), nullable=False)
    user = relationship("User", back_populates="unique_codes")

class Submission(Base):
    __tablename__ = "Submission"
    __table_args__ = (UniqueConstraint("KodeUnik", name="uq_submission_kodeunik"),)

    ID = Column(Integer, primary_key=True, autoincrement=True)
    KodeUnik = Column(String(100), nullable=False, unique=True)
    Status = Column(SAEnum(SubmissionStatusEnum), nullable=False, server_default=SubmissionStatusEnum.Pending.value)
    CreatorID = Column(Integer, ForeignKey("User.ID"), nullable=False)
    ReceiverID = Column(Integer, ForeignKey("User.ID"), nullable=False)
    TotalCashAdvance = Column(Numeric(15, 2), nullable=False)
    Description = Column(Text, nullable=True)
    Date = Column(DateTime(timezone=True), nullable=False)
    # VehicleID REMOVED
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    DinasID = Column(Integer, ForeignKey("Dinas.ID"), nullable=True) # Nullable untuk data lama, tapi sebaiknya Not Null

    dinas = relationship("Dinas", foreign_keys=[DinasID])
    creator = relationship("User", foreign_keys=[CreatorID], back_populates="created_submissions")
    receiver = relationship("User", foreign_keys=[ReceiverID], back_populates="received_submissions")
    # Vehicle relationship REMOVED
    logs = relationship("SubmissionLog", back_populates="submission", cascade="all, delete-orphan", order_by="SubmissionLog.Timestamp")

class SubmissionLog(Base):
    __tablename__ = "SubmissionLog"
    ID = Column(Integer, primary_key=True, autoincrement=True)
    SubmissionID = Column(Integer, ForeignKey("Submission.ID", ondelete="CASCADE"), nullable=False)
    Status = Column(SAEnum(SubmissionStatusEnum), nullable=False)
    Timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    UpdatedByUserID = Column(Integer, ForeignKey("User.ID"), nullable=True)
    Notes = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="logs")
    updater = relationship("User", foreign_keys=[UpdatedByUserID])

class Report(Base):
    __tablename__ = "Report"
    ID = Column(Integer, primary_key=True, autoincrement=True)
    KodeUnik = Column(String(100), nullable=False) 
    UserID = Column(Integer, ForeignKey("User.ID"), nullable=False)
    VehicleID = Column(Integer, ForeignKey("Vehicle.ID"), nullable=False)
    AmountRupiah = Column(Numeric(15, 2), nullable=False)
    AmountLiter = Column(Numeric(10, 3), nullable=False)
    Description = Column(Text)
    Status = Column(SAEnum(ReportStatusEnum), nullable=False, server_default=ReportStatusEnum.Pending.value)
    Timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    Latitude = Column(Numeric(10, 8))
    Longitude = Column(Numeric(11, 8))
    VehiclePhysicalPhotoPath = Column(Text)
    OdometerPhotoPath = Column(Text)
    InvoicePhotoPath = Column(Text)
    MyPertaminaPhotoPath = Column(Text)
    Odometer = Column(BigInteger)
    DinasID = Column(Integer, ForeignKey("Dinas.ID"), nullable=True)

    dinas = relationship("Dinas", foreign_keys=[DinasID])
    user = relationship("User", back_populates="reports")
    vehicle = relationship("Vehicle", back_populates="reports")
    logs = relationship("ReportLog", back_populates="report", cascade="all, delete-orphan", order_by="ReportLog.Timestamp")

class ReportLog(Base):
    __tablename__ = "ReportLog"
    ID = Column(Integer, primary_key=True, autoincrement=True)
    ReportID = Column(Integer, ForeignKey("Report.ID", ondelete="CASCADE"), nullable=False)
    Status = Column(SAEnum(ReportStatusEnum), nullable=False)
    Timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    UpdatedByUserID = Column(Integer, ForeignKey("User.ID"), nullable=True)
    Notes = Column(Text, nullable=True)

    report = relationship("Report", back_populates="logs")
    updater = relationship("User", foreign_keys=[UpdatedByUserID])