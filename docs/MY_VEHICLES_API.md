# My Vehicles API Documentation

## Overview

Endpoint untuk mendapatkan kendaraan yang terkait dengan user beserta detail penggunaan dan riwayat pengisian bensin.

## Endpoints

### 1. Get My Vehicles (List)

**GET** `/vehicle/my/vehicles`

Mendapatkan semua kendaraan yang pernah digunakan oleh user melalui submission atau report.

#### Authentication

- **Required**: Yes (JWT Token)
- **Header**: `Authorization: Bearer <token>`

#### Response Success (200)

```json
{
	"success": true,
	"data": [
		{
			"ID": 1,
			"Nama": "Toyota Avanza 2020",
			"Plat": "B 1234 ABC",
			"Merek": "Toyota",
			"KapasitasMesin": 1500,
			"JenisBensin": "Pertalite",
			"Odometer": 45000,
			"Status": "Active",
			"FotoFisik": "https://example.com/photo.jpg",
			"VehicleTypeID": 1,
			"VehicleTypeName": "Mobil Dinas",
			"TotalSubmissions": 15,
			"TotalReports": 23,
			"TotalFuelLiters": 450.5,
			"TotalRupiahSpent": 4500000.0,
			"LastRefuelDate": "2025-11-03T14:30:00+07:00",
			"LastRefuelLiters": 25.5,
			"LastRefuelRupiah": 250000.0,
			"LastOdometer": 45000
		},
		{
			"ID": 2,
			"Nama": "Honda Beat 2019",
			"Plat": "B 5678 DEF",
			"Merek": "Honda",
			"KapasitasMesin": 110,
			"JenisBensin": "Pertalite",
			"Odometer": 12000,
			"Status": "Active",
			"FotoFisik": null,
			"VehicleTypeID": 2,
			"VehicleTypeName": "Motor Dinas",
			"TotalSubmissions": 8,
			"TotalReports": 12,
			"TotalFuelLiters": 120.0,
			"TotalRupiahSpent": 1200000.0,
			"LastRefuelDate": "2025-11-02T09:15:00+07:00",
			"LastRefuelLiters": 10.0,
			"LastRefuelRupiah": 100000.0,
			"LastOdometer": 12000
		}
	],
	"message": "Ditemukan 2 kendaraan"
}
```

#### Response Fields (MyVehicleResponse)

| Field            | Type            | Description                                       |
| ---------------- | --------------- | ------------------------------------------------- |
| ID               | integer         | ID kendaraan                                      |
| Nama             | string          | Nama kendaraan                                    |
| Plat             | string          | Nomor plat kendaraan                              |
| Merek            | string \| null  | Merek kendaraan (Toyota, Honda, dll)              |
| KapasitasMesin   | integer \| null | Kapasitas mesin (cc)                              |
| JenisBensin      | string \| null  | Jenis bensin (Pertalite, Pertamax, dll)           |
| Odometer         | integer \| null | Odometer terakhir (km)                            |
| Status           | string          | Status kendaraan (Active/Nonactive)               |
| FotoFisik        | string \| null  | URL foto kendaraan                                |
| VehicleTypeID    | integer         | ID tipe kendaraan                                 |
| VehicleTypeName  | string \| null  | Nama tipe kendaraan                               |
| TotalSubmissions | integer         | Total submission yang menggunakan kendaraan ini   |
| TotalReports     | integer         | Total report pengisian bensin untuk kendaraan ini |
| TotalFuelLiters  | float           | Total liter bensin yang diisi                     |
| TotalRupiahSpent | float           | Total rupiah yang dikeluarkan untuk bensin        |
| LastRefuelDate   | string \| null  | Tanggal pengisian bensin terakhir (ISO 8601)      |
| LastRefuelLiters | float \| null   | Jumlah liter pengisian terakhir                   |
| LastRefuelRupiah | float \| null   | Biaya pengisian terakhir                          |
| LastOdometer     | integer \| null | Odometer saat pengisian terakhir                  |

---

### 2. Get My Vehicle Detail

**GET** `/vehicle/my/vehicles/{vehicle_id}`

Mendapatkan detail lengkap sebuah kendaraan termasuk riwayat 10 pengisian bensin terakhir.

#### Authentication

- **Required**: Yes (JWT Token)
- **Header**: `Authorization: Bearer <token>`

#### Path Parameters

| Parameter  | Type    | Required | Description                               |
| ---------- | ------- | -------- | ----------------------------------------- |
| vehicle_id | integer | Yes      | ID kendaraan yang ingin dilihat detailnya |

