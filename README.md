# sibeda-python

# SIBEDA API Backend (FastAPI)

## Autentikasi

Ada dua endpoint otentikasi:

1. `POST /token` (standar OAuth2 Password)

   - Body: `application/x-www-form-urlencoded`
     - `username=<NIP>`
     - `password=<Password>`
   - Response:
     ```json
     { "access_token": "<jwt>", "token_type": "bearer" }
     ```
   - Digunakan Swagger untuk otomatis menyuntik header `Authorization`.

2. `POST /login` (wrapped response)
   - Body sama seperti `/token`
   - Response dibungkus:
     ```json
     {
     	"success": true,
     	"data": { "access_token": "<jwt>", "token_type": "bearer" },
     	"message": null
     }
     ```
   - Cocok untuk frontend yang ingin format konsisten.

Untuk Swagger, gunakan tombol Authorize dan masukkan kredensial; sistem akan memanggil `/token` dan menyimpan header Authorization.

## Endpoint Profil Cepat (Opsional)

Tambahkan sendiri `/auth/me` bila ingin (belum dibuat) untuk menampilkan user dari token.

## Verifikasi Token

`GET /auth/verify`  
Parameter opsional: `check_user=true` untuk memastikan user masih ada di DB.

Contoh: `GET /auth/verify?check_user=true`

Response struktur dijelaskan di bawah.

## Contoh Curl

```bash
# Mendapatkan token standar
curl -X POST http://127.0.0.1:8000/token -H "Content-Type: application/x-www-form-urlencoded" -d "username=123&password=secretpass"

# Menggunakan token
curl http://127.0.0.1:8000/users/ -H "Authorization: Bearer <TOKEN>"

# Verifikasi token
curl http://127.0.0.1:8000/auth/verify?check_user=true -H "Authorization: Bearer <TOKEN>"
```

## Endpoint Verifikasi Token

Untuk membantu debugging error `401 Tidak bisa validasi token`, ditambahkan endpoint:

`GET /auth/verify`

Header yang dibutuhkan:

```
Authorization: Bearer <access_token>
```

### Contoh Response (valid)

```json
{
	"success": true,
	"data": {
		"valid": true,
		"claims": {
			"sub": "123",
			"ID": 3,
			"NIP": "123",
			"Role": "admin",
			"NamaLengkap": "Admin User",
			"Email": "admin@example.com",
			"NoTelepon": "0800",
			"DinasID": 1,
			"exp": 1759686828
		},
		"reason": null
	},
	"message": null
}
```

### Contoh Response (invalid)

```json
{
	"success": true,
	"data": {
		"valid": false,
		"claims": null,
		"reason": "Signature has expired"
	},
	"message": null
}
```

Field `reason` menjelaskan kenapa token tidak valid (expired, salah signature, format salah, dsb).

## Penyebab Umum 401

1. Header tidak benar: harus `Authorization: Bearer <token>`
2. `SECRET_KEY` berubah setelah login → token lama invalid
3. User terkait token sudah dihapus / NIP berubah
4. Token expired (`exp` sudah lewat)
5. Token terpotong saat copy-paste (kurang bagian signature / titik)

## Langkah Debug Singkat

1. Panggil `/auth/verify` dengan token → lihat `valid` & `reason`
2. Jika valid: cek user masih ada di DB sesuai `sub`
3. Jika `reason` expired → login ulang
4. Jika signature invalid → pastikan server pakai SECRET_KEY yang sama dengan saat generate

## Catatan

Endpoint `/auth/verify` sebaiknya hanya diaktifkan di environment development. Bila perlu, lindungi dengan role atau hapus sebelum production.

---

## Endpoint Submission Monthly Report

Untuk mendapatkan laporan pengajuan penggunaan dana per bulan, tersedia 3 endpoint baru:

### 1. GET `/submission/monthly/summary`

Mendapatkan ringkasan statistik pengajuan per bulan (total, status, dana)

