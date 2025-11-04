# API Endpoint Get Users with Details

## Overview

API untuk mendapatkan pengguna dengan detail lengkap termasuk informasi wallet (saldo), dinas, dan statistik submission dengan fitur pencarian dan filtering.

## Endpoint

### GET `/users/detailed/search`

Mendapatkan semua pengguna dengan **detail lengkap** termasuk wallet, dinas, dan submission count

#### Query Parameters

| Parameter   | Type    | Required | Default | Description                            | Validation               |
| ----------- | ------- | -------- | ------- | -------------------------------------- | ------------------------ |
| search      | string  | No       | -       | Cari berdasarkan NIP, Nama, atau Email | Case-insensitive         |
| role        | string  | No       | -       | Filter berdasarkan role                | admin, kepala_dinas, pic |
| dinas_id    | integer | No       | -       | Filter berdasarkan ID dinas            | -                        |
| is_verified | boolean | No       | -       | Filter berdasarkan status verifikasi   | true/false               |
| limit       | integer | No       | 100     | Batasi jumlah data                     | 1 ≤ limit ≤ 1000         |
| offset      | integer | No       | 0       | Skip sejumlah data                     | offset ≥ 0               |

#### Response

```json
{
	"success": true,
	"data": [
		{
			"ID": 1,
			"NIP": "123456789012345678",
			"NamaLengkap": "John Doe",
			"Email": "john.doe@example.com",
			"NoTelepon": "081234567890",
			"Role": "pic",
			"isVerified": true,
			"DinasID": 5,
			"DinasNama": "Dinas Perhubungan",
			"WalletID": 10,
			"WalletSaldo": 5000000.0,
			"WalletType": "Dana Operasional",
			"TotalSubmissionsCreated": 15,
			"TotalSubmissionsReceived": 8
		},
		{
			"ID": 2,
			"NIP": "987654321098765432",
			"NamaLengkap": "Jane Smith",
			"Email": "jane.smith@example.com",
			"NoTelepon": "082345678901",
			"Role": "kepala_dinas",
			"isVerified": true,
			"DinasID": 5,
			"DinasNama": "Dinas Perhubungan",
			"WalletID": 11,
			"WalletSaldo": 10000000.0,
			"WalletType": "Dana Operasional",
			"TotalSubmissionsCreated": 5,
			"TotalSubmissionsReceived": 25
		}
	],
	"message": "Ditemukan 2 dari 150 pengguna",
	"pagination": {
		"total": 150,
		"limit": 100,
		"offset": 0,
		"returned": 2,
		"has_more": true
	}
}
```

#### Response Fields

**User Info:**
| Field | Type | Description |
|-------|------|-------------|
| ID | integer | ID pengguna |
| NIP | string | Nomor Induk Pegawai |
| NamaLengkap | string | Nama lengkap pengguna |
| Email | string | Email pengguna |
| NoTelepon | string | Nomor telepon (nullable) |
| Role | string | Role pengguna (admin, kepala_dinas, pic) |
| isVerified | boolean | Status verifikasi akun |

**Dinas Info:**
| Field | Type | Description |
|-------|------|-------------|
| DinasID | integer | ID dinas (nullable) |
| DinasNama | string | Nama dinas (nullable) |

**Wallet Info:**
| Field | Type | Description |
|-------|------|-------------|
| WalletID | integer | ID wallet (nullable) |
| WalletSaldo | float | Saldo wallet (nullable) |
| WalletType | string | Tipe wallet (nullable) |

**Statistics:**
| Field | Type | Description |
|-------|------|-------------|
| TotalSubmissionsCreated | integer | Total pengajuan yang dibuat |
| TotalSubmissionsReceived | integer | Total pengajuan yang diterima |

**Pagination:**
| Field | Type | Description |
|-------|------|-------------|
| total | integer | Total pengguna yang match filter |
| limit | integer | Limit yang digunakan |
| offset | integer | Offset yang digunakan |
| returned | integer | Jumlah data yang dikembalikan |
| has_more | boolean | Masih ada data berikutnya? |

---

## Example Requests

