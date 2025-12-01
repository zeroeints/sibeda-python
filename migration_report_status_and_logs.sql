-- Migration: Add Status field to Report table and create ReportLog table
-- Date: 2025-11-29
-- Description: Menambahkan field Status pada Report untuk tracking status,
--              dan membuat tabel ReportLog untuk history tracking perubahan status

-- 1. Add Status column to Report table
ALTER TABLE Report 
ADD COLUMN Status VARCHAR
(50) NOT NULL DEFAULT 'Pending';

-- 2. Create ReportLog table for history tracking
CREATE TABLE ReportLog
(
    ID INT
    AUTO_INCREMENT PRIMARY KEY,
    ReportID INT NOT NULL,
    Status VARCHAR
    (50) NOT NULL,
    Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UpdatedByUserID INT NULL,
    Notes TEXT NULL,
    FOREIGN KEY
    (ReportID) REFERENCES Report
    (ID) ON
    DELETE CASCADE,
    FOREIGN KEY (UpdatedByUserID)
    REFERENCES User
    (ID) ON
    DELETE
    SET NULL
    );

    -- 3. Create index on ReportID for faster queries
    CREATE INDEX idx_reportlog_reportid ON ReportLog(ReportID);

    -- 4. Create index on Timestamp for sorting
    CREATE INDEX idx_reportlog_timestamp ON ReportLog(Timestamp);

    -- 5. Populate initial log entries for existing reports (optional - untuk backward compatibility)
    INSERT INTO ReportLog
        (ReportID, Status, Timestamp, UpdatedByUserID, Notes)
    SELECT
        ID as ReportID,
        'Pending' as Status,
        Timestamp,
        UserID as UpdatedByUserID,
        'Initial entry - migrated from existing report' as Notes
    FROM Report;

-- Notes:
-- - Status enum values: Pending, Reviewed, Accepted, Rejected
-- - Setiap kali status Report diubah, akan otomatis dibuat entry di ReportLog
-- - UpdatedByUserID bisa NULL untuk log yang dibuat sistem
-- - Notes untuk menyimpan keterangan tambahan perubahan status