#### Response Success (200)

```json
{
	"success": true,
	"data": {
		"ID": 1,
		"Nama": "Toyota Avanza 2020",
		"Plat": "B 1234 ABC",
		"Merek": "Toyota",
		"KapasitasMesin": 1500,
		"JenisBensin": "Pertalite",
		"Odometer": 45000,
		"Status": "Active",
		"FotoFisik": "https://example.com/photo.jpg",
		"VehicleTypeID": 1,
		"VehicleTypeName": "Mobil Dinas",
		"TotalSubmissions": 15,
		"TotalReports": 23,
		"TotalFuelLiters": 450.5,
		"TotalRupiahSpent": 4500000.0,
		"RecentRefuelHistory": [
			{
				"ID": 101,
				"KodeUnik": "SUB-2025-001",
				"AmountRupiah": 250000.0,
				"AmountLiter": 25.5,
				"Description": "Isi bensin rutin",
				"Timestamp": "2025-11-03T14:30:00+07:00",
				"Odometer": 45000,
				"Latitude": -6.2,
				"Longitude": 106.816666
			},
			{
				"ID": 98,
				"KodeUnik": "SUB-2025-002",
				"AmountRupiah": 200000.0,
				"AmountLiter": 20.0,
				"Description": "Isi bensin perjalanan dinas",
				"Timestamp": "2025-10-30T10:15:00+07:00",
				"Odometer": 44500,
				"Latitude": -6.17511,
				"Longitude": 106.865036
			}
		]
	},
	"message": "Detail kendaraan berhasil ditemukan"
}
```

#### Response Error (404)

```json
{
	"detail": "Kendaraan tidak ditemukan"
}
```

#### Response Fields (VehicleDetailResponse)

| Field               | Type            | Description                          |
| ------------------- | --------------- | ------------------------------------ |
| ID                  | integer         | ID kendaraan                         |
| Nama                | string          | Nama kendaraan                       |
| Plat                | string          | Nomor plat kendaraan                 |
| Merek               | string \| null  | Merek kendaraan                      |
| KapasitasMesin      | integer \| null | Kapasitas mesin (cc)                 |
| JenisBensin         | string \| null  | Jenis bensin                         |
| Odometer            | integer \| null | Odometer terakhir (km)               |
| Status              | string          | Status kendaraan                     |
| FotoFisik           | string \| null  | URL foto kendaraan                   |
| VehicleTypeID       | integer         | ID tipe kendaraan                    |
| VehicleTypeName     | string \| null  | Nama tipe kendaraan                  |
| TotalSubmissions    | integer         | Total submission                     |
| TotalReports        | integer         | Total report pengisian bensin        |
| TotalFuelLiters     | float           | Total liter bensin yang diisi        |
| TotalRupiahSpent    | float           | Total rupiah untuk bensin            |
| RecentRefuelHistory | array           | Riwayat 10 pengisian bensin terakhir |

#### RefuelHistoryItem Fields

| Field        | Type            | Description                  |
| ------------ | --------------- | ---------------------------- |
| ID           | integer         | ID report                    |
| KodeUnik     | string          | Kode unik submission         |
| AmountRupiah | float           | Biaya pengisian (Rupiah)     |
| AmountLiter  | float           | Jumlah bensin (Liter)        |
| Description  | string \| null  | Deskripsi pengisian          |
| Timestamp    | string          | Waktu pengisian (ISO 8601)   |
| Odometer     | integer \| null | Odometer saat pengisian (km) |
| Latitude     | float \| null   | Koordinat latitude           |
| Longitude    | float \| null   | Koordinat longitude          |

---

## Use Cases

### 1. Dashboard Kendaraan User

Menampilkan semua kendaraan yang pernah digunakan dengan statistik ringkas.

### 2. Monitoring Konsumsi BBM

Melihat total bensin yang sudah diisi untuk setiap kendaraan.

### 3. Riwayat Penggunaan Kendaraan

Tracking pengisian bensin terakhir dan total biaya yang dikeluarkan.

### 4. Analisis Efisiensi Kendaraan

Menghitung konsumsi BBM per kilometer berdasarkan total liter dan odometer.

### 5. Validasi Submission Baru

Cek kendaraan yang pernah digunakan sebelum membuat submission baru.

---

## Examples

### Python Example using requests

