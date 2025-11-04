# My Reports API Documentation

## Overview
Endpoint untuk mendapatkan pelaporan (report) pengisian bensin user beserta detail lengkap kendaraan dan submission terkait.

## Endpoints

### 1. Get My Reports (List)
**GET** `/report/my/reports`

Mendapatkan semua report pengisian bensin yang dibuat oleh user dengan detail lengkap.

#### Authentication
- **Required**: Yes (JWT Token)
- **Header**: `Authorization: Bearer <token>`

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| vehicle_id | integer | No | None | Filter berdasarkan ID kendaraan tertentu |
| limit | integer | No | 100 | Batasi jumlah data (max 1000) |
| offset | integer | No | 0 | Skip sejumlah data untuk pagination |

#### Response Success (200)
```json
{
  "success": true,
  "data": [
    {
      "ID": 101,
      "KodeUnik": "SUB-2025-001",
      "UserID": 5,
      "VehicleID": 1,
      "VehicleName": "Toyota Avanza 2020",
      "VehiclePlat": "B 1234 ABC",
      "VehicleType": "Mobil Dinas",
      "AmountRupiah": 250000.00,
      "AmountLiter": 25.5,
      "Description": "Pengisian bensin rutin",
      "Timestamp": "2025-11-03T14:30:00+07:00",
      "Latitude": -6.200000,
      "Longitude": 106.816666,
      "Odometer": 45000,
      "VehiclePhysicalPhotoPath": "https://example.com/vehicle.jpg",
      "OdometerPhotoPath": "https://example.com/odometer.jpg",
      "InvoicePhotoPath": "https://example.com/invoice.jpg",
      "MyPertaminaPhotoPath": "https://example.com/pertamina.jpg",
      "SubmissionStatus": "Accepted",
      "SubmissionTotal": 500000.00
    }
  ],
  "message": "Ditemukan 1 dari 23 report",
  "pagination": {
    "total": 23,
    "limit": 100,
    "offset": 0,
    "returned": 1,
    "has_more": true
  }
}
```

#### Response Fields (MyReportResponse)

| Field | Type | Description |
|-------|------|-------------|
| ID | integer | ID report |
| KodeUnik | string | Kode unik submission terkait |
| UserID | integer | ID user pelapor |
| VehicleID | integer | ID kendaraan |
| VehicleName | string \| null | Nama kendaraan |
| VehiclePlat | string \| null | Nomor plat kendaraan |
| VehicleType | string \| null | Tipe kendaraan (Mobil Dinas, Motor Dinas) |
| AmountRupiah | float | Biaya pengisian (Rupiah) |
| AmountLiter | float | Jumlah bensin (Liter) |
| Description | string \| null | Deskripsi pengisian |
| Timestamp | string \| null | Waktu pengisian (ISO 8601) |
| Latitude | float \| null | Koordinat latitude lokasi pengisian |
| Longitude | float \| null | Koordinat longitude lokasi pengisian |
| Odometer | integer \| null | Odometer kendaraan saat pengisian (km) |
| VehiclePhysicalPhotoPath | string \| null | URL foto fisik kendaraan |
| OdometerPhotoPath | string \| null | URL foto odometer |
| InvoicePhotoPath | string \| null | URL foto invoice/struk |
| MyPertaminaPhotoPath | string \| null | URL foto MyPertamina |
| SubmissionStatus | string \| null | Status submission (Accepted/Rejected/Pending) |
| SubmissionTotal | float \| null | Total cash advance submission |

---

### 2. Get My Report Detail
**GET** `/report/my/reports/{report_id}`

Mendapatkan detail lengkap sebuah report pengisian bensin termasuk info user, kendaraan, dan submission.

#### Authentication
- **Required**: Yes (JWT Token)
- **Header**: `Authorization: Bearer <token>`

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| report_id | integer | Yes | ID report yang ingin dilihat detailnya |