### 1. Get All Users with Details (First Page)

```bash
GET /users/detailed/search?limit=50&offset=0
Authorization: Bearer <token>
```

### 2. Search by Name

```bash
GET /users/detailed/search?search=John
Authorization: Bearer <token>
```

### 3. Search by Email

```bash
GET /users/detailed/search?search=@example.com
Authorization: Bearer <token>
```

### 4. Search by NIP

```bash
GET /users/detailed/search?search=123456
Authorization: Bearer <token>
```

### 5. Filter by Role

```bash
GET /users/detailed/search?role=pic
Authorization: Bearer <token>
```

### 6. Filter by Dinas

```bash
GET /users/detailed/search?dinas_id=5
Authorization: Bearer <token>
```

### 7. Filter by Verification Status

```bash
GET /users/detailed/search?is_verified=true
Authorization: Bearer <token>
```

### 8. Multiple Filters

```bash
GET /users/detailed/search?role=pic&dinas_id=5&is_verified=true&limit=20
Authorization: Bearer <token>
```

### 9. Search with Pagination

```bash
# Page 1
GET /users/detailed/search?search=John&limit=50&offset=0

# Page 2
GET /users/detailed/search?search=John&limit=50&offset=50
```

---

## Use Cases

### 1. User Management Dashboard

```bash
# Tampilkan semua user dengan wallet balance
GET /users/detailed/search?limit=50
```

### 2. Find Specific User

```bash
# Cari user berdasarkan nama atau email
GET /users/detailed/search?search=John
```

### 3. Filter by Role

```bash
# Lihat semua PIC
GET /users/detailed/search?role=pic

# Lihat semua Kepala Dinas
GET /users/detailed/search?role=kepala_dinas
```

### 4. Check Wallet Balance

```bash
# Cari user dengan saldo wallet tertentu
GET /users/detailed/search?dinas_id=5
```

### 5. Find Users by Dinas

```bash
# Lihat semua user di dinas tertentu
GET /users/detailed/search?dinas_id=5
```

### 6. Verified Users Only

```bash
# Lihat hanya user yang sudah terverifikasi
GET /users/detailed/search?is_verified=true
```

### 7. Combination Filters

```bash
# PIC yang verified di dinas 5
GET /users/detailed/search?role=pic&dinas_id=5&is_verified=true
```

---

## Python Example

```python
import requests

BASE_URL = "http://127.0.0.1:8000"
token = "your_jwt_token"
headers = {"Authorization": f"Bearer {token}"}

def search_users(search=None, role=None, dinas_id=None,
                 is_verified=None, limit=100, offset=0):
    """Search users with detailed information"""
    params = {
        "limit": limit,
        "offset": offset
    }

    if search:
        params["search"] = search
    if role:
        params["role"] = role
    if dinas_id:
        params["dinas_id"] = dinas_id
    if is_verified is not None:
        params["is_verified"] = is_verified

    response = requests.get(
        f"{BASE_URL}/users/detailed/search",
        params=params,
        headers=headers
    )
    response.raise_for_status()
    return response.json()

# Example 1: Search by name
result = search_users(search="John")
print(f"Found {result['pagination']['total']} users")

for user in result['data']:
    print(f"\n{user['NamaLengkap']} ({user['Email']})")
    print(f"  Role: {user['Role']}")
    print(f"  Dinas: {user['DinasNama']}")
    print(f"  Wallet: Rp {user['WalletSaldo']:,.2f}" if user['WalletSaldo'] else "  Wallet: None")
    print(f"  Submissions: Created={user['TotalSubmissionsCreated']}, Received={user['TotalSubmissionsReceived']}")

# Example 2: Get all PIC with pagination
offset = 0
limit = 50
all_pics = []

while True:
    result = search_users(role="pic", limit=limit, offset=offset)
    all_pics.extend(result['data'])

    if not result['pagination']['has_more']:
        break

    offset += limit

print(f"\nTotal PIC: {len(all_pics)}")

# Example 3: Find users in specific dinas
result = search_users(dinas_id=5)
print(f"\nUsers in Dinas 5: {result['pagination']['total']}")

# Example 4: Check wallet balances
result = search_users(limit=100)
total_balance = sum(user['WalletSaldo'] or 0 for user in result['data'])
print(f"\nTotal wallet balance (first 100 users): Rp {total_balance:,.2f}")
```