```python
import requests

# Get all my vehicles
url = "http://localhost:8000/vehicle/my/vehicles"
headers = {
    "Authorization": "Bearer your_jwt_token_here"
}

response = requests.get(url, headers=headers)
data = response.json()

print(f"Total kendaraan: {len(data['data'])}")
for vehicle in data['data']:
    print(f"\n{vehicle['Nama']} ({vehicle['Plat']})")
    print(f"  Total Bensin: {vehicle['TotalFuelLiters']} liter")
    print(f"  Total Biaya: Rp {vehicle['TotalRupiahSpent']:,.0f}")
    print(f"  Isi terakhir: {vehicle['LastRefuelDate']}")

# Get detail specific vehicle
vehicle_id = 1
url = f"http://localhost:8000/vehicle/my/vehicles/{vehicle_id}"
response = requests.get(url, headers=headers)
detail = response.json()['data']

print(f"\nDetail {detail['Nama']}")
print(f"Total Reports: {detail['TotalReports']}")
print(f"\nRiwayat 10 Pengisian Terakhir:")
for refuel in detail['RecentRefuelHistory']:
    print(f"  - {refuel['Timestamp']}: {refuel['AmountLiter']}L = Rp {refuel['AmountRupiah']:,.0f}")
```

### cURL Example

```bash
# Get all my vehicles
curl -X GET "http://localhost:8000/vehicle/my/vehicles" \
  -H "Authorization: Bearer your_jwt_token_here"

# Get detail specific vehicle
curl -X GET "http://localhost:8000/vehicle/my/vehicles/1" \
  -H "Authorization: Bearer your_jwt_token_here"
```

### JavaScript/Fetch Example

```javascript
// Get all my vehicles
async function getMyVehicles() {
	const response = await fetch("http://localhost:8000/vehicle/my/vehicles", {
		method: "GET",
		headers: {
			Authorization: "Bearer your_jwt_token_here",
			"Content-Type": "application/json"
		}
	});

	const data = await response.json();

	if (data.success) {
		console.log(`Total kendaraan: ${data.data.length}`);
		data.data.forEach((vehicle) => {
			console.log(`${vehicle.Nama} (${vehicle.Plat})`);
			console.log(
				`  BBM: ${
					vehicle.TotalFuelLiters
				}L / Rp ${vehicle.TotalRupiahSpent.toLocaleString("id-ID")}`
			);
		});
	}
}

// Get vehicle detail with refuel history
async function getVehicleDetail(vehicleId) {
	const response = await fetch(
		`http://localhost:8000/vehicle/my/vehicles/${vehicleId}`,
		{
			method: "GET",
			headers: {
				Authorization: "Bearer your_jwt_token_here",
				"Content-Type": "application/json"
			}
		}
	);

	const data = await response.json();

	if (data.success) {
		const vehicle = data.data;
		console.log(`Detail: ${vehicle.Nama}`);
		console.log(`Status: ${vehicle.Status}`);
		console.log(`Odometer: ${vehicle.Odometer} km`);
		console.log(`\nRiwayat Pengisian:`);
		vehicle.RecentRefuelHistory.forEach((refuel) => {
			console.log(
				`  ${refuel.Timestamp}: ${refuel.AmountLiter}L @ Odometer ${refuel.Odometer}km`
			);
		});
	}
}

getMyVehicles();
getVehicleDetail(1);
```

---

## Business Logic

### Vehicle Association

Kendaraan dianggap "milik" user jika:

1. User pernah membuat submission menggunakan kendaraan tersebut (sebagai Creator)
2. User pernah menerima submission untuk kendaraan tersebut (sebagai Receiver)
3. User pernah membuat report pengisian bensin untuk kendaraan tersebut

### Statistics Calculation

#### Total Fuel Liters

```sql
SUM(Report.AmountLiter)
WHERE Report.VehicleID = vehicle_id
  AND Report.UserID = user_id
```

#### Total Rupiah Spent

```sql
SUM(Report.AmountRupiah)
WHERE Report.VehicleID = vehicle_id
  AND Report.UserID = user_id
```

#### Average Fuel Consumption

```
Average = TotalFuelLiters / (CurrentOdometer - StartOdometer)
```

### Refuel History

- Diurutkan dari yang terbaru (Timestamp DESC)
- Dibatasi 10 record terakhir
- Termasuk data odometer untuk tracking efisiensi

---

## Data Relationships

```
User
  └─ Submission (CreatorID/ReceiverID)
       └─ Vehicle
  └─ Report (UserID)
       └─ Vehicle

Vehicle
  ├─ VehicleType
  ├─ Submission[]
  └─ Report[]
