# Quick Reference: Report Status API

## API Endpoints

### 1. Update Report Status

```http
PUT /report/{report_id}/status
Authorization: Bearer {token}
Content-Type: application/json

{
  "Status": "Accepted",
  "Notes": "Optional notes"
}
```

**Status Values:**

- `Pending` - Default status
- `Reviewed` - Under review
- `Accepted` - Approved
- `Rejected` - Declined

**Response:**

```json
{
  "success": true,
  "data": {
    "ID": 1,
    "Status": "Accepted",
    ...
  },
  "message": "Status report berhasil diubah menjadi Accepted"
}
```

---

### 2. Get Report History Logs

```http
GET /report/{report_id}/logs
Authorization: Bearer {token}
```

**Response:**

```json
{
	"success": true,
	"data": [
		{
			"ID": 1,
			"ReportID": 1,
			"Status": "Pending",
			"Timestamp": "2024-11-29T08:00:00Z",
			"UpdatedByUserID": 5,
			"UpdatedByUserName": "Ahmad Fauzi",
			"Notes": "Report dibuat"
		},
		{
			"ID": 2,
			"ReportID": 1,
			"Status": "Accepted",
			"Timestamp": "2024-11-29T10:00:00Z",
			"UpdatedByUserID": 1,
			"UpdatedByUserName": "Admin",
			"Notes": "Approved"
		}
	]
}
```

---

### 3. Get Report Detail (with logs)

```http
GET /report/my/reports/{report_id}
Authorization: Bearer {token}
```

**Response includes:**

- Report details
- Vehicle info
- Submission info
- **NEW:** `Status` field
- **NEW:** `Logs` array

---

### 4. Get My Reports (with status)

```http
GET /report/my/reports?vehicle_id=1&limit=10&offset=0
Authorization: Bearer {token}
```

**Response includes:**

- **NEW:** `Status` field for each report

---

## Database Schema

### Report Table

```sql
ALTER TABLE Report
ADD COLUMN Status VARCHAR(50) NOT NULL DEFAULT 'Pending';
```

### ReportLog Table

```sql
CREATE TABLE ReportLog (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    ReportID INT NOT NULL,
    Status VARCHAR(50) NOT NULL,
    Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedByUserID INT NULL,
    Notes TEXT NULL,
    FOREIGN KEY (ReportID) REFERENCES Report(ID) ON DELETE CASCADE,
    FOREIGN KEY (UpdatedByUserID) REFERENCES User(ID) ON DELETE SET NULL
);
```

---

## Python Usage Examples

### Update Status

```python
import requests

response = requests.put(
    f"{API_URL}/report/{report_id}/status",
    json={
        "Status": "Accepted",
        "Notes": "Approved by admin"
    },
    headers={"Authorization": f"Bearer {token}"}
)
```

### Get Logs

```python
response = requests.get(
    f"{API_URL}/report/{report_id}/logs",
    headers={"Authorization": f"Bearer {token}"}
)
logs = response.json()["data"]
```

---

## JavaScript Usage Examples

### Update Status

```javascript
const response = await fetch(`${API_URL}/report/${reportId}/status`, {
	method: "PUT",
	headers: {
		"Content-Type": "application/json",
		Authorization: `Bearer ${token}`
	},
	body: JSON.stringify({
		Status: "Accepted",
		Notes: "Approved by admin"
	})
});
```

### Get Logs

```javascript
const response = await fetch(`${API_URL}/report/${reportId}/logs`, {
	headers: {
		Authorization: `Bearer ${token}`
	}
});
const logs = await response.json();
```

---

## Status Flow

```
Pending → Reviewed → Accepted
                   → Rejected
```

---

## Migration Command

```bash
mysql -u username -p database_name < migration_report_status_and_logs.sql
```

---

**Last Updated:** November 29, 2025
