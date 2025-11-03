# API Endpoint Get All Submissions

## Overview

API untuk mendapatkan semua pengajuan (submission) dengan berbagai opsi filtering, pagination, dan detail lengkap.

## Endpoints

### 1. GET `/submission/`

Mendapatkan semua submission dengan data basic

#### Query Parameters

| Parameter   | Type    | Required | Default | Description                     | Validation                  |
| ----------- | ------- | -------- | ------- | ------------------------------- | --------------------------- |
| creator_id  | integer | No       | -       | Filter berdasarkan ID pembuat   | -                           |
| receiver_id | integer | No       | -       | Filter berdasarkan ID penerima  | -                           |
| vehicle_id  | integer | No       | -       | Filter berdasarkan ID kendaraan | -                           |
| status      | string  | No       | -       | Filter berdasarkan status       | Pending, Accepted, Rejected |
| limit       | integer | No       | -       | Batasi jumlah data              | 1 ≤ limit ≤ 1000            |
| offset      | integer | No       | 0       | Skip sejumlah data              | offset ≥ 0                  |

#### Response

```json
{
	"success": true,
	"data": [
		{
			"ID": 1,
			"KodeUnik": "SUB-2025-11-001",
			"CreatorID": 10,
			"ReceiverID": 5,
			"TotalCashAdvance": 5000000.0,
			"VehicleID": 3,
			"Status": "Pending",
			"created_at": "2025-11-02T10:30:00"
		},
		{
			"ID": 2,
			"KodeUnik": "SUB-2025-11-002",
			"CreatorID": 12,
			"ReceiverID": 5,
			"TotalCashAdvance": 3000000.0,
			"VehicleID": 7,
			"Status": "Accepted",
			"created_at": "2025-11-01T14:20:00"
		}
	],
	"message": "Ditemukan 2 submission"
}
```

#### Example Requests

**Get all submissions:**

```bash
GET /submission/
Authorization: Bearer <token>
```

**Filter by status:**

```bash
GET /submission/?status=Pending
Authorization: Bearer <token>
```

**Filter by creator with pagination:**

```bash
GET /submission/?creator_id=10&limit=50&offset=0
Authorization: Bearer <token>
```

**Filter by vehicle and status:**

```bash
GET /submission/?vehicle_id=3&status=Accepted
Authorization: Bearer <token>
```

---

### 2. GET `/submission/all/detailed`

Mendapatkan semua submission dengan **detail lengkap** (nama creator, receiver, vehicle) dan **pagination info**

#### Query Parameters

| Parameter   | Type    | Required | Default | Description                     | Validation                  |
| ----------- | ------- | -------- | ------- | ------------------------------- | --------------------------- |
| creator_id  | integer | No       | -       | Filter berdasarkan ID pembuat   | -                           |
| receiver_id | integer | No       | -       | Filter berdasarkan ID penerima  | -                           |
| vehicle_id  | integer | No       | -       | Filter berdasarkan ID kendaraan | -                           |
| status      | string  | No       | -       | Filter berdasarkan status       | Pending, Accepted, Rejected |
| limit       | integer | No       | 100     | Batasi jumlah data              | 1 ≤ limit ≤ 1000            |
| offset      | integer | No       | 0       | Skip sejumlah data              | offset ≥ 0                  |

#### Response

```json
{
	"success": true,
	"data": [
		{
			"ID": 1,
			"KodeUnik": "SUB-2025-11-001",
			"CreatorID": 10,
			"CreatorName": "John Doe",
			"ReceiverID": 5,
			"ReceiverName": "Jane Smith",
			"TotalCashAdvance": 5000000.0,
			"VehicleID": 3,
			"VehicleName": "Toyota Avanza",
			"VehiclePlat": "B 1234 XYZ",
			"Status": "Pending",
			"created_at": "2025-11-02T10:30:00"
		},
		{
			"ID": 2,
			"KodeUnik": "SUB-2025-11-002",
			"CreatorID": 12,
			"CreatorName": "Alice Johnson",
			"ReceiverID": 5,
			"ReceiverName": "Jane Smith",
			"TotalCashAdvance": 3000000.0,
			"VehicleID": 7,
			"VehicleName": "Honda CR-V",
			"VehiclePlat": "B 5678 ABC",
			"Status": "Accepted",
			"created_at": "2025-11-01T14:20:00"
		}
	],
	"message": "Ditemukan 2 dari 150 submission",
	"pagination": {
		"total": 150,
		"limit": 100,
		"offset": 0,
		"returned": 2,
		"has_more": true
	}
}
```

#### Pagination Info

| Field    | Type    | Description                            |
| -------- | ------- | -------------------------------------- |
| total    | integer | Total jumlah data yang memenuhi filter |
| limit    | integer | Limit yang digunakan                   |
| offset   | integer | Offset yang digunakan                  |
| returned | integer | Jumlah data yang dikembalikan          |
| has_more | boolean | Apakah masih ada data selanjutnya      |

