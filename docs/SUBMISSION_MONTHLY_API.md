# API Endpoint Pengajuan Penggunaan Dana (Submission) Per Bulan

## Overview

API ini menyediakan endpoint untuk mendapatkan data pengajuan penggunaan dana dengan filtering per bulan, termasuk ringkasan statistik dan detail lengkap.

## Endpoints

### 1. GET `/submission/monthly/summary`

Mendapatkan **ringkasan** pengajuan penggunaan dana per bulan

#### Query Parameters

| Parameter | Type    | Required | Description  | Validation         |
| --------- | ------- | -------- | ------------ | ------------------ |
| month     | integer | Yes      | Bulan (1-12) | 1 ≤ month ≤ 12     |
| year      | integer | Yes      | Tahun        | 2000 ≤ year ≤ 2100 |

#### Response

```json
{
	"success": true,
	"data": {
		"month": 11,
		"year": 2025,
		"total_submissions": 15,
		"total_pending": 5,
		"total_accepted": 8,
		"total_rejected": 2,
		"total_cash_advance": 50000000.0,
		"total_cash_advance_accepted": 30000000.0,
		"total_cash_advance_rejected": 5000000.0,
		"total_cash_advance_pending": 15000000.0
	},
	"message": "Ringkasan pengajuan bulan 11/2025"
}
```

#### Example Request

```bash
GET /submission/monthly/summary?month=11&year=2025
Authorization: Bearer <token>
```

---

### 2. GET `/submission/monthly/details`

Mendapatkan **detail lengkap** pengajuan penggunaan dana per bulan

#### Query Parameters

| Parameter | Type    | Required | Description  | Validation         |
| --------- | ------- | -------- | ------------ | ------------------ |
| month     | integer | Yes      | Bulan (1-12) | 1 ≤ month ≤ 12     |
| year      | integer | Yes      | Tahun        | 2000 ≤ year ≤ 2100 |

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
	"message": "Detail pengajuan bulan 11/2025"
}
```

#### Example Request

```bash
GET /submission/monthly/details?month=11&year=2025
Authorization: Bearer <token>
```

---

### 3. GET `/submission/monthly/report`

Mendapatkan **laporan lengkap** (ringkasan + detail) pengajuan penggunaan dana per bulan

#### Query Parameters

| Parameter | Type    | Required | Description  | Validation         |
| --------- | ------- | -------- | ------------ | ------------------ |
| month     | integer | Yes      | Bulan (1-12) | 1 ≤ month ≤ 12     |
| year      | integer | Yes      | Tahun        | 2000 ≤ year ≤ 2100 |

#### Response

```json
{
	"success": true,
	"data": {
		"summary": {
			"month": 11,
			"year": 2025,
			"total_submissions": 15,
			"total_pending": 5,
			"total_accepted": 8,
			"total_rejected": 2,
			"total_cash_advance": 50000000.0,
			"total_cash_advance_accepted": 30000000.0,
			"total_cash_advance_rejected": 5000000.0,
			"total_cash_advance_pending": 15000000.0
		},
		"details": [
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
			}
		]
	},
	"message": "Laporan lengkap pengajuan bulan 11/2025"
}
```

#### Example Request

```bash
GET /submission/monthly/report?month=11&year=2025
Authorization: Bearer <token>
```

---

## Schema Details

### SubmissionSummary

| Field                       | Type    | Description                             |
| --------------------------- | ------- | --------------------------------------- |
| month                       | integer | Bulan (1-12)                            |
| year                        | integer | Tahun                                   |
| total_submissions           | integer | Total pengajuan dalam bulan tersebut    |
| total_pending               | integer | Jumlah pengajuan dengan status Pending  |
| total_accepted              | integer | Jumlah pengajuan dengan status Accepted |
| total_rejected              | integer | Jumlah pengajuan dengan status Rejected |
| total_cash_advance          | float   | Total dana yang diajukan                |
| total_cash_advance_accepted | float   | Total dana yang diterima (Accepted)     |
| total_cash_advance_rejected | float   | Total dana yang ditolak (Rejected)      |
| total_cash_advance_pending  | float   | Total dana yang menunggu (Pending)      |

### SubmissionDetailResponse

| Field            | Type                 | Description                                  |
| ---------------- | -------------------- | -------------------------------------------- |
| ID               | integer              | ID pengajuan                                 |
| KodeUnik         | string               | Kode unik pengajuan                          |
| CreatorID        | integer              | ID pembuat pengajuan                         |
| CreatorName      | string               | Nama pembuat pengajuan                       |
| ReceiverID       | integer              | ID penerima pengajuan                        |
| ReceiverName     | string               | Nama penerima pengajuan                      |
| TotalCashAdvance | float                | Total dana yang diajukan                     |
| VehicleID        | integer              | ID kendaraan                                 |
| VehicleName      | string               | Nama kendaraan                               |
| VehiclePlat      | string               | Plat nomor kendaraan                         |
| Status           | SubmissionStatusEnum | Status pengajuan (Pending/Accepted/Rejected) |
| created_at       | datetime             | Waktu pembuatan pengajuan                    |

---

## Authentication

Semua endpoint memerlukan authentication dengan Bearer token JWT.

```bash
Authorization: Bearer <your_jwt_token>
```

---

## Error Responses

### 400 Bad Request

```json
{
	"detail": "Bulan harus antara 1-12"
}
```

### 401 Unauthorized

```json
{
	"detail": "Not authenticated"
}
```

---

## Use Cases

### 1. Dashboard Statistik

Gunakan endpoint `/submission/monthly/summary` untuk menampilkan ringkasan statistik di dashboard:

- Grafik jumlah pengajuan per status
- Total dana yang diajukan
- Perbandingan accepted vs rejected

### 2. Laporan Detail

Gunakan endpoint `/submission/monthly/details` untuk:

- Menampilkan tabel detail pengajuan
- Export data ke Excel/PDF
- Audit trail pengajuan

### 3. Laporan Lengkap

Gunakan endpoint `/submission/monthly/report` untuk:

- Laporan bulanan komprehensif
- Kombinasi statistik dan detail dalam satu request
- Efisiensi API call (1 request vs 2 request)

---

## Performance Notes

- Query dioptimalkan dengan menggunakan `extract()` untuk filtering tanggal
- Detail menggunakan join untuk mengurangi N+1 query problem
- Response sudah diurutkan berdasarkan `created_at DESC` (terbaru dulu)

---

## Version History

- **v1.0** (2025-11-02): Initial release dengan 3 endpoint monthly report
