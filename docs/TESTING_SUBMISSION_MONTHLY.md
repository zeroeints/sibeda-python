# Contoh Testing API Submission Monthly

## Testing dengan cURL

### 1. Login untuk mendapatkan token

```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "NIP": "123456789012345678",
    "Password": "password123"
  }'
```

Response:

```json
{
	"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
	"token_type": "bearer"
}
```

### 2. Get Monthly Summary

```bash
curl -X GET "http://127.0.0.1:8000/submission/monthly/summary?month=11&year=2025" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 3. Get Monthly Details

```bash
curl -X GET "http://127.0.0.1:8000/submission/monthly/details?month=11&year=2025" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. Get Complete Monthly Report

```bash
curl -X GET "http://127.0.0.1:8000/submission/monthly/report?month=11&year=2025" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Testing dengan Python

### Setup

```python
import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

# Login
def login(nip: str, password: str) -> str:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"NIP": nip, "Password": password}
    )
    response.raise_for_status()
    return response.json()["access_token"]

# Get headers with token
def get_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
```

### 1. Get Monthly Summary

```python
def get_monthly_summary(token: str, month: int, year: int):
    response = requests.get(
        f"{BASE_URL}/submission/monthly/summary",
        params={"month": month, "year": year},
        headers=get_headers(token)
    )
    response.raise_for_status()
    return response.json()

# Usage
token = login("123456789012345678", "password123")
summary = get_monthly_summary(token, 11, 2025)
print(f"Total submissions: {summary['data']['total_submissions']}")
print(f"Total cash advance: Rp {summary['data']['total_cash_advance']:,.2f}")
```

### 2. Get Monthly Details

```python
def get_monthly_details(token: str, month: int, year: int):
    response = requests.get(
        f"{BASE_URL}/submission/monthly/details",
        params={"month": month, "year": year},
        headers=get_headers(token)
    )
    response.raise_for_status()
    return response.json()

# Usage
token = login("123456789012345678", "password123")
details = get_monthly_details(token, 11, 2025)
for submission in details['data']:
    print(f"{submission['KodeUnik']}: {submission['CreatorName']} -> {submission['ReceiverName']}")
    print(f"  Amount: Rp {submission['TotalCashAdvance']:,.2f}")
    print(f"  Status: {submission['Status']}")
    print(f"  Vehicle: {submission['VehicleName']} ({submission['VehiclePlat']})")
    print()
```

### 3. Get Complete Monthly Report

```python
def get_monthly_report(token: str, month: int, year: int):
    response = requests.get(
        f"{BASE_URL}/submission/monthly/report",
        params={"month": month, "year": year},
        headers=get_headers(token)
    )
    response.raise_for_status()
    return response.json()

# Usage
token = login("123456789012345678", "password123")
report = get_monthly_report(token, 11, 2025)

# Print summary
summary = report['data']['summary']
print("=" * 50)
print(f"LAPORAN PENGAJUAN BULAN {summary['month']}/{summary['year']}")
print("=" * 50)
print(f"Total Pengajuan: {summary['total_submissions']}")
print(f"  - Pending  : {summary['total_pending']}")
print(f"  - Accepted : {summary['total_accepted']}")
print(f"  - Rejected : {summary['total_rejected']}")
print()
print(f"Total Dana: Rp {summary['total_cash_advance']:,.2f}")
print(f"  - Pending  : Rp {summary['total_cash_advance_pending']:,.2f}")
print(f"  - Accepted : Rp {summary['total_cash_advance_accepted']:,.2f}")
print(f"  - Rejected : Rp {summary['total_cash_advance_rejected']:,.2f}")
print("=" * 50)
print()

# Print details
print("DETAIL PENGAJUAN:")
print("-" * 50)
for idx, sub in enumerate(report['data']['details'], 1):
    print(f"{idx}. {sub['KodeUnik']}")
    print(f"   Pembuat : {sub['CreatorName']}")
    print(f"   Penerima: {sub['ReceiverName']}")
    print(f"   Kendaraan: {sub['VehicleName']} ({sub['VehiclePlat']})")
    print(f"   Dana    : Rp {sub['TotalCashAdvance']:,.2f}")
    print(f"   Status  : {sub['Status']}")
    print(f"   Tanggal : {sub['created_at']}")
    print()
```

---

## Testing dengan Postman

### 1. Setup Environment Variables

- `base_url`: `http://127.0.0.1:8000`
- `token`: (akan diisi setelah login)

### 2. Login Request

```
POST {{base_url}}/auth/login
Content-Type: application/json

{
  "NIP": "123456789012345678",
  "Password": "password123"
}
```

**Test Script:**

```javascript
pm.test("Status code is 200", function () {
	pm.response.to.have.status(200);
});

pm.test("Response has access_token", function () {
	var jsonData = pm.response.json();
	pm.expect(jsonData).to.have.property("access_token");
	pm.environment.set("token", jsonData.access_token);
});
```

### 3. Get Monthly Summary Request

