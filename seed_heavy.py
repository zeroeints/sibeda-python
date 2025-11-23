import random
from faker import Faker
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# --- IMPORT MODEL (Sesuaikan dengan path project Anda) ---
# Pastikan file ini berada di root folder project atau sesuaikan importnya
from config import get_settings # Pastikan module ini ada
from model.models import (
    Base, User, RoleEnum, Dinas, WalletType, VehicleType, Wallet, 
    Vehicle, VehicleStatusEnum, Submission, SubmissionStatusEnum, 
    PurposeEnum, SubmissionLog, Report
)

# --- KONFIGURASI DATABASE ---
# Menggunakan settings dari file config atau hardcode jika perlu
try:
    settings = get_settings()
    DATABASE_URL = settings.database_url
except:
    # Fallback jika config tidak ditemukan (GANTI INI JIKA PERLU)
    DATABASE_URL = "mysql+pymysql://root:@localhost/db_sibeda"

engine = create_engine(DATABASE_URL)
fake = Faker('id_ID')

# Hash password dummy
DUMMY_PASSWORD_HASH = "$bcrypt-sha256$v=2,t=2b,r=12$DUMMYHASHFORPASSWORD123......................"

def get_or_create_user(session, user_id, role, name, email, dinas_id, wallet_type_ids):
    """Helper untuk memastikan User 1, 3, 4 ada"""
    user = session.get(User, user_id)
    if not user:
        print(f"   Creating User ID {user_id} ({role.value})...")
        user = User(
            ID=user_id,
            NIP=fake.unique.numerify(text='##################'),
            Role=role,
            NamaLengkap=name,
            Email=email,
            NoTelepon=fake.phone_number(),
            Password=DUMMY_PASSWORD_HASH,
            isVerified=True,
            DinasID=dinas_id
        )
        session.add(user)
        session.flush() # Flush untuk memastikan ID terpakai

        # Buat Wallet
        wallet = Wallet(
            Saldo=random.choice([1000000, 5000000, 10000000]),
            UserID=user.ID,
            WalletTypeID=random.choice(wallet_type_ids)
        )
        session.add(wallet)
    return user