```

---

## Performance Considerations

### Database Queries

**Get My Vehicles** melakukan:

1. Query distinct vehicle IDs dari Submission (2 kondisi: Creator/Receiver)
2. Query distinct vehicle IDs dari Report
3. Loop untuk setiap vehicle:
   - Get vehicle detail
   - Get vehicle type
   - Count submissions
   - Count reports
   - Sum fuel liters
   - Sum rupiah
   - Get latest report

**Optimization Opportunities:**

- Add index pada `Submission.VehicleID`
- Add index pada `Report.VehicleID` dan `Report.UserID`
- Consider caching untuk statistics yang jarang berubah
- Use JOIN untuk mengurangi jumlah query

### Response Size

- List endpoint: ~500 bytes per vehicle
- Detail endpoint: ~2KB per vehicle (dengan 10 refuel history)
- Recommend pagination jika user memiliki >50 kendaraan

---

## Error Handling

### Common Errors

1. **Kendaraan tidak ditemukan** (404)

   - Vehicle ID tidak ada di database
   - Solution: Validasi vehicle_id terlebih dahulu

2. **Token tidak valid** (401)

   - JWT token expired atau invalid
   - Solution: Login ulang untuk mendapatkan token baru

3. **Empty result** (200 dengan data array kosong)
   - User belum pernah menggunakan kendaraan apapun
   - Solution: Buat submission atau report terlebih dahulu

---

## Security

### Authorization

- Endpoint memerlukan JWT authentication
- User hanya dapat melihat kendaraan yang pernah mereka gunakan
- Admin bisa menambahkan parameter `user_id` untuk melihat kendaraan user lain (future enhancement)

### Data Privacy

- Hanya menampilkan data report/submission yang terkait dengan user
- Tidak menampilkan data report dari user lain untuk kendaraan yang sama

---

## Related Endpoints

- `GET /vehicle/` - Get all vehicles (admin)
- `POST /vehicle/` - Create new vehicle (admin)
- `PUT /vehicle/{vehicle_id}` - Update vehicle (admin)
- `POST /report/` - Create fuel refill report
- `GET /submission/` - Get submissions using vehicles

---

## Testing

### Test Cases

1. ✅ Get my vehicles dengan token valid
2. ✅ Get my vehicles tanpa vehicle yang pernah digunakan (empty array)
3. ✅ Get vehicle detail dengan vehicle_id valid
4. ✅ Get vehicle detail dengan vehicle_id tidak ada (404)
5. ✅ Get my vehicles tanpa authentication token (401)
6. ✅ Verify statistics calculation (fuel, rupiah, submissions, reports)

### Sample Test (pytest)

```python
def test_get_my_vehicles_success(client, auth_headers, create_test_data):
    """Test get my vehicles successfully"""
    response = client.get("/vehicle/my/vehicles", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    if len(data["data"]) > 0:
        vehicle = data["data"][0]
        assert "ID" in vehicle
        assert "Plat" in vehicle
        assert "TotalFuelLiters" in vehicle

def test_get_vehicle_detail_success(client, auth_headers):
    """Test get vehicle detail with valid vehicle_id"""
    response = client.get("/vehicle/my/vehicles/1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "RecentRefuelHistory" in data["data"]
    assert isinstance(data["data"]["RecentRefuelHistory"], list)

def test_get_vehicle_detail_not_found(client, auth_headers):
    """Test get vehicle detail with invalid vehicle_id"""
    response = client.get("/vehicle/my/vehicles/9999", headers=auth_headers)
    assert response.status_code == 404
```

---

## Future Enhancements

### Planned Features

1. **Fuel Efficiency Calculation**

   - Average km/liter per vehicle
   - Comparison with vehicle specifications

2. **Cost Analysis**

   - Monthly fuel cost trends
   - Cost per kilometer calculation

3. **Maintenance Tracking**

   - Odometer-based maintenance reminders
   - Service history integration

4. **Export Reports**

   - CSV/PDF export untuk refuel history
   - Monthly/yearly fuel consumption reports

5. **Filters & Sorting**
   - Filter by vehicle type
   - Sort by last refuel date, total cost, etc.

---

## Changelog

### Version 1.0.0 (2025-11-03)

- ✅ Initial release
- ✅ Get my vehicles endpoint (list)
- ✅ Get vehicle detail endpoint
- ✅ Include fuel refill statistics
- ✅ Include refuel history (last 10)
- ✅ JWT authentication required