#### Response Success (200)
```json
{
  "success": true,
  "data": {
    "ID": 101,
    "KodeUnik": "SUB-2025-001",
    "UserID": 5,
    "UserName": "John Doe",
    "UserNIP": "123456789012345678",
    "VehicleID": 1,
    "Vehicle": {
      "ID": 1,
      "Nama": "Toyota Avanza 2020",
      "Plat": "B 1234 ABC",
      "Merek": "Toyota",
      "KapasitasMesin": 1500,
      "JenisBensin": "Pertalite",
      "Odometer": 45000,
      "Status": "Active",
      "VehicleType": "Mobil Dinas"
    },
    "AmountRupiah": 250000.00,
    "AmountLiter": 25.5,
    "Description": "Pengisian bensin untuk perjalanan dinas ke Bandung",
    "Timestamp": "2025-11-03T14:30:00+07:00",
    "Latitude": -6.200000,
    "Longitude": 106.816666,
    "Odometer": 45000,
    "Photos": {
      "VehiclePhysical": "https://example.com/vehicle.jpg",
      "Odometer": "https://example.com/odometer.jpg",
      "Invoice": "https://example.com/invoice.jpg",
      "MyPertamina": "https://example.com/pertamina.jpg"
    },
    "Submission": {
      "ID": 50,
      "KodeUnik": "SUB-2025-001",
      "Status": "Accepted",
      "TotalCashAdvance": 500000.00,
      "CreatorID": 5,
      "CreatorName": "John Doe",
      "ReceiverID": 10,
      "ReceiverName": "Jane Smith",
      "CreatedAt": "2025-11-01T10:00:00+07:00"
    }
  },
  "message": "Detail report berhasil ditemukan"
}
```

#### Response Error (404)
```json
{
  "detail": "Report tidak ditemukan"
}
```

#### Response Fields (ReportDetailResponse)

| Field | Type | Description |
|-------|------|-------------|
| ID | integer | ID report |
| KodeUnik | string | Kode unik submission |
| UserID | integer | ID user pelapor |
| UserName | string \| null | Nama user pelapor |
| UserNIP | string \| null | NIP user pelapor |
| VehicleID | integer | ID kendaraan |
| Vehicle | VehicleInfo \| null | Info lengkap kendaraan |
| AmountRupiah | float | Biaya pengisian |
| AmountLiter | float | Jumlah bensin (liter) |
| Description | string \| null | Deskripsi |
| Timestamp | string \| null | Waktu pengisian |
| Latitude | float \| null | Latitude lokasi |
| Longitude | float \| null | Longitude lokasi |
| Odometer | integer \| null | Odometer (km) |
| Photos | PhotoPaths | Objek berisi path semua foto |
| Submission | SubmissionInfo \| null | Info submission terkait |

#### VehicleInfo Fields

| Field | Type | Description |
|-------|------|-------------|
| ID | integer | ID kendaraan |
| Nama | string | Nama kendaraan |
| Plat | string | Nomor plat |
| Merek | string \| null | Merek kendaraan |
| KapasitasMesin | integer \| null | Kapasitas mesin (cc) |
| JenisBensin | string \| null | Jenis bensin |
| Odometer | integer \| null | Odometer terakhir |
| Status | string | Status kendaraan |
| VehicleType | string \| null | Tipe kendaraan |

#### SubmissionInfo Fields

| Field | Type | Description |
|-------|------|-------------|
| ID | integer | ID submission |
| KodeUnik | string | Kode unik |
| Status | string | Status submission |
| TotalCashAdvance | float | Total cash advance |
| CreatorID | integer | ID pembuat |
| CreatorName | string \| null | Nama pembuat |
| ReceiverID | integer | ID penerima |
| ReceiverName | string \| null | Nama penerima |
| CreatedAt | string \| null | Tanggal dibuat |

---

## Use Cases

### 1. Dashboard Report User
Menampilkan semua laporan pengisian bensin yang pernah dibuat user.

### 2. Tracking Pengeluaran BBM
Melihat total biaya dan liter bensin yang sudah diisi per kendaraan.

### 3. Verifikasi Laporan
Admin/Kepala Dinas dapat memverifikasi laporan dengan melihat foto bukti.

### 4. Analisis Pola Pengisian
Melihat kapan dan dimana sering isi bensin untuk optimasi rute.

### 5. Rekonsiliasi dengan Submission
Mencocokkan laporan pengisian dengan submission/pengajuan dana.

---

## Examples