```
GET {{base_url}}/submission/monthly/summary?month=11&year=2025
Authorization: Bearer {{token}}
```

**Test Script:**

```javascript
pm.test("Status code is 200", function () {
	pm.response.to.have.status(200);
});

pm.test("Response has summary data", function () {
	var jsonData = pm.response.json();
	pm.expect(jsonData.success).to.eql(true);
	pm.expect(jsonData.data).to.have.property("total_submissions");
	pm.expect(jsonData.data).to.have.property("total_cash_advance");
});
```

### 4. Get Monthly Details Request

```
GET {{base_url}}/submission/monthly/details?month=11&year=2025
Authorization: Bearer {{token}}
```

### 5. Get Monthly Report Request

```
GET {{base_url}}/submission/monthly/report?month=11&year=2025
Authorization: Bearer {{token}}
```

---

## Testing Edge Cases

### Invalid Month (should return 400)

```bash
curl -X GET "http://127.0.0.1:8000/submission/monthly/summary?month=13&year=2025" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Invalid Year (should return 400)

```bash
curl -X GET "http://127.0.0.1:8000/submission/monthly/summary?month=11&year=1999" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### No Data (should return empty list with zero counts)

```bash
curl -X GET "http://127.0.0.1:8000/submission/monthly/summary?month=1&year=2020" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected response:

```json
{
	"success": true,
	"data": {
		"month": 1,
		"year": 2020,
		"total_submissions": 0,
		"total_pending": 0,
		"total_accepted": 0,
		"total_rejected": 0,
		"total_cash_advance": 0.0,
		"total_cash_advance_accepted": 0.0,
		"total_cash_advance_rejected": 0.0,
		"total_cash_advance_pending": 0.0
	},
	"message": "Ringkasan pengajuan bulan 1/2020"
}
```

---

## Complete Python Test Script

```python
#!/usr/bin/env python3
"""
Test script untuk Submission Monthly API
"""
import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

class SubmissionAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = None

    def login(self, nip: str, password: str):
        """Login dan simpan token"""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"NIP": nip, "Password": password}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
        print("✓ Login successful")
        return self.token

    def _headers(self):
        """Get headers dengan authentication"""
        if not self.token:
            raise ValueError("Not logged in. Call login() first.")
        return {"Authorization": f"Bearer {self.token}"}

    def get_summary(self, month: int, year: int):
        """Get monthly summary"""
        response = requests.get(
            f"{self.base_url}/submission/monthly/summary",
            params={"month": month, "year": year},
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def get_details(self, month: int, year: int):
        """Get monthly details"""
        response = requests.get(
            f"{self.base_url}/submission/monthly/details",
            params={"month": month, "year": year},
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def get_report(self, month: int, year: int):
        """Get complete monthly report"""
        response = requests.get(
            f"{self.base_url}/submission/monthly/report",
            params={"month": month, "year": year},
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

def main():
    # Initialize API client
    api = SubmissionAPI(BASE_URL)

    # Login
    try:
        api.login("123456789012345678", "password123")
    except Exception as e:
        print(f"✗ Login failed: {e}")
        return

    # Get current month and year
    now = datetime.now()
    month, year = now.month, now.year

    # Test 1: Get Summary
    print(f"\n{'=' * 60}")
    print(f"Test 1: Get Monthly Summary ({month}/{year})")
    print('=' * 60)
    try:
        result = api.get_summary(month, year)
        summary = result['data']
        print(f"✓ Total Submissions: {summary['total_submissions']}")
        print(f"  - Pending : {summary['total_pending']}")
        print(f"  - Accepted: {summary['total_accepted']}")
        print(f"  - Rejected: {summary['total_rejected']}")
        print(f"✓ Total Cash Advance: Rp {summary['total_cash_advance']:,.2f}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 2: Get Details
    print(f"\n{'=' * 60}")
    print(f"Test 2: Get Monthly Details ({month}/{year})")
    print('=' * 60)
    try:
        result = api.get_details(month, year)
        details = result['data']
        print(f"✓ Found {len(details)} submissions")
        for idx, sub in enumerate(details[:5], 1):  # Show first 5
            print(f"\n{idx}. {sub['KodeUnik']}")
            print(f"   {sub['CreatorName']} → {sub['ReceiverName']}")
            print(f"   Rp {sub['TotalCashAdvance']:,.2f} - {sub['Status']}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 3: Get Complete Report
    print(f"\n{'=' * 60}")
    print(f"Test 3: Get Complete Monthly Report ({month}/{year})")
    print('=' * 60)
    try:
        result = api.get_report(month, year)
        print("✓ Report retrieved successfully")
        print(f"  Summary: {len(result['data']['summary'])} fields")
        print(f"  Details: {len(result['data']['details'])} submissions")
    except Exception as e:
        print(f"✗ Failed: {e}")

    print(f"\n{'=' * 60}")
    print("All tests completed!")
    print('=' * 60)

if __name__ == "__main__":
    main()
```

Save as `test_submission_monthly.py` dan jalankan:

```bash
python test_submission_monthly.py
```
