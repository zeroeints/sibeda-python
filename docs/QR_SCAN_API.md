# QR Scan Endpoint Documentation

## Endpoint

**POST** `/qr/scan` atau `/en/qr/scan` atau `/id/qr/scan`

## Deskripsi

Endpoint untuk memindai QR code dan mengembalikan data user pemilik QR code tersebut.

**Fitur:**

- Support **signed token** (format: `base64.signature`)
- Support **raw code** (format: `0613`, `ABC123`, dll)
- **Read-only** operation (kode tidak dihapus setelah scan)
- Bisa dipindai berkali-kali

## Request

### Body (JSON)

```json
{
	"kode_unik": "eyJ1aWQiOjkyLCJjb2RlIjoiMDYxMyIsInRzIjoxNzYwNjA2NjI5fQ.EW7wegHxTYUf37hacmvjmWPYJRN8Xnu3BXseh7hW-lk"
}
```

Atau dengan raw code:

```json
{
	"kode_unik": "0613"
}
```

## Response

### Success (200 OK)

```json
{
	"success": true,
	"data": {
		"ID": 92,
		"NIP": "123456789987654321",
		"NamaLengkap": "John Doe",
		"Email": "john@example.com",
		"NoTelepon": "08123456789",
		"Role": "pic",
		"isVerified": true
	},
	"message": "QR code is ready"
}
```

### Error Responses

#### 404 Not Found - Kode Tidak Ditemukan

```json
{
	"success": false,
	"code": 404,
	"message": "Data not found",
	"request_id": "..."
}
```

#### 400 Bad Request - Token Tidak Valid

```json
{
	"detail": "Token QR tidak valid: signature"
}
```

## Cara Menggunakan

### 1. Dengan cURL (Windows PowerShell)

```powershell
# Dengan signed token
$body = @{kode_unik='eyJ1aWQiOjkyLCJjb2RlIjoiMDYxMyIsInRzIjoxNzYwNjA2NjI5fQ.EW7wegHxTYUf37hacmvjmWPYJRN8Xnu3BXseh7hW-lk'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/en/qr/scan' -Method Post -Body $body -ContentType 'application/json'

# Dengan raw code
$body = @{kode_unik='0613'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/en/qr/scan' -Method Post -Body $body -ContentType 'application/json'
```

### 2. Dengan Python

```python
import requests

# Dengan signed token
response = requests.post(
    'http://127.0.0.1:8000/en/qr/scan',
    json={'kode_unik': 'eyJ1aWQiOjkyLCJjb2RlIjoiMDYxMyIsInRzIjoxNzYwNjA2NjI5fQ.EW7wegHxTYUf37hacmvjmWPYJRN8Xnu3BXseh7hW-lk'}
)
print(response.json())

# Dengan raw code
response = requests.post(
    'http://127.0.0.1:8000/en/qr/scan',
    json={'kode_unik': '0613'}
)
print(response.json())
```

### 3. Dengan JavaScript/Fetch

```javascript
// Dengan signed token
fetch("http://127.0.0.1:8000/en/qr/scan", {
	method: "POST",
	headers: { "Content-Type": "application/json" },
	body: JSON.stringify({
		kode_unik:
			"eyJ1aWQiOjkyLCJjb2RlIjoiMDYxMyIsInRzIjoxNzYwNjA2NjI5fQ.EW7wegHxTYUf37hacmvjmWPYJRN8Xnu3BXseh7hW-lk"
	})
})
	.then((r) => r.json())
	.then((data) => console.log(data));

// Dengan raw code
fetch("http://127.0.0.1:8000/en/qr/scan", {
	method: "POST",
	headers: { "Content-Type": "application/json" },
	body: JSON.stringify({ kode_unik: "0613" })
})
	.then((r) => r.json())
	.then((data) => console.log(data));
```

## Flow Diagram

