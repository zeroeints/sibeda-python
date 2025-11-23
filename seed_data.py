import random
from faker import Faker
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# --- IMPORT MODEL ANDA DI SINI ---
# Asumsi file model anda bernama models.py. 
# Sesuaikan path import ini dengan struktur folder project Anda.
from config import get_settings
from model.models import (
    Base, User, RoleEnum, Dinas, WalletType, VehicleType, Wallet, 
    Vehicle, VehicleStatusEnum, Submission, SubmissionStatusEnum, 
    PurposeEnum, SubmissionLog, Report
)

# --- KONFIGURASI DATABASE ---
# Ganti URL ini sesuai database Anda (MySQL/PostgreSQL/dll)
# Contoh: "mysql+pymysql://user:pass@localhost/db_sibeda"
settings = get_settings()
engine = create_engine(settings.database_url)
fake = Faker('id_ID') # Menggunakan locale Indonesia

# Hash password dummy (misalnya: "password123")
# Format ini meniru bcrypt yang ada di data anda.
# Jika sistem login anda strict, pastikan hash ini valid.
DUMMY_PASSWORD_HASH = "$bcrypt-sha256$v=2,t=2b,r=12$DUMMYHASHFORPASSWORD123......................" 

def seed_data():
    with Session(engine) as session:
        print("🌱 Memulai proses seeding...")

        # 1. Setup Data Referensi (Jika belum ada)
        print("... Seeding Reference Data (WalletType, VehicleType, Dinas)")
        
        # Wallet Types
        w_types = ["Cash", "E-Wallet (Gopay/OVO)", "Transfer Bank"]
        for w_name in w_types:
            if not session.execute(select(WalletType).where(WalletType.Nama == w_name)).scalar():
                session.add(WalletType(Nama=w_name))
        
        # Vehicle Types
        v_types = ["Motor Operasional", "Mobil Dinas", "Truk/Angkutan"]
        for v_name in v_types:
            if not session.execute(select(VehicleType).where(VehicleType.Nama == v_name)).scalar():
                session.add(VehicleType(Nama=v_name))

        # Dinas (Pastikan ID 1 ada seperti di data user)
        dinas_kominfo = session.get(Dinas, 1)
        if not dinas_kominfo:
            dinas_kominfo = Dinas(ID=1, Nama="Dinas Komunikasi dan Informatika")
            session.add(dinas_kominfo)
        
        # Tambah dinas dummy lain
        if not session.execute(select(Dinas).where(Dinas.Nama == "Dinas Pekerjaan Umum")).scalar():
            session.add(Dinas(Nama="Dinas Pekerjaan Umum"))
        
        session.commit()

        # Ambil referensi ID untuk foreign keys
        wt_ids = [w.ID for w in session.scalars(select(WalletType)).all()]
        vt_ids = [v.ID for v in session.scalars(select(VehicleType)).all()]
        dinas_ids = [d.ID for d in session.scalars(select(Dinas)).all()]

        # 2. Seeding Users (PIC & Kadis)
        print("... Seeding Users & Wallets")
        
        existing_nips = [u.NIP for u in session.scalars(select(User)).all()]
        new_users = []
        
        # Buat 15 User baru (Campuran Role)
        roles = [RoleEnum.pic] * 10 + [RoleEnum.kepala_dinas] * 3 + [RoleEnum.admin] * 2
        
        for role in roles:
            nip = fake.unique.numerify(text='##################') # 18 digit NIP
            while nip in existing_nips:
                nip = fake.unique.numerify(text='##################')
            
            user = User(
                NIP=nip,
                Role=role,
                NamaLengkap=fake.name(),
                Email=fake.unique.email(),
                NoTelepon=fake.phone_number(),
                Password=DUMMY_PASSWORD_HASH, # Semua user baru passwordnya sama
                isVerified=True,
                DinasID=random.choice(dinas_ids)
            )
            session.add(user)
            session.flush() # Flush untuk dapat User.ID

            # Buat Wallet untuk user tersebut (Wajib karena relasi)
            wallet = Wallet(
                Saldo=random.choice([0, 50000, 100000, 250000, 500000]),
                UserID=user.ID,
                WalletTypeID=random.choice(wt_ids)
            )
            session.add(wallet)
            new_users.append(user)

        session.commit()

        # 3. Seeding Vehicles
        print("... Seeding Vehicles")
        vehicles = []
        existing_plats = [v.Plat for v in session.scalars(select(Vehicle)).all()]
        
        for _ in range(10):
            plat = f"DK {fake.random_int(1000, 9999)} {fake.random_uppercase_letter()}{fake.random_uppercase_letter()}"
            if plat in existing_plats: continue

            veh = Vehicle(
                Nama=f"{random.choice(['Toyota', 'Honda', 'Mitsubishi', 'Suzuki'])} {fake.first_name()}", # Misal: Toyota Budi (Nama Aset)
                Plat=plat,
                KapasitasMesin=random.choice([1500, 2000, 2500, 150]),
                VehicleTypeID=random.choice(vt_ids),
                Odometer=random.randint(10000, 100000),
                Status=VehicleStatusEnum.Active,
                JenisBensin=random.choice(["Pertalite", "Pertamax", "Solar"]),
                Merek=random.choice(["Toyota", "Honda", "Mitsubishi"]),
                FotoFisik="https://via.placeholder.com/300.png/09f/fff" # Dummy image
            )
            session.add(veh)
            vehicles.append(veh)
        
        session.commit()

        # Refresh lists
        all_pics = session.scalars(select(User).where(User.Role == RoleEnum.pic)).all()
        all_kadis = session.scalars(select(User).where(User.Role == RoleEnum.kepala_dinas)).all()
        all_vehicles = session.scalars(select(Vehicle)).all()

        if not all_pics or not all_kadis or not all_vehicles:
            print("Warning: Tidak cukup data untuk membuat submission.")
            return

        # 4. Seeding Submissions (Transactions)
        print("... Seeding Submissions & Logs")
        
        for _ in range(20): # Buat 20 Transaksi
            creator = random.choice(all_pics)
            receiver = random.choice(all_kadis) # Kadis yang menerima
            vehicle = random.choice(all_vehicles)
            
            status = random.choice(list(SubmissionStatusEnum))
            created_at = fake.date_time_between(start_date='-30d', end_date='now')
            
            # Unique Code
            kode_unik = fake.unique.bothify(text='SUB-####-????')

            submission = Submission(
                KodeUnik=kode_unik,
                Status=status,
                CreatorID=creator.ID,
                ReceiverID=receiver.ID,
                TotalCashAdvance=random.choice([100000, 200000, 300000]),
                VehicleID=vehicle.ID,
                created_at=created_at
            )
            session.add(submission)
            session.flush()

            # Log: Created
            session.add(SubmissionLog(
                SubmissionID=submission.ID,
                Status=SubmissionStatusEnum.Pending,
                Timestamp=created_at
            ))

            # Log: Final Status (If not pending)
            if status != SubmissionStatusEnum.Pending:
                session.add(SubmissionLog(
                    SubmissionID=submission.ID,
                    Status=status,
                    Timestamp=created_at + timedelta(hours=random.randint(1, 24))
                ))

            # 5. Seeding Report (Only for Accepted Submissions)
            if status == SubmissionStatusEnum.Accepted:
                # 80% chance user actually reported
                if random.random() > 0.2:
                    report = Report(
                        KodeUnik=submission.KodeUnik,
                        UserID=creator.ID,
                        VehicleID=vehicle.ID,
                        AmountRupiah=submission.TotalCashAdvance,
                        AmountLiter=submission.TotalCashAdvance / 10000, # Asumsi 10rb/liter
                        Description=fake.sentence(),
                        Timestamp=created_at + timedelta(days=1),
                        Latitude=fake.latitude(),
                        Longitude=fake.longitude(),
                        VehiclePhysicalPhotoPath="dummy/path/fisik.jpg",
                        OdometerPhotoPath="dummy/path/odo.jpg",
                        InvoicePhotoPath="dummy/path/struk.jpg",
                        Odometer=vehicle.Odometer + random.randint(10, 100)
                    )
                    session.add(report)

        session.commit()
        print("✅ Selesai! Database telah diisi dengan data dummy.")

if __name__ == "__main__":
    seed_data()