### 2. GET `/submission/monthly/details`

Mendapatkan detail lengkap setiap pengajuan per bulan dengan informasi creator, receiver, dan vehicle

### 3. GET `/submission/monthly/report`

Mendapatkan laporan lengkap (ringkasan + detail) dalam satu request

**Dokumentasi lengkap:** Lihat file [docs/SUBMISSION_MONTHLY_API.md](docs/SUBMISSION_MONTHLY_API.md)

**Testing guide:** Lihat file [docs/TESTING_SUBMISSION_MONTHLY.md](docs/TESTING_SUBMISSION_MONTHLY.md)

**Query Parameters:**

- `month`: Integer 1-12 (bulan yang ingin ditampilkan)
- `year`: Integer 2000-2100 (tahun yang ingin ditampilkan)

**Authentication:** Bearer token required untuk semua endpoint

**Contoh:**

```bash
GET /submission/monthly/report?month=11&year=2025
Authorization: Bearer <token>
```

---

## Endpoint Get All Submissions

Untuk mendapatkan semua pengajuan dengan berbagai opsi filtering dan pagination:

### 1. GET `/submission/`

Mendapatkan semua submission dengan data basic (ID, KodeUnik, Status, dll)

### 2. GET `/submission/all/detailed`

Mendapatkan semua submission dengan **detail lengkap** (nama creator, receiver, vehicle) dan **pagination info**

**Dokumentasi lengkap:** Lihat file [docs/GET_ALL_SUBMISSIONS_API.md](docs/GET_ALL_SUBMISSIONS_API.md)

**Query Parameters:**

- `creator_id`: Filter berdasarkan ID pembuat (optional)
- `receiver_id`: Filter berdasarkan ID penerima (optional)
- `vehicle_id`: Filter berdasarkan ID kendaraan (optional)
- `status`: Filter berdasarkan status - Pending, Accepted, Rejected (optional)
- `limit`: Batasi jumlah data (default 100 untuk detailed, max 1000)
- `offset`: Skip sejumlah data untuk pagination (default 0)

**Contoh:**

```bash
# Get all dengan detail lengkap
GET /submission/all/detailed?limit=50&offset=0

# Filter by status
GET /submission/all/detailed?status=Pending

# Multiple filters
GET /submission/all/detailed?creator_id=10&status=Pending&limit=20
```

---

## Endpoint Get Users with Details

Untuk mendapatkan pengguna dengan detail lengkap termasuk wallet, dinas, dan submission statistics:

### GET `/users/detailed/search`

Mendapatkan semua pengguna dengan **detail lengkap** termasuk:

- ✅ Data user lengkap (NIP, Nama, Email, Role, dll)
- ✅ **Wallet info** (ID, Saldo, Type)
- ✅ **Dinas info** (ID, Nama)
- ✅ Total submission yang dibuat dan diterima
- ✅ **Fitur pencarian** (search by NIP, Nama, Email)
- ✅ **Multiple filters** (role, dinas, verification status)
- ✅ **Pagination** dengan info lengkap

**Dokumentasi lengkap:** Lihat file [docs/USER_DETAILED_SEARCH_API.md](docs/USER_DETAILED_SEARCH_API.md)

**Query Parameters:**

- `search`: Cari berdasarkan NIP, Nama, atau Email (optional, case-insensitive)
- `role`: Filter berdasarkan role - admin, kepala_dinas, pic (optional)
- `dinas_id`: Filter berdasarkan ID dinas (optional)
- `is_verified`: Filter berdasarkan status verifikasi - true/false (optional)
- `limit`: Batasi jumlah data (default 100, max 1000)
- `offset`: Skip sejumlah data untuk pagination (default 0)

**Contoh:**

```bash
# Search by name
GET /users/detailed/search?search=John

# Filter by role
GET /users/detailed/search?role=pic

# Filter by dinas
GET /users/detailed/search?dinas_id=5

# Multiple filters
GET /users/detailed/search?role=pic&is_verified=true&dinas_id=5
```