def seed_heavy_data():
    with Session(engine) as session:
        print("🚀 Memulai Massive Seeding...")

        # 1. Pastikan Reference Data Ada
        print("... Cek Reference Data")
        
        # Dinas
        dinas = session.get(Dinas, 1)
        if not dinas:
            dinas = Dinas(ID=1, Nama="Dinas Komunikasi dan Informatika")
            session.add(dinas)
            session.flush()
        
        dinas_pu = session.execute(select(Dinas).where(Dinas.Nama == "Dinas Pekerjaan Umum")).scalar()
        if not dinas_pu:
            dinas_pu = Dinas(Nama="Dinas Pekerjaan Umum")
            session.add(dinas_pu)
            session.flush()

        dinas_ids = [dinas.ID, dinas_pu.ID]

        # Wallet & Vehicle Types
        w_types = ["Cash", "E-Wallet", "Bank Transfer"]
        for w in w_types:
            if not session.execute(select(WalletType).where(WalletType.Nama == w)).scalar():
                session.add(WalletType(Nama=w))
        
        v_types = ["Motor", "Mobil", "Truk"]
        for v in v_types:
            if not session.execute(select(VehicleType).where(VehicleType.Nama == v)).scalar():
                session.add(VehicleType(Nama=v))
        
        session.commit()

        wt_ids = [w.ID for w in session.scalars(select(WalletType)).all()]
        vt_ids = [v.ID for v in session.scalars(select(VehicleType)).all()]

        # 2. Setup Core Users (ID 1, 3, 4)
        print("... Setup Core Users (PIC:1, Kadis:3, Admin:4)")
        
        pic_user = get_or_create_user(session, 1, RoleEnum.pic, "Budi PIC", "pic@sibeda.com", dinas.ID, wt_ids)
        kadis_user = get_or_create_user(session, 3, RoleEnum.kepala_dinas, "Pak Kadis", "kadis@sibeda.com", dinas.ID, wt_ids)
        admin_user = get_or_create_user(session, 4, RoleEnum.admin, "Admin Sistem", "admin@sibeda.com", dinas.ID, wt_ids)
        
        session.commit()

        # 3. Generate Vehicles (Lebih Banyak)
        print("... Generating 30 Vehicles")
        existing_plats = [v.Plat for v in session.scalars(select(Vehicle)).all()]
        vehicles = []
        
        for _ in range(30):
            plat = f"DK {fake.random_int(1000, 9999)} {fake.random_uppercase_letter()}{fake.random_uppercase_letter()}"
            if plat in existing_plats: continue

            veh = Vehicle(
                Nama=f"{random.choice(['Toyota', 'Honda', 'Mitsubishi', 'Isuzu'])} {fake.first_name()}",
                Plat=plat,
                KapasitasMesin=random.choice([110, 150, 1500, 2000, 2500]),
                VehicleTypeID=random.choice(vt_ids),
                Odometer=random.randint(5000, 200000),
                Status=random.choice([VehicleStatusEnum.Active, VehicleStatusEnum.Active, VehicleStatusEnum.Nonactive]), # Lebih banyak active
                JenisBensin=random.choice(["Pertalite", "Pertamax", "Solar"]),
                Merek=random.choice(["Toyota", "Honda", "Yamaha", "Suzuki"]),
                FotoFisik=f"https://source.unsplash.com/random/300x200/?car,motorcycle&sig={random.randint(1,1000)}"
            )
            session.add(veh)
            vehicles.append(veh)
        
        session.commit()
        # Reload vehicles with IDs
        all_vehicles = session.scalars(select(Vehicle)).all()

        # 4. Generate Transactions (Submissions & Reports)
        print("... Generating 100+ Submissions and Reports")
        
        # Skenario 1: Admin (4) Memberi Dana ke PIC (1)
        # Skenario 2: PIC (1) Mengajukan ke Kadis (3) - (Opsional, tapi kita fokus ke Admin->PIC sesuai prompt)
        
        for _ in range(100):
            # Tentukan tanggal transaksi (menyebar 3 bulan terakhir)
            created_at = fake.date_time_between(start_date='-90d', end_date='now')
            
            # 70% Transaksi dari Admin ke PIC, 30% PIC ke Kadis
            if random.random() > 0.3:
                creator = admin_user
                receiver = pic_user
            else:
                creator = pic_user
                receiver = kadis_user

            selected_vehicle = random.choice(all_vehicles)
            status = random.choices(
                [SubmissionStatusEnum.Accepted, SubmissionStatusEnum.Rejected, SubmissionStatusEnum.Pending],
                weights=[60, 20, 20], # 60% Accepted
                k=1
            )[0]

            total_cash = random.choice([100000, 150000, 200000, 300000, 500000])
            kode_unik = fake.unique.bothify(text='SUB-####-????').upper()

            # Create Submission
            submission = Submission(
                KodeUnik=kode_unik,
                Status=status,
                CreatorID=creator.ID,
                ReceiverID=receiver.ID,
                TotalCashAdvance=total_cash,
                VehicleID=selected_vehicle.ID,
                created_at=created_at
            )
            session.add(submission)
            session.flush()

            # Create Log (Initial)
            session.add(SubmissionLog(
                SubmissionID=submission.ID,
                Status=SubmissionStatusEnum.Pending,
                Timestamp=created_at
            ))

            # Create Log (Final Decision)
            if status != SubmissionStatusEnum.Pending:
                decision_time = created_at + timedelta(hours=random.randint(1, 48))
                session.add(SubmissionLog(
                    SubmissionID=submission.ID,
                    Status=status,
                    Timestamp=decision_time
                ))

                # 5. Generate Report (Hanya jika Submission Accepted & Creator/Receiver melibatkan PIC)
                # Skenario: Jika Admin memberi dana ke PIC (Accepted), maka PIC membuat laporan penggunaan.
                if status == SubmissionStatusEnum.Accepted and receiver.ID == 1:
                    # 90% PIC membuat laporan jika sudah disetujui
                    if random.random() > 0.1:
                        report_time = decision_time + timedelta(days=random.randint(1, 5))
                        
                        # Hitung pemakaian bensin (Logis sedikit)
                        harga_per_liter = 10000
                        liter = total_cash / harga_per_liter
                        
                        # Tambah odometer
                        new_odometer = selected_vehicle.Odometer + int(liter * 10) # Asumsi 1:10 km/l
                        
                        # Update kendaraan odometer (hanya simulasi di data report, tidak update master vehicle agar variatif)
                        
                        report = Report(
                            KodeUnik=submission.KodeUnik,
                            UserID=pic_user.ID, # PIC yang melaporkan
                            VehicleID=selected_vehicle.ID,
                            AmountRupiah=total_cash,
                            AmountLiter=liter,
                            Description=fake.sentence(nb_words=10),
                            Timestamp=report_time,
                            Latitude=fake.latitude(),
                            Longitude=fake.longitude(),
                            VehiclePhysicalPhotoPath="https://placehold.co/600x400?text=Fisik+Kendaraan",
                            OdometerPhotoPath="https://placehold.co/600x400?text=Odometer",
                            InvoicePhotoPath="https://placehold.co/600x400?text=Struk+SPBU",
                            MyPertaminaPhotoPath="https://placehold.co/600x400?text=App+MyPertamina",
                            Odometer=new_odometer
                        )
                        session.add(report)

        session.commit()
        print("✅ Selesai! 100 Data Transaksi + User + Kendaraan telah dibuat.")

if __name__ == "__main__":
    seed_heavy_data()