#### Example Requests

**Get all submissions with details (first page):**

```bash
GET /submission/all/detailed?limit=50&offset=0
Authorization: Bearer <token>
```

**Get next page:**

```bash
GET /submission/all/detailed?limit=50&offset=50
Authorization: Bearer <token>
```

**Filter by status with details:**

```bash
GET /submission/all/detailed?status=Pending&limit=100
Authorization: Bearer <token>
```

**Filter by creator and receiver:**

```bash
GET /submission/all/detailed?creator_id=10&receiver_id=5
Authorization: Bearer <token>
```

---

## Comparison: Basic vs Detailed

### Basic Endpoint (`/submission/`)

✅ **Pros:**

- Lebih cepat (tidak ada join query)
- Data lebih ringkas
- Cocok untuk list sederhana

❌ **Cons:**

- Hanya ID, tidak ada nama
- Perlu query tambahan untuk mendapatkan nama
- Tidak ada pagination info

### Detailed Endpoint (`/submission/all/detailed`)

✅ **Pros:**

- Data lengkap dengan nama creator, receiver, vehicle
- Pagination info lengkap
- Satu query untuk semua info
- Cocok untuk tabel/report

❌ **Cons:**

- Sedikit lebih lambat (ada join query)
- Response lebih besar

---

## Use Cases

### 1. List Pengajuan di Dashboard

```bash
# Tampilkan 20 pengajuan terbaru dengan detail
GET /submission/all/detailed?limit=20&offset=0
```

### 2. Filter Pengajuan Pending

```bash
# Tampilkan semua pengajuan yang masih pending
GET /submission/all/detailed?status=Pending
```

### 3. Pengajuan Berdasarkan User

```bash
# Tampilkan pengajuan yang dibuat oleh user tertentu
GET /submission/all/detailed?creator_id=10
```

### 4. Pagination untuk Large Dataset

```bash
# Page 1
GET /submission/all/detailed?limit=100&offset=0

# Page 2
GET /submission/all/detailed?limit=100&offset=100

# Page 3
GET /submission/all/detailed?limit=100&offset=200
```

### 5. Kombinasi Multiple Filters

```bash
# Pengajuan dari creator 10, untuk vehicle 3, yang masih pending
GET /submission/all/detailed?creator_id=10&vehicle_id=3&status=Pending
```

---

## Python Example

```python
import requests

BASE_URL = "http://127.0.0.1:8000"
token = "your_jwt_token"
headers = {"Authorization": f"Bearer {token}"}

def get_all_submissions_paginated(limit=100, offset=0, status=None):
    """Get submissions with pagination"""
    params = {
        "limit": limit,
        "offset": offset
    }
    if status:
        params["status"] = status

    response = requests.get(
        f"{BASE_URL}/submission/all/detailed",
        params=params,
        headers=headers
    )
    response.raise_for_status()
    return response.json()

# Get first page
result = get_all_submissions_paginated(limit=50, offset=0)
print(f"Total: {result['pagination']['total']}")
print(f"Has more: {result['pagination']['has_more']}")

# Iterate through all pages
offset = 0
limit = 100
all_submissions = []

while True:
    result = get_all_submissions_paginated(limit=limit, offset=offset)
    all_submissions.extend(result['data'])

    if not result['pagination']['has_more']:
        break

    offset += limit

print(f"Total submissions loaded: {len(all_submissions)}")
```

---

## cURL Examples

### Get all submissions (basic)

```bash
curl -X GET "http://127.0.0.1:8000/submission/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get all submissions with details

```bash
curl -X GET "http://127.0.0.1:8000/submission/all/detailed?limit=50&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Filter by status

```bash
curl -X GET "http://127.0.0.1:8000/submission/all/detailed?status=Pending" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Filter by creator

```bash
curl -X GET "http://127.0.0.1:8000/submission/all/detailed?creator_id=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Multiple filters with pagination

```bash
curl -X GET "http://127.0.0.1:8000/submission/all/detailed?creator_id=10&status=Pending&limit=20&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Performance Tips

1. **Use pagination** untuk dataset besar (gunakan limit)
2. **Filter sebanyak mungkin** untuk mengurangi data yang diproses
3. **Use basic endpoint** jika tidak perlu nama detail
4. **Cache results** di frontend jika data tidak sering berubah
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

- Data diurutkan berdasarkan `created_at DESC` (terbaru dulu)
- Default limit untuk detailed endpoint adalah 100
- Maximum limit adalah 1000 untuk mencegah timeout
- Status filter case-sensitive: gunakan `Pending`, `Accepted`, atau `Rejected`