**Response includes:**

- User data (NIP, Nama, Email, Role, Status Verifikasi)
- Wallet balance & type
- Dinas name
- Submission statistics (created & received)
- Pagination info (total, has_more, dll)

---

## Endpoint Get User Balance

Untuk mendapatkan saldo wallet user beserta informasi lengkap:

### GET `/users/balance/{user_id}`

Mendapatkan saldo wallet user dengan **detail lengkap** termasuk:

- ✅ User info (NIP, Nama, Email, Role)
- ✅ **Saldo wallet** (jumlah dana tersedia)
- ✅ **Wallet type** (jenis wallet: Bensin, Non-Bensin, dll)
- ✅ **Dinas info** (ID dan Nama dinas)

**Dokumentasi lengkap:** Lihat file [docs/USER_BALANCE_API.md](docs/USER_BALANCE_API.md)

**Path Parameters:**

- `user_id`: ID user yang ingin dicek saldonya (required)

**Authentication:** Bearer token required

**Contoh:**

```bash
# Get balance untuk user ID 1
GET /users/balance/1
Authorization: Bearer <token>

# Get balance untuk user ID 5
GET /users/balance/5
Authorization: Bearer <token>
```

**Response example:**

```json
{
	"success": true,
	"data": {
		"user_id": 1,
		"nip": "123456789012345678",
		"nama_lengkap": "John Doe",
		"email": "john.doe@example.com",
		"role": "pic",
		"dinas_id": 5,
		"dinas_nama": "Dinas Kesehatan",
		"wallet_id": 10,
		"saldo": 5000000.0,
		"wallet_type_id": 1,
		"wallet_type_nama": "Bensin"
	},
	"message": "Berhasil mendapatkan saldo user"
}
```

**Use Cases:**

- Cek saldo sebelum membuat submission baru
- Monitoring saldo user untuk admin/kepala dinas
- Verifikasi dana tersedia untuk pengajuan
- Self-check balance untuk user

---

## Endpoint Get My Vehicles

Untuk mendapatkan kendaraan yang pernah digunakan user beserta detail penggunaan dan riwayat pengisian bensin:

### 1. GET `/vehicle/my/vehicles`

Mendapatkan semua kendaraan yang pernah digunakan oleh user dengan **statistik lengkap**:

- ✅ Data kendaraan lengkap (Nama, Plat, Merek, Odometer, dll)
- ✅ **Tipe kendaraan** (Mobil Dinas, Motor Dinas, dll)
- ✅ **Total submission** menggunakan kendaraan ini
- ✅ **Total report** pengisian bensin
- ✅ **Total bensin** (liter) yang sudah diisi
- ✅ **Total biaya** bensin (Rupiah)
- ✅ **Info pengisian terakhir** (tanggal, liter, rupiah, odometer)

### 2. GET `/vehicle/my/vehicles/{vehicle_id}`

Mendapatkan **detail lengkap** kendaraan termasuk:

- ✅ Semua info kendaraan dan statistik
- ✅ **Riwayat 10 pengisian bensin terakhir**
  - Tanggal & waktu
  - Jumlah liter & rupiah
  - Odometer saat pengisian
  - Lokasi (latitude, longitude)
  - Deskripsi

**Dokumentasi lengkap:** Lihat file [docs/MY_VEHICLES_API.md](docs/MY_VEHICLES_API.md)

**Authentication:** Bearer token required

**Contoh:**

```bash
# Get all my vehicles
GET /vehicle/my/vehicles
Authorization: Bearer <token>

# Get detail specific vehicle with refuel history
GET /vehicle/my/vehicles/1
Authorization: Bearer <token>
```

**Response example (list):**

