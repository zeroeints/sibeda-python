import random
from faker import Faker
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select, text
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import logging

# --- SETUP ---
load_dotenv()
from config import get_settings
from model.models import (
    Base, User, RoleEnum, Dinas, WalletType, VehicleType, Wallet, 
    Vehicle, VehicleStatusEnum, Submission, SubmissionStatusEnum, 
    SubmissionLog, Report, ReportLog, ReportStatusEnum
)

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# DB Config
settings = get_settings()
engine = create_engine(settings.database_url)
fake = Faker('id_ID')

# Hash Password (password123)
PASSWORD_HASH = "$bcrypt-sha256$v=2,t=2b,r=12$aNMkUf1Xp0HMCDmku3XgM.$TR1hRdt9SZ66CdlnepazFEQcM.tkb4a" 

def get_status_vehicle(i):
    return VehicleStatusEnum.Active if i % 2 == 0 else VehicleStatusEnum.Nonactive

def seed_heavy_v2():
    with Session(engine) as session:
        logger.info("🚀 Memulai Seeding Khusus UI Testing (50% Full / 50% Null)...")

        # ==========================================
        # 0. CLEANUP (Opsional: Hapus data lama agar ID reset/bersih)
        # ==========================================
        # logger.warning("Cleaning up old data...")
        # session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        # session.execute(text("TRUNCATE TABLE ReportLog"))
        # session.execute(text("TRUNCATE TABLE SubmissionLog"))
        # session.execute(text("TRUNCATE TABLE Report"))
        # session.execute(text("TRUNCATE TABLE Submission"))
        # session.execute(text("TRUNCATE TABLE user_vehicle"))
        # session.execute(text("TRUNCATE TABLE Vehicle"))
        # session.execute(text("TRUNCATE TABLE Wallet"))
        # session.execute(text("TRUNCATE TABLE User"))
        # session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        # session.commit()

        # ==========================================
        # 1. REFERENCE DATA (Wajib Ada)
        # ==========================================
        logger.info("📦 Seeding Reference Data...")
        
        # 3 Dinas Utama
        dinas_list = []
        dinas_names = ["Dinas A (Testing)", "Dinas B (Testing)", "Dinas C (Testing)"]
        for d_name in dinas_names:
            d = session.execute(select(Dinas).where(Dinas.Nama == d_name)).scalar_one_or_none()
            if not d:
                d = Dinas(Nama=d_name)
                session.add(d)
                session.flush()
            dinas_list.append(d)

        # Wallet & Vehicle Types
        w_type = session.execute(select(WalletType).limit(1)).scalar_one_or_none()
        if not w_type:
            w_type = WalletType(Nama="Cash")
            session.add(w_type)
            session.flush()
        
        v_type_mobil = session.execute(select(VehicleType).where(VehicleType.Nama == "Mobil Dinas")).scalar_one_or_none()
        if not v_type_mobil:
            v_type_mobil = VehicleType(Nama="Mobil Dinas")
            session.add(v_type_mobil)
            session.flush()

        # ==========================================
        # 2. USERS (12 Total: 3 Admin, 3 Kadis, 6 PIC)
        # ==========================================
        logger.info("👥 Seeding 12 Users (Mix Null/Full Fields)...")
        
        users_created = []

        # -- A. 3 ADMINS --
        for i in range(3):
            is_full = (i % 2 == 0) # Genap = Full, Ganjil = Null
            admin = User(
                NIP=f"ADM{i+1:03d}" + fake.numerify("############"),
                NamaLengkap=f"Admin {i+1} ({'Full' if is_full else 'Null'})",
                Email=f"admin{i+1}@test.com",
                Role=RoleEnum.admin,
                Password=PASSWORD_HASH,
                isVerified=True,
                # Optional Fields Logic:
                NoTelepon=fake.phone_number() if is_full else None,
                DinasID=None # Admin biasanya global
            )
            session.add(admin)
            users_created.append(admin)

        # -- B. 3 KADIS (1 per Dinas) --
        for i in range(3):
            is_full = (i % 2 == 0)
            kadis = User(
                NIP=f"KDS{i+1:03d}" + fake.numerify("############"),
                NamaLengkap=f"Kadis {i+1} ({'Full' if is_full else 'Null'})",
                Email=f"kadis{i+1}@test.com",
                Role=RoleEnum.kepala_dinas,
                Password=PASSWORD_HASH,
                isVerified=True,
                # Optional Fields Logic:
                NoTelepon=fake.phone_number() if is_full else None,
                DinasID=dinas_list[i].ID # Assign ke Dinas A, B, C berurutan
            )
            session.add(kadis)
            users_created.append(kadis)

        # -- C. 6 PIC (2 per Dinas) --
        for i in range(6):
            is_full = (i % 2 == 0)
            dinas_idx = i // 2 # 0,0, 1,1, 2,2 -> Dinas A, A, B, B, C, C
            
            pic = User(
                NIP=f"PIC{i+1:03d}" + fake.numerify("############"),
                NamaLengkap=f"PIC {i+1} Dinas {dinas_idx+1} ({'Full' if is_full else 'Null'})",
                Email=f"pic{i+1}@test.com",
                Role=RoleEnum.pic,
                Password=PASSWORD_HASH,
                isVerified=True,
                # Optional Fields Logic:
                NoTelepon=fake.phone_number() if is_full else None,
                DinasID=dinas_list[dinas_idx].ID
            )
            session.add(pic)
            users_created.append(pic)
        
        session.flush()

        # Buat Wallet untuk semua user
        for u in users_created:
            w = Wallet(UserID=u.ID, WalletTypeID=w_type.ID, Saldo=5000000)
            session.add(w)

        # Pisahkan list untuk referensi nanti
        list_pic = [u for u in users_created if u.Role == RoleEnum.pic]
        list_kadis = [u for u in users_created if u.Role == RoleEnum.kepala_dinas]

        # ==========================================
        # 3. VEHICLES (20 Total)
        # ==========================================
        logger.info("🚗 Seeding 20 Vehicles (50% Full Specs, 50% Minimal Specs)...")
        
        vehicles = []
        for i in range(20):
            is_full = (i % 2 == 0)
            
            veh = Vehicle(
                Nama=f"Kendaraan {i+1} ({'Lengkap' if is_full else 'Min'})",
                Plat=f"B {fake.random_int(1000,9999)} {fake.random_uppercase_letter()}{fake.random_uppercase_letter()}",
                VehicleTypeID=v_type_mobil.ID,
                Status=VehicleStatusEnum.Active if is_full else VehicleStatusEnum.Active, # Status wajib active/nonactive enum
                
                # --- OPTIONAL FIELDS (Null vs Full) ---
                KapasitasMesin = 1500 if is_full else None,
                JenisBensin    = "Pertamax" if is_full else None,
                Merek          = "Toyota" if is_full else None,
                FotoFisik      = "https://placehold.co/600x400/png" if is_full else None,
                AssetIconName  = "AppAssets.ilustCar1" if is_full else None,
                AssetIconColor = "AppColors.primary70" if is_full else None,
                TipeTransmisi  = "Matic" if is_full else None,
                TotalFuelBar   = 8 if is_full else 8, # Default DB biasanya not null default 8
                CurrentFuelBar = 4 if is_full else 0,
                DinasID        = dinas_list[i % 3].ID if is_full else None, # Separuh tidak punya dinas
                Odometer       = 10000 if is_full else 0
            )
            session.add(veh)
            vehicles.append(veh)
        
        session.flush()

        # Assign vehicles to random PICs (hanya untuk data yang Full)
        for i, veh in enumerate(vehicles):
            if i % 2 == 0: # Full vehicle assigned to random PIC
                owner = random.choice(list_pic)
                if veh not in owner.vehicles:
                    owner.vehicles.append(veh)

        # ==========================================
        # 4. SUBMISSIONS (20 Total)
        # ==========================================
        logger.info("📝 Seeding 20 Submissions (50% Detailed, 50% Simple)...")
        
        submission_refs = []

        for i in range(20):
            is_full = (i % 2 == 0)
            
            creator = list_pic[i % len(list_pic)] # Rotate PIC
            receiver = list_kadis[0] # Default receiver
            
            sub = Submission(
                KodeUnik=f"SUB-{fake.unique.random_number(digits=8)}",
                CreatorID=creator.ID,
                ReceiverID=receiver.ID,
                TotalCashAdvance=100000 * (i+1),
                Status=SubmissionStatusEnum.Accepted if is_full else SubmissionStatusEnum.Pending,
                created_at=datetime.now(),
                
                # --- OPTIONAL FIELDS ---
                Description=f"Pengajuan perjalanan dinas lengkap ke-{i+1} dengan detail panjang." if is_full else None,
                Date=datetime.now() if is_full else datetime.now(), # Date biasanya not null di UI logic, kita isi saja
                DinasID=creator.DinasID if is_full else None # Kadang submission lintas dinas / error data
            )
            session.add(sub)
            session.flush()
            submission_refs.append(sub)

            # Log
            session.add(SubmissionLog(
                SubmissionID=sub.ID,
                Status=sub.Status,
                UpdatedByUserID=creator.ID,
                Notes="Auto generated log full." if is_full else None # Notes Optional
            ))

        # ==========================================
        # 5. REPORTS (20 Total)
        # ==========================================
        logger.info("⛽ Seeding 20 Reports (50% Bukti Lengkap, 50% Bukti Kosong)...")

        for i in range(20):
            is_full = (i % 2 == 0)
            
            # Ambil submission yang sesuai (atau random)
            related_sub = submission_refs[i]
            user = list_pic[i % len(list_pic)]
            veh = vehicles[i % len(vehicles)]

            rep = Report(
                KodeUnik=related_sub.KodeUnik,
                UserID=user.ID,
                VehicleID=veh.ID,
                AmountRupiah=50000,
                AmountLiter=5.0,
                Status=ReportStatusEnum.Accepted if is_full else ReportStatusEnum.Pending,
                Timestamp=datetime.now(),
                
                # --- OPTIONAL FIELDS (UI Testing Critical) ---
                Description = f"Isi bensin full tank di SPBU 34.1234. Bukti lengkap foto fisik dan struk." if is_full else None,
                Latitude    = -6.2088 if is_full else None,
                Longitude   = 106.8456 if is_full else None,
                Odometer    = 15000 if is_full else None,
                DinasID     = user.DinasID if is_full else None,
                
                # Photos (String URL)
                VehiclePhysicalPhotoPath = "https://placehold.co/400x300?text=Fisik" if is_full else None,
                OdometerPhotoPath        = "https://placehold.co/400x300?text=Odometer" if is_full else None,
                InvoicePhotoPath         = "https://placehold.co/400x300?text=Struk" if is_full else None,
                MyPertaminaPhotoPath     = "https://placehold.co/400x300?text=App" if is_full else None
            )
            session.add(rep)
            session.flush()
            
            # Log
            session.add(ReportLog(
                ReportID=rep.ID,
                Status=rep.Status,
                UpdatedByUserID=user.ID,
                Notes="Bukti valid dan lengkap." if is_full else None
            ))

        session.commit()
        logger.info("✅ SEEDING SELESAI! Data siap untuk testing Flutter.")
        logger.info("   - User Index Genap (0,2..): Data Lengkap (Ada NoTelp, dll)")
        logger.info("   - User Index Ganjil (1,3..): Data Minimal (Null NoTelp)")
        logger.info("   - Vehicle/Report Genap: Ada Foto, Deskripsi, GPS")
        logger.info("   - Vehicle/Report Ganjil: Foto Null, Deskripsi Null, GPS Null")

if __name__ == "__main__":
    seed_heavy_v2()