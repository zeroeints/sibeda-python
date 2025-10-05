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
