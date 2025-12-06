# SIBEDA API

**Sistem Informasi Bensin Daerah** - Backend API menggunakan FastAPI untuk manajemen pengajuan dan pelaporan penggunaan BBM kendaraan dinas.

## 🚀 Tech Stack

- **Framework**: FastAPI
- **Database**: MySQL (PyMySQL + SQLAlchemy ORM)
- **Authentication**: JWT (python-jose)
- **Password Hashing**: Passlib + Bcrypt
- **Validation**: Pydantic v2
- **Testing**: Pytest + Faker

## 📋 Fitur Utama

- ✅ Autentikasi JWT (Login, Register, Forgot Password, OTP)
- ✅ Manajemen User dengan Role (Admin, Kepala Dinas, PIC)
- ✅ Manajemen Kendaraan Dinas
- ✅ Pengajuan Dana BBM (Submission)
- ✅ Pelaporan Penggunaan BBM (Report) dengan Upload Foto
- ✅ Wallet/Saldo User
- ✅ Statistik Dashboard
- ✅ QR Code Assignment

## 📁 Struktur Project

```
sibeda-python/
├── main.py                 # Entry point aplikasi
├── config.py               # Konfigurasi environment
├── middleware.py           # Request logging & language middleware
├── requirements.txt        # Dependencies
├── .env                    # Environment variables
├── assets/                 # Upload files (foto kendaraan, report)
│   ├── reports/
│   └── vehicles/
├── controller/
│   └── auth.py             # JWT & authentication logic
├── database/
│   └── database.py         # Database connection
├── model/
│   └── models.py           # SQLAlchemy models
├── routers/
│   ├── auth.py             # Auth endpoints
│   ├── users.py            # User management
│   ├── vehicle.py          # Vehicle CRUD
│   ├── vehicle_type.py     # Vehicle type CRUD
│   ├── submission.py       # Submission CRUD
│   ├── report.py           # Report CRUD with photo upload
│   ├── wallet.py           # Wallet management
│   ├── dinas.py            # Dinas CRUD
│   ├── stat.py             # Statistics
│   ├── qr.py               # QR code assignment
│   └── seeder.py           # Database seeder
├── schemas/
│   └── schemas.py          # Pydantic schemas
├── services/
│   ├── user_service.py
│   ├── vehicle_service.py
│   ├── submission_service.py
│   ├── report_service.py
│   ├── wallet_service.py
│   ├── dinas_service.py
│   └── stat_service.py
├── utils/
│   ├── file_upload.py      # File upload helper
│   ├── mailer.py           # Email sender
│   ├── otp.py              # OTP generator
│   └── responses.py        # Response helpers
├── i18n/
│   └── messages.py         # Internationalization
└── tests/
    ├── conftest.py
    ├── test_user_auth.py
    └── test_vehicle.py
```

## ⚙️ Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/zeroeints/sibeda-python.git
cd sibeda-python
```

### 2. Buat Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment

Buat file `.env` di root project:

```env
APP_NAME=SIBEDA API
DEBUG=true
ENVIRONMENT=development

DATABASE_URL=mysql+pymysql://root:@localhost:3306/sibeda_db

SECRET_KEY=your-super-secret-key-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=60

LOG_LEVEL=INFO

# SMTP (Optional - untuk forgot password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=true
MAIL_FROM=noreply@sibeda.com
MAIL_FROM_NAME=SIBEDA
```

### 5. Buat Database

```sql
CREATE DATABASE sibeda_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. Jalankan Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server akan berjalan di `http://localhost:8000`

## 📚 API Documentation

Setelah server berjalan, akses:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Autentikasi

### Login

```bash
# OAuth2 Password Flow (untuk Swagger)
POST /token
Content-Type: application/x-www-form-urlencoded
username=<NIP>&password=<PASSWORD>

# JSON Login (untuk Frontend)
POST /login
Content-Type: application/x-www-form-urlencoded
username=<NIP>&password=<PASSWORD>
```

### Menggunakan Token

