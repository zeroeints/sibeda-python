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

````