```
Input QR Code (signed token atau raw)
         ↓
extract_kode_unik_from_qr() di utils/otp.py
         ↓
Cek format: ada "." ? → Decode token : Return raw
         ↓
Query UniqueCodeGenerator WHERE KodeUnik = code
         ↓
Ambil User berdasarkan UserID
         ↓
Return UserResponse
         ↓
Kode TIDAK dihapus (read-only)
```

## Token Format

### Signed Token

Format: `base64url(payload).base64url(signature)`

Payload (JSON):

```json
{
	"uid": 92, // User ID
	"code": "0613", // Kode unik asli
	"ts": 1760606629 // Timestamp
}
```

Signature: HMAC-SHA256 dengan secret key

### Keuntungan Signed Token

1. ✅ Tidak bisa dimanipulasi (HMAC signature)
2. ✅ Bisa include metadata (user ID, timestamp)
3. ✅ Lebih aman untuk transport
4. ✅ Backward compatible dengan raw code

## Database Structure

### Table: UniqueCodeGenerator

| Column     | Type     | Description                 |
| ---------- | -------- | --------------------------- |
| ID         | Integer  | Primary key                 |
| UserID     | Integer  | FK ke User.ID               |
| KodeUnik   | String   | Kode unik                   |
| expired_at | DateTime | Waktu expired               |
| Purpose    | Enum     | Tujuan (otp, register, dll) |

### Relationship

`UniqueCodeGenerator.UserID` → `User.ID`

## Testing

### Test Case 1: Scan dengan Signed Token ✅

```powershell
$body = @{kode_unik='eyJ1aWQiOjkyLCJjb2RlIjoiMDYxMyIsInRzIjoxNzYwNjA2NjI5fQ.EW7wegHxTYUf37hacmvjmWPYJRN8Xnu3BXseh7hW-lk'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/en/qr/scan' -Method Post -Body $body -ContentType 'application/json'
```

Expected: 200 OK dengan data user

### Test Case 2: Scan dengan Raw Code ✅

```powershell
$body = @{kode_unik='0613'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/en/qr/scan' -Method Post -Body $body -ContentType 'application/json'
```

Expected: 200 OK dengan data user

### Test Case 3: Kode Tidak Ada ❌

```powershell
$body = @{kode_unik='TIDAK_ADA'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/en/qr/scan' -Method Post -Body $body -ContentType 'application/json'
```

Expected: 404 Not Found

### Test Case 4: Multiple Scans ✅

Scan kode yang sama berkali-kali → Semua harus berhasil (kode tidak dihapus)

## Troubleshooting

### Error: "Token QR tidak valid: signature"

- Token signature tidak cocok
- Token mungkin dimanipulasi atau corrupt
- Coba gunakan raw code sebagai gantinya

### Error: "Data not found"

- Kode unik tidak ada di database
- Cek `UniqueCodeGenerator` table: `SELECT * FROM UniqueCodeGenerator WHERE KodeUnik = '0613'`

### Error: "User not found"

- User dengan UserID tersebut tidak ada
- Cek relasi: `SELECT * FROM User WHERE ID = (SELECT UserID FROM UniqueCodeGenerator WHERE KodeUnik = '0613')`

## Security Notes

1. **No Authentication Required**: Endpoint ini public (tidak perlu login)
2. **Read-Only**: Kode tidak dihapus, aman untuk scan berkali-kali
3. **Token Verification**: Signed token diverifikasi dengan HMAC-SHA256
4. **Rate Limiting**: Pertimbangkan tambahkan rate limit untuk prevent abuse

## Implementation Files

| File                 | Purpose                                                   |
| -------------------- | --------------------------------------------------------- |
| `utils/otp.py`       | `extract_kode_unik_from_qr()` - Extract & decode QR token |
| `routers/qr.py`      | `POST /qr/scan` - Endpoint handler                        |
| `schemas/schemas.py` | `QRScanRequest` - Request validation                      |

---

**Status**: ✅ Fully Implemented & Tested
**Version**: 1.0
**Last Updated**: October 16, 2025
