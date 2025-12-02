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
    User, RoleEnum, Dinas, WalletType, VehicleType, Wallet, 
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
        logger.info("🌱 Memulai proses seeding database (V2 - Full Data - PEP8)...")

        # ==========================================
        # 1. REFERENCE DATA (Dinas, Types)
        # ==========================================
        logger.info("... 1. Seeding Data Referensi")
        
        # Dinas
        dinas_names = [
            "Dinas Komunikasi dan Informatika", 
            "Dinas Pekerjaan Umum", 
            "Dinas Perhubungan", 
            "Dinas Kesehatan"
        ]
        dinas_objs = []
        for d_nama in dinas_names:
            dinas = session.execute(select(Dinas).where(Dinas.nama == d_nama)).scalar_one_or_none()
            if not dinas:
                dinas = Dinas(nama=d_nama)
                session.add(dinas)
                session.flush()
            dinas_objs.append(dinas)
        
        # Wallet Types
        w_types = ["Linkaja", "OVO", "Gopay"]
        wallet_types = []
        for w_name in w_types:
            wt = session.execute(select(WalletType).where(WalletType.nama == w_name)).scalar_one_or_none()
            if not wt:
                wt = WalletType(nama=w_name)
                session.add(wt)
                session.flush()
            wallet_types.append(wt)

        # Vehicle Types
        v_types = ["Motor", "Mobil", "Lainnya"]
        vehicle_types = []
        for v_name in v_types:
            vt = session.execute(select(VehicleType).where(VehicleType.nama == v_name)).scalar_one_or_none()
            if not vt:
                vt = VehicleType(nama=v_name)
                session.add(vt)
                session.flush()
            vehicle_types.append(vt)

        # ==========================================
        # 2. USERS & WALLETS (6 Users Total)
        # ==========================================
        logger.info("... 2. Seeding 6 Users & Wallets")
        
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
            user = session.execute(select(User).where(User.nip == nip)).scalar_one_or_none()
            if not user:
                user = User(
                    nip=nip,
                    nama_lengkap=name,
                    email=f"{name.split()[0].lower()}@sibeda.local",
                    role=role,
                    password=DEFAULT_PASSWORD_HASH,
                    no_telepon=fake.phone_number(),
                    is_verified=True,
                    dinas_id=dinas_objs[d_idx].id
                )
                session.add(user)
                session.flush()
                
                wallet = Wallet(
                    user_id=user.id,
                    wallet_type_id=random.choice(wallet_types).id,
                    saldo=random.choice([10000000, 25000000, 50000000])
                )
                session.add(wallet)
            users.append(user)

        pic_users = [u for u in users if u.role == RoleEnum.pic]
        kadis_users = [u for u in users if u.role == RoleEnum.kepala_dinas]
        admin_user = [u for u in users if u.role == RoleEnum.admin][0]

        # ==========================================
        # 3. VEHICLES (30 Unit)
        # ==========================================
        logger.info("... 3. Seeding 30 Vehicles")
        
        vehicles = []
        icons = [
            ("AppAssets.ilustCar1", "AppColors.primary70"), 
            ("AppAssets.ilustCar2", "AppColors.primary50"), 
            ("AppAssets.ilustMotorcycle1", "AppColors.secondary70"), 
            ("AppAssets.ilustOthers1", "AppColors.tertiary30")
        ]

        for _ in range(30):
            plat = f"DK {fake.random_int(1000, 9999)} {fake.random_uppercase_letter()}{fake.random_uppercase_letter()}"
            
            if session.execute(select(Vehicle).where(Vehicle.plat == plat)).scalar_one_or_none():
                continue

            icon_data = random.choice(icons)
            vt = random.choice(vehicle_types)
            owner_dinas = random.choice(dinas_objs)

            transmisi = "Manual"
            if "Motor" in vt.nama:
                transmisi = random.choice(["Matic", "Manual"])
            elif "Mobil" in vt.nama:
                transmisi = random.choice(["Matic", "Manual"])
            
            veh = Vehicle(
                nama=f"{vt.nama} - {fake.word().capitalize()}",
                plat=plat,
                kapasitas_mesin=random.choice([110, 125, 150, 1500, 2000, 2500]),
                vehicle_type_id=vt.id,
                odometer=random.randint(1000, 150000),
                status=random.choice([VehicleStatusEnum.active, VehicleStatusEnum.active, VehicleStatusEnum.nonactive]),
                jenis_bensin=random.choice(["Pertalite", "Pertamax", "Solar", "Dexlite"]),
                merek=random.choice(["Toyota", "Honda", "Suzuki", "Mitsubishi", "Isuzu", "Yamaha"]),
                foto_fisik=f"https://source.unsplash.com/random/400x300/?vehicle&sig={random.randint(1,1000)}",
                asset_icon_name=icon_data[0],
                asset_icon_color=icon_data[1],
                tipe_transmisi=transmisi,
                total_fuel_bar=8,
                current_fuel_bar=random.randint(1, 8),
                dinas_id=owner_dinas.id 
            )
            session.add(veh)
            vehicles.append(veh)
        session.flush()

        # ==========================================
        # 4. ASSIGN VEHICLES TO USERS
        # ==========================================
        logger.info("... 4. Assigning Vehicles to PICs")
        
        for veh in vehicles:
            potential_owners = [u for u in pic_users if u.dinas_id == veh.dinas_id]
            if not potential_owners:
                potential_owners = pic_users
            
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
            creator = random.choice(pic_users)
            potential_receivers = [k for k in kadis_users if k.dinas_id == creator.dinas_id]
            if potential_receivers:
                receiver = potential_receivers[0]
            else:
                receiver = admin_user if random.random() > 0.5 else random.choice(kadis_users)

            final_status = random.choices(
                [SubmissionStatusEnum.pending, SubmissionStatusEnum.accepted, SubmissionStatusEnum.rejected],
                weights=[15, 75, 10],
                k=1
            )[0]

            created_at = fake.date_time_between(start_date='-3m', end_date='now', tzinfo=timezone.utc)
            date_input = created_at

            sub = Submission(
                kode_unik=f"SUB-{created_at.strftime('%Y%m')}-{fake.unique.random_number(digits=5)}",
                creator_id=creator.id,
                receiver_id=receiver.id,
                total_cash_advance=random.choice([100000, 150000, 200000, 250000, 300000, 500000]),
                status=final_status,
                created_at=created_at,
                description=fake.sentence(nb_words=8, variable_nb_words=True),
                date=date_input,
                dinas_id=creator.dinas_id
            )
            session.add(sub)
            session.flush()

            # Log Creation
            session.add(SubmissionLog(
                submission_id=sub.id,
                status=SubmissionStatusEnum.pending,
                timestamp=created_at,
                updated_by_user_id=creator.id,
                notes="Pengajuan anggaran BBM operasional"
            ))

            if final_status != SubmissionStatusEnum.pending:
                decision_time = created_at + timedelta(hours=random.randint(2, 48))
                notes = "Disetujui" if final_status == SubmissionStatusEnum.accepted else "Ditolak"
                
                session.add(SubmissionLog(
                    submission_id=sub.id,
                    status=final_status,
                    timestamp=decision_time,
                    updated_by_user_id=receiver.id,
                    notes=notes
                ))
                
                if final_status == SubmissionStatusEnum.accepted:
                    submissions.append((sub, decision_time))

        # ==========================================
        # 6. REPORTS
        # ==========================================
        logger.info("... 6. Seeding Reports")

        for sub, approved_date in submissions:
            if random.random() < 0.9:
                report_date = approved_date + timedelta(days=random.randint(0, 3))
                user_report = session.get(User, sub.creator_id)
                
                if user_report.vehicles:
                    selected_vehicle = random.choice(user_report.vehicles)
                else:
                    dinas_vehicles = [v for v in vehicles if v.dinas_id == user_report.dinas_id]
                    if dinas_vehicles:
                        selected_vehicle = random.choice(dinas_vehicles)
                    else:
                        selected_vehicle = random.choice(vehicles)

                report_status = random.choices(
                    [ReportStatusEnum.pending, ReportStatusEnum.accepted, ReportStatusEnum.rejected],
                    weights=[20, 70, 10], k=1
                )[0]

                report = Report(
                    kode_unik=sub.kode_unik,
                    user_id=sub.creator_id,
                    vehicle_id=selected_vehicle.id,
                    amount_rupiah=sub.total_cash_advance,
                    amount_liter=float(sub.total_cash_advance) / 10000,
                    description=f"Pengisian BBM di SPBU {fake.city()}",
                    status=report_status,
                    timestamp=report_date,
                    latitude=float(fake.latitude()),
                    longitude=float(fake.longitude()),
                    vehicle_physical_photo_path=f"https://source.unsplash.com/random/300x300/?car&sig={sub.id}",
                    odometer_photo_path=f"https://source.unsplash.com/random/300x300/?dashboard&sig={sub.id}",
                    invoice_photo_path=f"https://source.unsplash.com/random/300x300/?receipt&sig={sub.id}",
                    my_pertamina_photo_path=f"https://source.unsplash.com/random/300x300/?app&sig={sub.id}",
                    odometer=selected_vehicle.odometer + random.randint(50, 500),
                    dinas_id=sub.dinas_id
                )
                session.add(report)
                session.flush()

                session.add(ReportLog(
                    report_id=report.id,
                    status=ReportStatusEnum.pending,
                    timestamp=report_date,
                    updated_by_user_id=sub.creator_id,
                    notes="Laporan realisasi diupload"
                ))

                if report_status != ReportStatusEnum.pending:
                    review_date = report_date + timedelta(hours=random.randint(1, 24))
                    reviewer_id = sub.receiver_id
                    notes = "Bukti valid." if report_status == ReportStatusEnum.accepted else "Perbaiki foto."
                    
                    session.add(ReportLog(
                        report_id=report.id,
                        status=report_status,
                        timestamp=review_date,
                        updated_by_user_id=reviewer_id,
                        notes=notes
                    ))

        session.commit()
        logger.info("✅ SEEDING SELESAI!")

if __name__ == "__main__":
    seed_database()