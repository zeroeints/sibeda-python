# User Balance API Documentation

## Overview

Endpoint untuk mendapatkan saldo wallet user beserta informasi lengkap user dan dinas.

## Endpoint

### Get User Balance

**GET** `/users/balance/{user_id}`

Mendapatkan saldo wallet user dengan detail lengkap termasuk informasi user, dinas, dan tipe wallet.

#### Authentication

- **Required**: Yes (JWT Token)
- **Header**: `Authorization: Bearer <token>`

#### Path Parameters

| Parameter | Type    | Required | Description                       |
| --------- | ------- | -------- | --------------------------------- |
| user_id   | integer | Yes      | ID user yang ingin dicek saldonya |

#### Response Success (200)

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

#### Response Error (404)

**User Not Found**

```json
{
	"detail": "User tidak ditemukan"
}
```

**Wallet Not Found**

```json
{
	"detail": "Wallet tidak ditemukan untuk user ini"
}
```

#### Response Error (401)

**Unauthorized**

```json
{
	"detail": "Not authenticated"
}
```

## Response Fields

| Field            | Type            | Description                            |
| ---------------- | --------------- | -------------------------------------- |
| user_id          | integer         | ID user                                |
| nip              | string          | Nomor Induk Pegawai                    |
| nama_lengkap     | string          | Nama lengkap user                      |
| email            | string          | Email user                             |
| role             | string          | Role user (admin, kepala_dinas, pic)   |
| dinas_id         | integer \| null | ID dinas (null jika tidak ada dinas)   |
| dinas_nama       | string \| null  | Nama dinas (null jika tidak ada dinas) |
| wallet_id        | integer         | ID wallet                              |
| saldo            | float           | Saldo wallet dalam Rupiah              |
| wallet_type_id   | integer         | ID tipe wallet                         |
| wallet_type_nama | string \| null  | Nama tipe wallet (contoh: "Bensin")    |

## Use Cases

### 1. Cek Saldo User Tertentu

Digunakan oleh admin atau kepala dinas untuk melihat saldo wallet user tertentu.

### 2. Self Check Balance

User dapat mengecek saldo mereka sendiri (gunakan user_id dari token).

### 3. Verifikasi Sebelum Submission

Cek apakah user memiliki saldo cukup sebelum membuat submission baru.

### 4. Monitoring Dinas

Kepala dinas dapat memonitor saldo wallet staff di dinasnya.

## Examples

### Python Example using requests

```python
import requests

# Get user balance
url = "http://localhost:8000/users/balance/1"
headers = {
    "Authorization": "Bearer your_jwt_token_here"
}

response = requests.get(url, headers=headers)
print(response.json())

# Output:
# {
#   "success": true,
#   "data": {
#     "user_id": 1,
#     "nip": "123456789012345678",
#     "nama_lengkap": "John Doe",
#     "email": "john.doe@example.com",
#     "role": "pic",
#     "dinas_id": 5,
#     "dinas_nama": "Dinas Kesehatan",
#     "wallet_id": 10,
#     "saldo": 5000000.00,
#     "wallet_type_id": 1,
#     "wallet_type_nama": "Bensin"
#   },
#   "message": "Berhasil mendapatkan saldo user"
# }
```

### cURL Example

```bash
# Get user balance
curl -X GET "http://localhost:8000/users/balance/1" \
  -H "Authorization: Bearer your_jwt_token_here"
```

### JavaScript/Fetch Example

```javascript
// Get user balance
async function getUserBalance(userId) {
	const response = await fetch(
		`http://localhost:8000/users/balance/${userId}`,
		{
			method: "GET",
			headers: {
				Authorization: "Bearer your_jwt_token_here",
				"Content-Type": "application/json"
			}
		}
	);

	const data = await response.json();
	console.log(data);

	// Display balance
	if (data.success) {
		console.log(
			`Saldo ${data.data.nama_lengkap}: Rp ${data.data.saldo.toLocaleString(
				"id-ID"
			)}`
		);
		console.log(`Dinas: ${data.data.dinas_nama || "Tidak ada dinas"}`);
		console.log(`Tipe Wallet: ${data.data.wallet_type_nama}`);
	}
}

getUserBalance(1);
```

## Business Logic

### Saldo Format

- Saldo disimpan dalam database sebagai `Numeric(15,2)` (15 digit total, 2 desimal)
- Dikembalikan sebagai `float` dalam response
- Maksimal: 9,999,999,999,999.99

### Wallet Type

- Setiap wallet terkait dengan satu tipe wallet (contoh: "Bensin", "Non-Bensin")
- Tipe wallet menentukan jenis dana yang tersedia di wallet

### Dinas Association

- User bisa memiliki dinas atau tidak (dinas_id nullable)
- Jika tidak ada dinas, dinas_nama akan null

## Error Handling

### Common Errors

1. **User tidak ditemukan** (404)

   - User ID tidak ada di database
   - Solution: Verifikasi user_id yang valid

2. **Wallet tidak ditemukan** (404)

   - User belum memiliki wallet
   - Solution: Buat wallet untuk user terlebih dahulu

3. **Token tidak valid** (401)
   - JWT token expired atau invalid
   - Solution: Login ulang untuk mendapatkan token baru

## Performance Considerations

### Database Queries

Endpoint ini melakukan 4 query:

1. Get user by ID
2. Get wallet by UserID
3. Get wallet type by WalletTypeID
4. Get dinas by DinasID (jika ada)

### Optimization Tips

- Consider caching wallet balance untuk high-traffic scenarios
- Join queries bisa di-optimize dengan eager loading
- Index pada UserID di tabel Wallet untuk faster lookup

## Security

### Authorization

- Endpoint memerlukan JWT authentication
- Consider role-based access:
  - Admin: dapat melihat saldo semua user
  - Kepala Dinas: dapat melihat saldo user di dinasnya
  - PIC: hanya dapat melihat saldo sendiri

### Recommendation

Tambahkan business logic di endpoint untuk membatasi akses:

```python
# Contoh implementasi authorization
if _current_user.Role == RoleEnum.pic and _current_user.ID != user_id:
    raise HTTPException(403, "Anda hanya dapat melihat saldo sendiri")
```

## Related Endpoints

- `GET /users/{user_id}` - Get user detail (tanpa saldo)
- `GET /users/detailed/search` - Search users dengan saldo
- `GET /wallet/` - Get all wallets (admin only)
- `POST /submission/` - Create submission (memotong saldo)

## Testing

### Test Cases

1. ✅ Get balance dengan user_id valid
2. ✅ Get balance dengan user_id tidak ada
3. ✅ Get balance untuk user tanpa wallet
4. ✅ Get balance untuk user tanpa dinas
5. ✅ Get balance tanpa authentication token
6. ✅ Get balance dengan token expired

### Sample Test (pytest)

```python
def test_get_user_balance_success(client, auth_headers):
    """Test get user balance successfully"""
    response = client.get("/users/balance/1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "saldo" in data["data"]
    assert data["data"]["user_id"] == 1

def test_get_user_balance_not_found(client, auth_headers):
    """Test get user balance with invalid user_id"""
    response = client.get("/users/balance/9999", headers=auth_headers)
    assert response.status_code == 404
    assert "tidak ditemukan" in response.json()["detail"]
```

## Changelog

### Version 1.0.0 (2025-11-03)

- ✅ Initial release
- ✅ Get user balance endpoint
- ✅ Include user, dinas, and wallet type information
- ✅ JWT authentication required
- ✅ Error handling untuk user/wallet not found