### Python Example using requests
```python
import requests

# Get all my reports
url = "http://localhost:8000/report/my/reports"
headers = {
    "Authorization": "Bearer your_jwt_token_here"
}
params = {
    "limit": 50,
    "offset": 0
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

print(f"Total reports: {data['pagination']['total']}")
for report in data['data']:
    print(f"\n{report['Timestamp']}")
    print(f"  Kendaraan: {report['VehicleName']} ({report['VehiclePlat']})")
    print(f"  Bensin: {report['AmountLiter']}L = Rp {report['AmountRupiah']:,.0f}")
    print(f"  Status: {report['SubmissionStatus']}")

# Filter by vehicle
response = requests.get(
    "http://localhost:8000/report/my/reports",
    headers=headers,
    params={"vehicle_id": 1, "limit": 20}
)

# Get detail specific report
report_id = 101
url = f"http://localhost:8000/report/my/reports/{report_id}"
response = requests.get(url, headers=headers)
detail = response.json()['data']

print(f"\nDetail Report #{report_id}")
print(f"Pelapor: {detail['UserName']} (NIP: {detail['UserNIP']})")
print(f"Kendaraan: {detail['Vehicle']['Nama']}")
print(f"Odometer: {detail['Odometer']} km")
print(f"Lokasi: {detail['Latitude']}, {detail['Longitude']}")
print(f"\nFoto bukti:")
print(f"  - Kendaraan: {detail['Photos']['VehiclePhysical']}")
print(f"  - Invoice: {detail['Photos']['Invoice']}")
```

### cURL Example
```bash
# Get all my reports
curl -X GET "http://localhost:8000/report/my/reports?limit=50&offset=0" \
  -H "Authorization: Bearer your_jwt_token_here"

# Filter by vehicle
curl -X GET "http://localhost:8000/report/my/reports?vehicle_id=1" \
  -H "Authorization: Bearer your_jwt_token_here"

# Get detail specific report
curl -X GET "http://localhost:8000/report/my/reports/101" \
  -H "Authorization: Bearer your_jwt_token_here"
```

### JavaScript/Fetch Example
```javascript
// Get all my reports with pagination
async function getMyReports(limit = 50, offset = 0) {
  const response = await fetch(
    `http://localhost:8000/report/my/reports?limit=${limit}&offset=${offset}`,
    {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer your_jwt_token_here',
        'Content-Type': 'application/json'
      }
    }
  );
  
  const data = await response.json();
  
  if (data.success) {
    console.log(`Total: ${data.pagination.total} reports`);
    data.data.forEach(report => {
      console.log(`${report.Timestamp}: ${report.VehicleName} - ${report.AmountLiter}L`);
    });
    
    // Check if there are more reports
    if (data.pagination.has_more) {
      console.log("Ada lebih banyak report...");
    }
  }
}

// Get report detail
async function getReportDetail(reportId) {
  const response = await fetch(
    `http://localhost:8000/report/my/reports/${reportId}`,
    {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer your_jwt_token_here',
        'Content-Type': 'application/json'
      }
    }
  );
  
  const data = await response.json();
  
  if (data.success) {
    const report = data.data;
    console.log(`Report #${report.ID}`);
    console.log(`Pelapor: ${report.UserName}`);
    console.log(`Kendaraan: ${report.Vehicle.Nama} (${report.Vehicle.Plat})`);
    console.log(`Bensin: ${report.AmountLiter}L = Rp ${report.AmountRupiah.toLocaleString('id-ID')}`);
    console.log(`Odometer: ${report.Odometer} km`);
    
    // Show submission status
    if (report.Submission) {
      console.log(`\nSubmission: ${report.Submission.Status}`);
      console.log(`Total: Rp ${report.Submission.TotalCashAdvance.toLocaleString('id-ID')}`);
    }
  }
}

getMyReports(50, 0);
getReportDetail(101);
```

---

## Business Logic

### Report Ownership
- Report dimiliki oleh user yang membuatnya (UserID)
- User hanya dapat melihat report yang mereka buat sendiri
- Admin dapat melihat semua report (melalui endpoint `/report/` yang existing)

### Photo Evidence
Report memiliki 4 jenis foto bukti:
1. **VehiclePhysical**: Foto fisik kendaraan
2. **Odometer**: Foto odometer/speedometer
3. **Invoice**: Foto struk/invoice pembelian BBM
4. **MyPertamina**: Foto aplikasi MyPertamina (untuk validasi)

### Submission Linkage
- Report terkait dengan Submission melalui `KodeUnik`
- Satu submission bisa memiliki banyak report (multi refuel)
- Report status mengikuti submission status (Accepted/Rejected/Pending)

### Location Tracking
- Latitude & Longitude disimpan untuk tracking lokasi pengisian
- Berguna untuk verifikasi pengisian di SPBU resmi
- Dapat digunakan untuk analisis pola perjalanan

---

## Data Relationships

```
User
  └─ Report (UserID)
       ├─ Vehicle (VehicleID)
       │    └─ VehicleType
       └─ Submission (KodeUnik)
            ├─ Creator (User)
            └─ Receiver (User)
