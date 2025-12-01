import random
from faker import Faker
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from datetime import datetime, timedelta, timezone
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

# Password Default: "password123"
DEFAULT_PASSWORD_HASH = "$bcrypt-sha256$v=2,t=2b,r=12$aNMkUf1Xp0HMCDmku3XgM.$TR1hRdt9SZ66CdlnepazFEQcM.tkb4a" 

def seed_database():
    with Session(engine) as session:
        logger.info("🌱 Memulai proses seeding database (V2 - Full Data)...")

        # ==========================================
        # 1. REFERENCE DATA (Dinas, Types)
        # ==========================================
        logger.info("... 1. Seeding Data Referensi")
        
        # Dinas (Pastikan ada 4 seperti request sebelumnya, tapi user akan kita sebar)
        dinas_names = [
            "Dinas Komunikasi dan Informatika", 
            "Dinas Pekerjaan Umum", 
            "Dinas Perhubungan", 
            "Dinas Kesehatan"
        ]
        dinas_objs = []
        for d_nama in dinas_names:
            dinas = session.execute(select(Dinas).where(Dinas.Nama == d_nama)).scalar_one_or_none()
            if not dinas:
                dinas = Dinas(Nama=d_nama)
                session.add(dinas)
                session.flush()
            dinas_objs.append(dinas)
        
        # Wallet Types
        w_types = ["Linkaja", "OVO", "Gopay", "Cash", "Bank Transfer"]
        wallet_types = []
        for w_name in w_types:
            wt = session.execute(select(WalletType).where(WalletType.Nama == w_name)).scalar_one_or_none()
            if not wt:
                wt = WalletType(Nama=w_name)
                session.add(wt)
                session.flush()
            wallet_types.append(wt)

        # Vehicle Types
        v_types = ["Motor Dinas", "Mobil Dinas", "Truk Operasional", "Ambulans"]
        vehicle_types = []
        for v_name in v_types:
            vt = session.execute(select(VehicleType).where(VehicleType.Nama == v_name)).scalar_one_or_none()
            if not vt:
                vt = VehicleType(Nama=v_name)
                session.add(vt)
                session.flush()
            vehicle_types.append(vt)

        # ==========================================
        # 2. USERS & WALLETS (6 Users Total)
        # ==========================================
        logger.info("... 2. Seeding 6 Users & Wallets")
        
        # Skema Distribusi:
        # User 1: Admin (Di Dinas 0)
        # User 2: Kadis A (Di Dinas 0)
        # User 3: Kadis B (Di Dinas 1)
        # User 4: PIC A (Di Dinas 0) -> Bawahan Kadis A
        # User 5: PIC B (Di Dinas 1) -> Bawahan Kadis B
        # User 6: PIC C (Di Dinas 2) -> Dinas tanpa Kadis di sistem ini (akan submit ke Admin/Kadis A)
        
        users_config = [
            # NIP, Nama, Role, Index Dinas
            ("100000000000000001", "Admin Sistem", RoleEnum.admin, 0),
            ("100000000000000002", "Budi Santoso (Kadis Kominfo)", RoleEnum.kepala_dinas, 0),
            ("100000000000000003", "Siti Aminah (Kadis PU)", RoleEnum.kepala_dinas, 1),
            ("100000000000000004", "Andi Lapangan (PIC Kominfo)", RoleEnum.pic, 0),
            ("100000000000000005", "Rudi Staff (PIC PU)", RoleEnum.pic, 1),
            ("100000000000000006", "Dewi Dishub (PIC Dishub)", RoleEnum.pic, 2),
        ]

        users = []
        for nip, name, role, d_idx in users_config:
            user = session.execute(select(User).where(User.NIP == nip)).scalar_one_or_none()
            if not user:
                user = User(
                    NIP=nip,
                    NamaLengkap=name,
                    Email=f"{name.split()[0].lower()}@sibeda.local",
                    Role=role,
                    Password=DEFAULT_PASSWORD_HASH,
                    NoTelepon=fake.phone_number(),
                    isVerified=True,
                    DinasID=dinas_objs[d_idx].ID
                )
                session.add(user)
                session.flush()
                
                # Create Wallet for everyone
                wallet = Wallet(
                    UserID=user.ID,
                    WalletTypeID=random.choice(wallet_types).ID,
                    Saldo=random.choice([10000000, 25000000, 50000000])
                )
                session.add(wallet)
            users.append(user)

        # Pisahkan list user untuk logic nanti
        pic_users = [u for u in users if u.Role == RoleEnum.pic]
        kadis_users = [u for u in users if u.Role == RoleEnum.kepala_dinas]
        admin_user = [u for u in users if u.Role == RoleEnum.admin][0]

        # ==========================================
        # 3. VEHICLES (30 Unit)
        # ==========================================
        logger.info("... 3. Seeding 30 Vehicles (Full Specs)")
        
        vehicles = []
        icons = [
            ("AppAssets.ilustCar1", "AppColors.primary70"), 
            ("AppAssets.ilustCar2", "AppColors.primary50"), 
            ("AppAssets.ilustMotorcycle1", "AppColors.secondary70"), 
            ("AppAssets.ilustOthers1", "AppColors.tertiary30")
        ]

        for _ in range(30):
            plat = f"DK {fake.random_int(1000, 9999)} {fake.random_uppercase_letter()}{fake.random_uppercase_letter()}"
            
            # Skip jika plat sudah ada
            if session.execute(select(Vehicle).where(Vehicle.Plat == plat)).scalar_one_or_none():
                continue

            icon_data = random.choice(icons)
            vt = random.choice(vehicle_types)
            
            # Tentukan Dinas kepemilikan kendaraan secara random dari dinas yg ada
            owner_dinas = random.choice(dinas_objs)

            # Logic Tipe Transmisi berdasarkan tipe kendaraan
            transmisi = "Manual"
            if "Motor" in vt.Nama:
                transmisi = random.choice(["Matic", "Manual"])
            elif "Mobil" in vt.Nama:
                transmisi = random.choice(["Matic", "Manual"])
            
            veh = Vehicle(
                Nama=f"{vt.Nama} - {fake.word().capitalize()}",
                Plat=plat,
                KapasitasMesin=random.choice([110, 125, 150, 1500, 2000, 2500]),
                VehicleTypeID=vt.ID,
                Odometer=random.randint(1000, 150000),
                Status=random.choice([VehicleStatusEnum.Active, VehicleStatusEnum.Active, VehicleStatusEnum.Nonactive]),
                JenisBensin=random.choice(["Pertalite", "Pertamax", "Solar", "Dexlite"]),
                Merek=random.choice(["Toyota", "Honda", "Suzuki", "Mitsubishi", "Isuzu", "Yamaha"]),
                FotoFisik=f"https://source.unsplash.com/random/400x300/?vehicle&sig={random.randint(1,1000)}",
                AssetIconName=icon_data[0],
                AssetIconColor=icon_data[1],
                # New Fields
                TipeTransmisi=transmisi,
                TotalFuelBar=8, # Default standar
                CurrentFuelBar=random.randint(1, 8),
                DinasID=owner_dinas.ID 
            )
            session.add(veh)
            vehicles.append(veh)
        session.flush()

        # ==========================================
        # 4. ASSIGN VEHICLES TO USERS
        # ==========================================
        logger.info("... 4. Assigning Vehicles to PICs")
        
        # Assign kendaraan ke PIC yang satu Dinas (jika memungkinkan)
        for veh in vehicles:
            # Cari PIC di dinas yang sama dengan kendaraan
            potential_owners = [u for u in pic_users if u.DinasID == veh.DinasID]
            
            # Jika tidak ada PIC di dinas tersebut, ambil random PIC lain (peminjaman lintas dinas)
            if not potential_owners:
                potential_owners = pic_users
            
            # Assign ke 1 atau 2 orang
            if potential_owners:
                owners = random.sample(potential_owners, k=1) 
                for owner in owners:
                    if veh not in owner.vehicles:
                        owner.vehicles.append(veh)
        
        session.flush()

        # ==========================================
        # 5. SUBMISSIONS (100 Transaksi)
        # ==========================================
        logger.info("... 5. Seeding 100 Submissions")
        
        submissions = []

        for _ in range(100):
            # 1. Pilih Creator (PIC)
            creator = random.choice(pic_users)
            
            # 2. Pilih Receiver (Kadis di Dinas yang sama, atau Admin)
            potential_receivers = [k for k in kadis_users if k.DinasID == creator.DinasID]
            if potential_receivers:
                receiver = potential_receivers[0]
            else:
                # Jika PIC tidak punya Kadis (misal Dinas 2), kirim ke Admin atau Kadis lain
                receiver = admin_user if random.random() > 0.5 else random.choice(kadis_users)

            # 3. Status logic
            final_status = random.choices(
                [SubmissionStatusEnum.Pending, SubmissionStatusEnum.Accepted, SubmissionStatusEnum.Rejected],
                weights=[15, 75, 10], # Mayoritas diterima agar banyak report
                k=1
            )[0]

            # 4. Waktu
            created_at = fake.date_time_between(start_date='-3m', end_date='now', tzinfo=timezone.utc)
            date_input = created_at # Tanggal kegiatan sama dengan created_at

            sub = Submission(
                KodeUnik=f"SUB-{created_at.strftime('%Y%m')}-{fake.unique.random_number(digits=5)}",
                CreatorID=creator.ID,
                ReceiverID=receiver.ID,
                TotalCashAdvance=random.choice([100000, 150000, 200000, 250000, 300000, 500000]),
                Status=final_status,
                created_at=created_at,
                # New Fields
                Description=fake.sentence(nb_words=8, variable_nb_words=True),
                Date=date_input,
                DinasID=creator.DinasID # Penting: DinasID dari Creator
            )
            session.add(sub)
            session.flush()

            # Log Creation
            session.add(SubmissionLog(
                SubmissionID=sub.ID,
                Status=SubmissionStatusEnum.Pending,
                Timestamp=created_at,
                UpdatedByUserID=creator.ID,
                Notes="Pengajuan anggaran BBM operasional"
            ))

            # Log Decision
            if final_status != SubmissionStatusEnum.Pending:
                decision_time = created_at + timedelta(hours=random.randint(2, 48))
                notes = "Disetujui, silakan gunakan dengan bijak" if final_status == SubmissionStatusEnum.Accepted else "Ditolak, anggaran tidak mencukupi"
                
                session.add(SubmissionLog(
                    SubmissionID=sub.ID,
                    Status=final_status,
                    Timestamp=decision_time,
                    UpdatedByUserID=receiver.ID,
                    Notes=notes
                ))
                
                if final_status == SubmissionStatusEnum.Accepted:
                    submissions.append((sub, decision_time))

        # ==========================================
        # 6. REPORTS (Dari Accepted Submissions)
        # ==========================================
        logger.info("... 6. Seeding Reports")

        for sub, approved_date in submissions:
            # 90% submission yang diapprove akan dilaporkan
            if random.random() < 0.9:
                report_date = approved_date + timedelta(days=random.randint(0, 3))
                
                # Cari user pembuat report (creator submission)
                user_report = session.get(User, sub.CreatorID)
                
                # Pilih kendaraan: Prioritas kendaraan yg dipegang user, kalau gak ada ambil random yg satu dinas
                if user_report.vehicles:
                    selected_vehicle = random.choice(user_report.vehicles)
                else:
                    # Fallback ke kendaraan di dinas yang sama
                    dinas_vehicles = [v for v in vehicles if v.DinasID == user_report.DinasID]
                    if dinas_vehicles:
                        selected_vehicle = random.choice(dinas_vehicles)
                    else:
                        selected_vehicle = random.choice(vehicles) # Fallback terakhir

                # Status Report
                report_status = random.choices(
                    [ReportStatusEnum.Pending, ReportStatusEnum.Accepted, ReportStatusEnum.Rejected],
                    weights=[20, 70, 10], k=1
                )[0]

                report = Report(
                    KodeUnik=sub.KodeUnik,
                    UserID=sub.CreatorID,
                    VehicleID=selected_vehicle.ID,
                    AmountRupiah=sub.TotalCashAdvance, # Asumsi habis pas
                    AmountLiter=float(sub.TotalCashAdvance) / 10000, # Asumsi harga 10rb
                    Description=f"Pengisian BBM di SPBU {fake.city()}",
                    Status=report_status,
                    Timestamp=report_date,
                    Latitude=float(fake.latitude()),
                    Longitude=float(fake.longitude()),
                    VehiclePhysicalPhotoPath=f"https://source.unsplash.com/random/300x300/?car&sig={sub.ID}",
                    OdometerPhotoPath=f"https://source.unsplash.com/random/300x300/?dashboard&sig={sub.ID}",
                    InvoicePhotoPath=f"https://source.unsplash.com/random/300x300/?receipt&sig={sub.ID}",
                    MyPertaminaPhotoPath=f"https://source.unsplash.com/random/300x300/?app&sig={sub.ID}",
                    Odometer=selected_vehicle.Odometer + random.randint(50, 500), # Odometer nambah dikit
                    DinasID=sub.DinasID # Penting: DinasID dari Submission/User
                )
                session.add(report)
                session.flush()

                # Log Report Created
                session.add(ReportLog(
                    ReportID=report.ID,
                    Status=ReportStatusEnum.Pending,
                    Timestamp=report_date,
                    UpdatedByUserID=sub.CreatorID,
                    Notes="Laporan realisasi diupload"
                ))

                # Log Report Decision
                if report_status != ReportStatusEnum.Pending:
                    review_date = report_date + timedelta(hours=random.randint(1, 24))
                    # Reviewer adalah Receiver dari submission awal (Kadis/Admin)
                    reviewer_id = sub.ReceiverID
                    
                    notes = "Bukti lengkap dan valid." if report_status == ReportStatusEnum.Accepted else "Foto struk buram, tolong perbaiki."
                    
                    session.add(ReportLog(
                        ReportID=report.ID,
                        Status=report_status,
                        Timestamp=review_date,
                        UpdatedByUserID=reviewer_id,
                        Notes=notes
                    ))

        session.commit()
        logger.info("✅ SEEDING SELESAI! Database siap digunakan dengan data lengkap.")

if __name__ == "__main__":
    seed_database()