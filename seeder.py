import random
from faker import Faker
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# --- IMPORT MODEL ---
from config import get_settings
from model.models import (
    Base, User, RoleEnum, Dinas, WalletType, VehicleType, Wallet, 
    Vehicle, VehicleStatusEnum, Submission, SubmissionStatusEnum, 
    SubmissionLog, Report, ReportLog, ReportStatusEnum
)

# --- KONFIGURASI LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- KONFIGURASI DB ---
settings = get_settings()
engine = create_engine(settings.database_url)
fake = Faker('id_ID')

DEFAULT_PASSWORD_HASH = "$bcrypt-sha256$v=2,t=2b,r=12$aNMkUf1Xp0HMCDmku3XgM.$TR1hRdt9SZ66CdlnepazFEQcM.tkb4a" 

def seed_database():
    with Session(engine) as session:
        logger.info("🌱 Memulai proses seeding database...")

        # 1. Reference Data
        logger.info("... 1. Seeding Data Referensi")
        
        dinas_list = ["Dinas Komunikasi dan Informatika", "Dinas Pekerjaan Umum", "Dinas Perhubungan", "Dinas Kesehatan"]
        dinas_objs = []
        for d_nama in dinas_list:
            dinas = session.execute(select(Dinas).where(Dinas.Nama == d_nama)).scalar_one_or_none()
            if not dinas:
                dinas = Dinas(Nama=d_nama)
                session.add(dinas)
                session.flush()
            dinas_objs.append(dinas)
        
        w_types = ["Linkaja", "OVO", "Gopay"]
        wallet_types = []
        for w_name in w_types:
            wt = session.execute(select(WalletType).where(WalletType.Nama == w_name)).scalar_one_or_none()
            if not wt:
                wt = WalletType(Nama=w_name)
                session.add(wt)
                session.flush()
            wallet_types.append(wt)

        v_types = ["motor", "mobil", "lainnnya"]
        vehicle_types = []
        for v_name in v_types:
            vt = session.execute(select(VehicleType).where(VehicleType.Nama == v_name)).scalar_one_or_none()
            if not vt:
                vt = VehicleType(Nama=v_name)
                session.add(vt)
                session.flush()
            vehicle_types.append(vt)

        # 2. Users & Wallets
        logger.info("... 2. Seeding Users & Wallets")
        
        users = []
        specific_users = [
            ("100000000000000001", "Admin Sistem", RoleEnum.admin, 0),
            ("100000000000000002", "Budi Santoso (Kadis)", RoleEnum.kepala_dinas, 0),
            ("100000000000000003", "Andi Lapangan (PIC)", RoleEnum.pic, 0),
            ("100000000000000004", "Siti Staff (PIC)", RoleEnum.pic, 0),
            ("100000000000000005", "Dr. Ratna (Kadis Kes)", RoleEnum.kepala_dinas, 3),
        ]

        for nip, name, role, d_idx in specific_users:
            user = session.execute(select(User).where(User.NIP == nip)).scalar_one_or_none()
            if not user:
                user = User(
                    NIP=nip,
                    NamaLengkap=name,
                    Email=f"{name.split()[0].lower()}@gmail.com",
                    Role=role,
                    Password=DEFAULT_PASSWORD_HASH,
                    NoTelepon=fake.phone_number(),
                    isVerified=True,
                    DinasID=dinas_objs[d_idx].ID
                )
                session.add(user)
                session.flush()
                
                wallet = Wallet(
                    UserID=user.ID,
                    WalletTypeID=random.choice(wallet_types).ID,
                    Saldo=random.choice([5000000, 10000000, 25000000])
                )
                session.add(wallet)
            users.append(user)

        # 3. Vehicles
        logger.info("... 3. Seeding Vehicles")
        
        vehicles = []
        icons = [
            ("AppAssets.ilustCar1", "AppColors.primary70"), ("AppAssets.ilustCar2", "AppColors.primary50"), ("AppAssets.ilustMotorcycle1", "AppColors.secondary70"), 
            ("AppAssets.ilustOthers1", "AppColors.tertiary30")
        ]

        for _ in range(20):
            plat = f"DK {fake.random_int(1000, 9999)} {fake.random_uppercase_letter()}{fake.random_uppercase_letter()}"
            if session.execute(select(Vehicle).where(Vehicle.Plat == plat)).scalar_one_or_none():
                continue

            icon_data = random.choice(icons)
            vt = random.choice(vehicle_types)
            
            veh = Vehicle(
                Nama=f"{vt.Nama} - {fake.first_name()}",
                Plat=plat,
                KapasitasMesin=random.choice([150, 250, 1500, 2500]),
                VehicleTypeID=vt.ID,
                Odometer=random.randint(1000, 100000),
                Status=VehicleStatusEnum.Active,
                JenisBensin=random.choice(["Pertalite", "Pertamax", "Solar"]),
                Merek=random.choice(["Toyota", "Honda", "Suzuki", "Mitsubishi"]),
                FotoFisik=f"https://source.unsplash.com/random/400x300/?vehicle&sig={random.randint(1,1000)}",
                AssetIconName=icon_data[0],
                AssetIconColor=icon_data[1]
            )
            session.add(veh)
            vehicles.append(veh)
        session.flush()

        # 4. Assign Vehicles
        logger.info("... 4. Assigning Vehicles to Users")
        pic_users = [u for u in users if u.Role == RoleEnum.pic]
        for veh in vehicles:
            owners = random.sample(pic_users, k=random.randint(1, 2))
            for owner in owners:
                if veh not in owner.vehicles:
                    owner.vehicles.append(veh)
        session.flush()

        # 5. Submissions
        logger.info("... 5. Seeding Submissions & Logs")
        
        submissions = []
        kadis_users = [u for u in users if u.Role == RoleEnum.kepala_dinas]

        for _ in range(50):
            creator = random.choice(pic_users)
            receiver = random.choice(kadis_users)
            
            # VEHICLE TIDAK DIPILIH SAAT SUBMISSION

            final_status = random.choices(
                [SubmissionStatusEnum.Pending, SubmissionStatusEnum.Accepted, SubmissionStatusEnum.Rejected],
                weights=[20, 60, 20], k=1
            )[0]

            created_at = fake.date_time_between(start_date='-6m', end_date='now')
            
            sub = Submission(
                KodeUnik=f"SUB-{created_at.strftime('%Y%m')}-{fake.random_number(digits=4)}",
                CreatorID=creator.ID,
                ReceiverID=receiver.ID,
                TotalCashAdvance=random.choice([100000, 250000, 500000, 1000000]),
                # VehicleID REMOVED
                Status=final_status,
                created_at=created_at
            )
            session.add(sub)
            session.flush()

            session.add(SubmissionLog(
                SubmissionID=sub.ID,
                Status=SubmissionStatusEnum.Pending,
                Timestamp=created_at,
                UpdatedByUserID=creator.ID,
                Notes="Submission dibuat"
            ))

            if final_status != SubmissionStatusEnum.Pending:
                decision_time = created_at + timedelta(days=random.randint(1, 3))
                session.add(SubmissionLog(
                    SubmissionID=sub.ID,
                    Status=final_status,
                    Timestamp=decision_time,
                    UpdatedByUserID=receiver.ID,
                    Notes="Disetujui untuk kegiatan operasional" if final_status == SubmissionStatusEnum.Accepted else "Ditolak, anggaran habis"
                ))
                
                if final_status == SubmissionStatusEnum.Accepted:
                    submissions.append((sub, decision_time))

        # 6. Reports
        logger.info("... 6. Seeding Reports & Logs")

        for sub, approved_date in submissions:
            if random.random() > 0.2:
                report_date = approved_date + timedelta(days=random.randint(1, 5))
                report_status = random.choices([ReportStatusEnum.Pending, ReportStatusEnum.Accepted], weights=[30, 70], k=1)[0]
                
                # VEHICLE DIPILIH SAAT REPORT
                # Pilih kendaraan yang dimiliki user atau random
                creator_user = session.get(User, sub.CreatorID)
                if creator_user and creator_user.vehicles:
                    selected_vehicle = random.choice(creator_user.vehicles)
                else:
                    selected_vehicle = random.choice(vehicles)

                report = Report(
                    KodeUnik=sub.KodeUnik,
                    UserID=sub.CreatorID,
                    VehicleID=selected_vehicle.ID,
                    AmountRupiah=sub.TotalCashAdvance, # Asumsi habis semua
                    AmountLiter=float(sub.TotalCashAdvance) / 10000,
                    Description="Pengisian BBM Full Tank",
                    Status=report_status,
                    Timestamp=report_date,
                    Latitude=fake.latitude(),
                    Longitude=fake.longitude(),
                    VehiclePhysicalPhotoPath="https://via.placeholder.com/150",
                    OdometerPhotoPath="https://via.placeholder.com/150",
                    InvoicePhotoPath="https://via.placeholder.com/150",
                    MyPertaminaPhotoPath="https://via.placeholder.com/150",
                    Odometer=random.randint(50000, 100000)
                )
                session.add(report)
                session.flush()

                session.add(ReportLog(
                    ReportID=report.ID,
                    Status=ReportStatusEnum.Pending,
                    Timestamp=report_date,
                    UpdatedByUserID=sub.CreatorID,
                    Notes="Laporan diupload"
                ))

                if report_status == ReportStatusEnum.Accepted:
                    review_date = report_date + timedelta(hours=random.randint(2, 24))
                    session.add(ReportLog(
                        ReportID=report.ID,
                        Status=ReportStatusEnum.Accepted,
                        Timestamp=review_date,
                        UpdatedByUserID=sub.ReceiverID,
                        Notes="Bukti valid, diterima."
                    ))

        session.commit()
        logger.info("✅ SEEDING SELESAI! Database siap digunakan.")

if __name__ == "__main__":
    seed_database()