```bash
curl http://localhost:8000/users/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## 📡 API Endpoints

### Auth

| Method | Endpoint                | Deskripsi                |
| ------ | ----------------------- | ------------------------ |
| POST   | `/token`                | Login (OAuth2)           |
| POST   | `/login`                | Login (wrapped response) |
| POST   | `/auth/register`        | Register user baru       |
| GET    | `/auth/verify`          | Verifikasi token         |
| POST   | `/auth/forgot-password` | Request reset password   |
| POST   | `/auth/verify-otp`      | Verifikasi OTP           |
| POST   | `/auth/reset-password`  | Reset password           |
| PUT    | `/auth/change-password` | Ganti password           |

### Users

| Method | Endpoint                 | Deskripsi                  |
| ------ | ------------------------ | -------------------------- |
| GET    | `/users/`                | List semua user            |
| GET    | `/users/{id}`            | Detail user                |
| POST   | `/users/`                | Create user                |
| PUT    | `/users/{id}`            | Update user                |
| DELETE | `/users/{id}`            | Delete user                |
| GET    | `/users/balance/{id}`    | Get user balance           |
| GET    | `/users/detailed/search` | Search users dengan detail |

### Vehicles

| Method | Endpoint                    | Deskripsi                     |
| ------ | --------------------------- | ----------------------------- |
| GET    | `/vehicle/`                 | List kendaraan                |
| POST   | `/vehicle/`                 | Create kendaraan (with photo) |
| PUT    | `/vehicle/{id}`             | Update kendaraan (with photo) |
| PATCH  | `/vehicle/{id}`             | Partial update (with photo)   |
| DELETE | `/vehicle/{id}`             | Delete kendaraan              |
| GET    | `/vehicle/my/vehicles`      | Kendaraan user                |
| GET    | `/vehicle/my/vehicles/{id}` | Detail kendaraan user         |
| GET    | `/vehicle/dinas/{id}`       | Kendaraan per dinas           |
| POST   | `/vehicle/{id}/assign`      | Assign user ke kendaraan      |
| POST   | `/vehicle/{id}/unassign`    | Unassign user                 |

### Submissions

| Method | Endpoint                      | Deskripsi         |
| ------ | ----------------------------- | ----------------- |
| GET    | `/submission/`                | List pengajuan    |
| POST   | `/submission/`                | Create pengajuan  |
| GET    | `/submission/{id}`            | Detail pengajuan  |
| PUT    | `/submission/{id}`            | Update pengajuan  |
| DELETE | `/submission/{id}`            | Delete pengajuan  |
| GET    | `/submission/my/submissions`  | Pengajuan user    |
| GET    | `/submission/monthly/summary` | Ringkasan bulanan |
| GET    | `/submission/monthly/details` | Detail bulanan    |

### Reports

| Method | Endpoint              | Deskripsi                    |
| ------ | --------------------- | ---------------------------- |
| GET    | `/report/`            | List laporan                 |
| POST   | `/report/`            | Create laporan (with photos) |
| PATCH  | `/report/{id}`        | Update laporan (with photos) |
| DELETE | `/report/{id}`        | Delete laporan               |
| GET    | `/report/my/reports`  | Laporan user                 |
| PUT    | `/report/{id}/status` | Update status laporan        |
| GET    | `/report/{id}/logs`   | Log perubahan status         |

### Others

| Method | Endpoint         | Deskripsi              |
| ------ | ---------------- | ---------------------- |
| GET    | `/dinas/`        | List dinas             |
| GET    | `/vehicle-type/` | List tipe kendaraan    |
| GET    | `/wallet/`       | List wallet            |
| GET    | `/stat/pic`      | Statistik PIC          |
| GET    | `/stat/kadis`    | Statistik Kepala Dinas |
| GET    | `/stat/admin`    | Statistik Admin        |

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_user_auth.py

# Run with verbose
pytest -v
```

## 🔧 Database Seeding

```bash
# Via endpoint (development only)
POST /seeder/seed

# Via script
python db_seeder.py
```

## 📝 Lisensi

MIT License

## 👥 Kontributor

- Tim Pengembang SIBEDA