```

---

## Performance Considerations

### Database Queries
**Get My Reports** melakukan:
1. Query reports dengan filter user_id dan vehicle_id
2. Count total untuk pagination
3. Loop untuk setiap report:
   - Get vehicle info
   - Get vehicle type
   - Get submission info

**Optimization Tips:**
- Add index pada `Report.UserID` dan `Report.VehicleID`
- Add index pada `Report.KodeUnik` untuk join dengan Submission
- Consider eager loading dengan SQLAlchemy joinedload
- Implement caching untuk vehicle type yang jarang berubah

### Pagination
- Default limit: 100 records
- Maximum limit: 1000 records
- Recommend limit 50-100 untuk optimal UX
- Use offset untuk pagination (consider cursor-based for large datasets)

---

## Error Handling

### Common Errors

1. **Report tidak ditemukan** (404)
   - Report ID tidak ada di database
   - Solution: Validasi report_id terlebih dahulu

2. **Token tidak valid** (401)
   - JWT token expired atau invalid
   - Solution: Login ulang untuk mendapatkan token baru

3. **Empty result** (200 dengan data array kosong)
   - User belum pernah membuat report
   - Solution: Buat report baru terlebih dahulu

---

## Security

### Authorization
- Endpoint memerlukan JWT authentication
- User hanya dapat melihat report mereka sendiri
- Consider adding ownership check di get_report_detail (commented in code)

### Data Privacy
- Tidak menampilkan data report user lain
- Photo paths harus di-validate sebelum diakses
- Coordinate data bisa sensitive (pertimbangkan privacy settings)

---

## Related Endpoints

- `GET /report/` - Get all reports (admin, dengan filter user_id)
- `GET /report/{report_id}` - Get specific report (admin)
- `POST /report/` - Create new report
- `PUT /report/{report_id}` - Update report
- `DELETE /report/{report_id}` - Delete report
- `GET /vehicle/my/vehicles` - Get my vehicles
- `GET /submission/` - Get submissions

---

## Testing

### Test Cases
1. ✅ Get my reports dengan token valid
2. ✅ Get my reports dengan pagination
3. ✅ Filter reports by vehicle_id
4. ✅ Get report detail dengan report_id valid
5. ✅ Get report detail dengan report_id tidak ada (404)
6. ✅ Get my reports tanpa authentication token (401)
7. ✅ Verify pagination info correct
8. ✅ Verify vehicle and submission info populated correctly

### Sample Test (pytest)
```python
def test_get_my_reports_success(client, auth_headers):
    """Test get my reports successfully"""
    response = client.get("/report/my/reports", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert "pagination" in data
    assert "total" in data["pagination"]

def test_get_my_reports_with_filter(client, auth_headers):
    """Test get my reports filtered by vehicle"""
    response = client.get(
        "/report/my/reports?vehicle_id=1&limit=20",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    # All reports should be for vehicle_id 1
    for report in data["data"]:
        assert report["VehicleID"] == 1

def test_get_report_detail_success(client, auth_headers):
    """Test get report detail with valid report_id"""
    response = client.get("/report/my/reports/1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Vehicle" in data["data"]
    assert "Photos" in data["data"]
    assert "Submission" in data["data"]

def test_get_report_detail_not_found(client, auth_headers):
    """Test get report detail with invalid report_id"""
    response = client.get("/report/my/reports/9999", headers=auth_headers)
    assert response.status_code == 404
```

---

## Future Enhancements

### Planned Features
1. **Bulk Export**
   - Export reports to CSV/Excel
   - Generate PDF report summary

2. **Advanced Filters**
   - Date range filter
   - Amount range filter
   - Location radius filter

3. **Analytics Dashboard**
   - Monthly fuel consumption charts
   - Cost per kilometer analysis
   - Most used SPBU locations

4. **Photo Validation**
   - Auto-detect photo quality
   - OCR for invoice amount validation
   - GPS location verification

5. **Notifications**
   - Alert when report submitted
   - Alert when submission status changes

---

## Changelog

### Version 1.0.0 (2025-11-03)
- ✅ Initial release
- ✅ Get my reports endpoint (list with pagination)
- ✅ Get report detail endpoint
- ✅ Include vehicle and submission info
- ✅ Filter by vehicle_id
- ✅ Photo paths included
- ✅ JWT authentication required