---

## cURL Examples

### Search by Name

```bash
curl -X GET "http://127.0.0.1:8000/users/detailed/search?search=John" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Filter by Role

```bash
curl -X GET "http://127.0.0.1:8000/users/detailed/search?role=pic" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Filter by Dinas

```bash
curl -X GET "http://127.0.0.1:8000/users/detailed/search?dinas_id=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Multiple Filters with Pagination

```bash
curl -X GET "http://127.0.0.1:8000/users/detailed/search?role=pic&is_verified=true&limit=20&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Search with NIP

```bash
curl -X GET "http://127.0.0.1:8000/users/detailed/search?search=123456" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Response Example

### User with Complete Data

```json
{
	"ID": 1,
	"NIP": "123456789012345678",
	"NamaLengkap": "John Doe",
	"Email": "john.doe@example.com",
	"NoTelepon": "081234567890",
	"Role": "pic",
	"isVerified": true,
	"DinasID": 5,
	"DinasNama": "Dinas Perhubungan",
	"WalletID": 10,
	"WalletSaldo": 5000000.0,
	"WalletType": "Dana Operasional",
	"TotalSubmissionsCreated": 15,
	"TotalSubmissionsReceived": 8
}
```

### User without Wallet or Dinas

```json
{
	"ID": 2,
	"NIP": "987654321098765432",
	"NamaLengkap": "Jane Smith",
	"Email": "jane.smith@example.com",
	"NoTelepon": null,
	"Role": "admin",
	"isVerified": false,
	"DinasID": null,
	"DinasNama": null,
	"WalletID": null,
	"WalletSaldo": null,
	"WalletType": null,
	"TotalSubmissionsCreated": 0,
	"TotalSubmissionsReceived": 0
}
```

---

## Performance Tips

1. **Use pagination** untuk dataset besar
2. **Be specific with filters** untuk mengurangi data yang diproses
3. **Search is case-insensitive** jadi "john" akan match "John Doe"
4. **Limit default 100** sudah optimal untuk kebanyakan kasus
5. **Monitor pagination.total** untuk mengetahui ukuran dataset

---

## Error Responses

### 401 Unauthorized

```json
{
	"detail": "Not authenticated"
}
```

### 422 Validation Error

```json
{
	"detail": [
		{
			"loc": ["query", "limit"],
			"msg": "ensure this value is less than or equal to 1000",
			"type": "value_error.number.not_le"
		}
	]
}
```

---

## Notes

- **Search** mencari di 3 field: NIP, NamaLengkap, Email (case-insensitive)
- **WalletSaldo** dalam Rupiah (IDR)
- **TotalSubmissionsCreated**: Jumlah pengajuan yang dibuat user
- **TotalSubmissionsReceived**: Jumlah pengajuan yang diterima user (sebagai receiver)
- **Role values**: `admin`, `kepala_dinas`, `pic`
- Data diurutkan berdasarkan **ID DESC** (terbaru dulu)
- User tanpa wallet akan memiliki `WalletID`, `WalletSaldo`, dan `WalletType` = null
- User tanpa dinas akan memiliki `DinasID` dan `DinasNama` = null

---

## Comparison with Basic User Endpoint

### Basic `/users/` Endpoint

- ✅ Cepat
- ❌ Hanya data basic user
- ❌ Tidak ada wallet info
- ❌ Tidak ada dinas info
- ❌ Tidak ada submission count

### Detailed `/users/detailed/search` Endpoint

- ✅ Data lengkap termasuk wallet & dinas
- ✅ Submission statistics
- ✅ Search & filter advanced
- ✅ Pagination info lengkap
- ❌ Sedikit lebih lambat (ada join query)

**Rekomendasi:**

- Gunakan `/users/` untuk list simple
- Gunakan `/users/detailed/search` untuk dashboard & reporting