```json
{
	"success": true,
	"data": [
		{
			"ID": 1,
			"Nama": "Toyota Avanza 2020",
			"Plat": "B 1234 ABC",
			"Merek": "Toyota",
			"VehicleTypeName": "Mobil Dinas",
			"TotalFuelLiters": 450.5,
			"TotalRupiahSpent": 4500000.0,
			"LastRefuelDate": "2025-11-03T14:30:00+07:00",
			"LastRefuelLiters": 25.5,
			"TotalSubmissions": 15,
			"TotalReports": 23
		}
	],
	"message": "Ditemukan 1 kendaraan"
}
```

**Use Cases:**

- Dashboard kendaraan yang pernah digunakan
- Monitoring konsumsi BBM per kendaraan
- Tracking pengisian bensin terakhir
- Analisis efisiensi kendaraan (liter/km)
- Validasi sebelum membuat submission baru

---

## Endpoint Get My Reports

Untuk mendapatkan laporan (report) pengisian bensin user beserta detail lengkap:

### 1. GET `/report/my/reports`

Mendapatkan semua report/pelaporan pengisian bensin yang dibuat oleh user dengan **detail lengkap**:

- ✅ Info report (KodeUnik, Jumlah Liter, Rupiah, Waktu, Lokasi)
- ✅ **Info kendaraan** (Nama, Plat, Tipe)
- ✅ **Info submission terkait** (Status, Total Cash Advance)
- ✅ **Foto bukti** (Kendaraan, Odometer, Invoice, MyPertamina)
- ✅ **Filter by vehicle** (opsional)
- ✅ **Pagination** dengan info lengkap

### 2. GET `/report/my/reports/{report_id}`

Mendapatkan **detail lengkap** sebuah report termasuk:

- ✅ Info user pelapor (Nama, NIP)
- ✅ Info kendaraan lengkap (Nama, Plat, Merek, Kapasitas, Jenis Bensin, dll)
- ✅ Detail pengisian (Liter, Rupiah, Odometer, Lokasi GPS)
- ✅ Semua foto bukti (4 jenis foto)
- ✅ Info submission terkait lengkap (Status, Total, Creator, Receiver)

**Dokumentasi lengkap:** Lihat file [docs/MY_REPORTS_API.md](docs/MY_REPORTS_API.md)

**Query Parameters (list):**

- `vehicle_id`: Filter berdasarkan ID kendaraan (optional)
- `limit`: Batasi jumlah data (default 100, max 1000)
- `offset`: Skip sejumlah data untuk pagination (default 0)

**Authentication:** Bearer token required

**Contoh:**

```bash
# Get all my reports
GET /report/my/reports?limit=50&offset=0
Authorization: Bearer <token>

# Filter by vehicle
GET /report/my/reports?vehicle_id=1
Authorization: Bearer <token>

# Get detail specific report
GET /report/my/reports/101
Authorization: Bearer <token>
```

**Response example (list):**

```json
{
	"success": true,
	"data": [
		{
			"ID": 101,
			"KodeUnik": "SUB-2025-001",
			"VehicleName": "Toyota Avanza 2020",
			"VehiclePlat": "B 1234 ABC",
			"VehicleType": "Mobil Dinas",
			"AmountRupiah": 250000.0,
			"AmountLiter": 25.5,
			"Timestamp": "2025-11-03T14:30:00+07:00",
			"Odometer": 45000,
			"SubmissionStatus": "Accepted",
			"SubmissionTotal": 500000.0
		}
	],
	"message": "Ditemukan 1 dari 23 report",
	"pagination": {
		"total": 23,
		"limit": 50,
		"offset": 0,
		"returned": 1,
		"has_more": true
	}
}
```

**Use Cases:**

- Dashboard laporan pengisian bensin user
- Tracking pengeluaran BBM per kendaraan
- Verifikasi laporan dengan foto bukti
- Analisis pola pengisian (waktu & lokasi)
- Rekonsiliasi dengan submission/pengajuan dana

```

```

```

```
