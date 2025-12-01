from __future__ import annotations
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract, func
from fastapi import HTTPException, UploadFile
import model.models as models
from model.models import Report as ReportModel, ReportLog as ReportLogModel, ReportStatusEnum
from schemas.schemas import ReportCreate
from utils.file_upload import save_report_photo

class ReportService:
    @staticmethod
    def _get_base_query(db: Session):
        """
        Query dasar dengan Eager Loading lengkap.
        Menambahkan: Dinas
        """
        return db.query(ReportModel).options(
            joinedload(ReportModel.user),
            joinedload(ReportModel.dinas), # [NEW] Load Dinas
            joinedload(ReportModel.vehicle).joinedload(models.Vehicle.vehicle_type),
            joinedload(ReportModel.logs).joinedload(ReportLogModel.updater)
        )

    @staticmethod
    def list(
        db: Session, 
        user_id: int | None = None, 
        vehicle_id: int | None = None,
        month: int | None = None,
        year: int | None = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        q = ReportService._get_base_query(db)

        # Filters
        if user_id: q = q.filter(ReportModel.UserID == user_id)
        if vehicle_id: q = q.filter(ReportModel.VehicleID == vehicle_id)
        if month: q = q.filter(extract('month', ReportModel.Timestamp) == month)
        if year: q = q.filter(extract('year', ReportModel.Timestamp) == year)

        q = q.order_by(ReportModel.Timestamp.desc())
        
        # Pagination Data
        data = q.offset(offset).limit(limit).all()

        # Count Total (Optimized query reuse)
        count_q = db.query(func.count(ReportModel.ID))
        if user_id: count_q = count_q.filter(ReportModel.UserID == user_id)
        if vehicle_id: count_q = count_q.filter(ReportModel.VehicleID == vehicle_id)
        if month: count_q = count_q.filter(extract('month', ReportModel.Timestamp) == month)
        if year: count_q = count_q.filter(extract('year', ReportModel.Timestamp) == year)
        
        total_records = count_q.scalar() or 0
        has_more = (offset + len(data)) < total_records

        # Statistics
        stat_q = db.query(ReportModel.Status, func.count(ReportModel.ID))
        if user_id: stat_q = stat_q.filter(ReportModel.UserID == user_id)
        if vehicle_id: stat_q = stat_q.filter(ReportModel.VehicleID == vehicle_id)
        if month: stat_q = stat_q.filter(extract('month', ReportModel.Timestamp) == month)
        if year: stat_q = stat_q.filter(extract('year', ReportModel.Timestamp) == year)
        
        stats_result = stat_q.group_by(ReportModel.Status).all()
        
        stat_dict = {"total_data": total_records}
        for s in ReportStatusEnum:
            stat_dict[f"total_{s.value.lower()}"] = 0
        
        for status_enum, count in stats_result:
            key = f"total_{status_enum.value.lower()}"
            stat_dict[key] = count

        return {
            "list": data,
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
            "month": month,
            "year": year,
            "stat": stat_dict
        }
    @staticmethod
    def get_my_reports(db: Session, user_id: int, vehicle_id: int | None = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Versi Optimized: Menggunakan JOIN ke Submission untuk menghindari N+1 Query.
        """
        # Kita select ReportModel (full object) DAN kolom spesifik dari Submission
        q = db.query(
            ReportModel, 
            SubmissionModel.Status.label("sub_status"),
            SubmissionModel.TotalCashAdvance.label("sub_total")
        ).outerjoin(
            SubmissionModel, SubmissionModel.KodeUnik == ReportModel.KodeUnik
        ).options(
            # Eager load relasi Report agar tidak lazy load saat di-loop
            joinedload(ReportModel.user),
            joinedload(ReportModel.dinas),
            joinedload(ReportModel.vehicle).joinedload(models.Vehicle.vehicle_type),
            joinedload(ReportModel.logs)
        )

        # Filters
        q = q.filter(ReportModel.UserID == user_id)
        if vehicle_id:
            q = q.filter(ReportModel.VehicleID == vehicle_id)
        
        # Pagination Stats
        total_records = q.count() # Count query (bisa dioptimalkan lagi tapi ini sudah lebih baik)
        
        # Fetch Data
        q = q.order_by(ReportModel.Timestamp.desc())
        raw_results = q.offset(offset).limit(limit).all()
        
        # Construct Response
        # Kita harus menggabungkan object ReportModel dengan data tambahan dari Submission
        result_list = []
        for report, sub_status, sub_total in raw_results:
            # Karena kita pakai Pydantic from_attributes=True, kita bisa passing object SQLAlchemy
            # Namun untuk field tambahan (SubmissionStatus), kita perlu set secara manual 
            # atau bungkus ke dict jika model Pydantic mendukungnya.
            
            # Cara paling aman: Convert model ke dict, lalu update field tambahan
            # Note: Ini sedikit expensive dibanding passing object, tapi aman.
            # Alternatif: Buat wrapper class sementara.
            
            # Kita gunakan pendekatan attribute setting sementara pada instance (hacky but fast)
            # atau mapping manual field-field penting.
            
            # Pendekatan Mapping Manual (Explicit is better than implicit bugs)
            vehicle_obj = report.vehicle
            vehicle_type_name = vehicle_obj.vehicle_type.Nama if vehicle_obj and vehicle_obj.vehicle_type else None
            
            item = {
                # Fields from ReportModel
                "ID": report.ID,
                "KodeUnik": report.KodeUnik,
                "User": report.user, # Pydantic akan handle nested serialization
                "Vehicle": report.vehicle, # Pydantic akan handle nested serialization
                "Dinas": report.dinas,
                "AmountRupiah": report.AmountRupiah,
                "AmountLiter": report.AmountLiter,
                "Description": report.Description,
                "Status": report.Status,
                "Timestamp": report.Timestamp,
                "Latitude": report.Latitude,
                "Longitude": report.Longitude,
                "Odometer": report.Odometer,
                "VehiclePhysicalPhotoPath": report.VehiclePhysicalPhotoPath,
                "OdometerPhotoPath": report.OdometerPhotoPath,
                "InvoicePhotoPath": report.InvoicePhotoPath,
                "MyPertaminaPhotoPath": report.MyPertaminaPhotoPath,
                "Logs": report.logs,
                
                # Fields from Join
                "SubmissionStatus": sub_status.value if sub_status else None,
                "SubmissionTotal": float(sub_total) if sub_total else None
            }
            result_list.append(item)

        has_more = (offset + len(result_list)) < total_records
        
        return {
            "list": result_list,
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
            "month": None,
            "year": None,
            "stat": {"total_data": total_records}
        }

    @staticmethod
    def get(db: Session, report_id: int) -> Optional[ReportModel]:
        return ReportService._get_base_query(db).filter(ReportModel.ID == report_id).first()

    @staticmethod
    def _create_report_log(db, report_id, status, user_id, notes):
        log = ReportLogModel(ReportID=report_id, Status=status, UpdatedByUserID=user_id, Notes=notes)
        db.add(log)

    @staticmethod
    def create(db: Session, payload: ReportCreate) -> ReportModel:
        # [UPDATED] Validasi & Auto-assign DinasID
        user = db.query(models.User).filter(models.User.ID == payload.UserID).first()
        if not user: raise HTTPException(400, "UserID tidak ditemukan")
        
        if not db.query(models.Vehicle).filter(models.Vehicle.ID == payload.VehicleID).first():
            raise HTTPException(400, "VehicleID tidak ditemukan")
        
        status = ReportStatusEnum[payload.Status.value] if payload.Status else ReportStatusEnum.Pending
        
        report = ReportModel(
            KodeUnik=payload.KodeUnik, UserID=payload.UserID, VehicleID=payload.VehicleID,
            AmountRupiah=payload.AmountRupiah, AmountLiter=payload.AmountLiter, Description=payload.Description,
            Status=status, Latitude=payload.Latitude, Longitude=payload.Longitude,
            VehiclePhysicalPhotoPath=payload.VehiclePhysicalPhotoPath, OdometerPhotoPath=payload.OdometerPhotoPath,
            InvoicePhotoPath=payload.InvoicePhotoPath, MyPertaminaPhotoPath=payload.MyPertaminaPhotoPath,
            Odometer=payload.Odometer, 
            DinasID=user.DinasID # [NEW] Simpan DinasID
        )
        db.add(report)
        db.flush()
        ReportService._create_report_log(db, report.ID, status, payload.UserID, "Report dibuat")
        db.commit()
        return ReportService.get(db, report.ID) # type: ignore

    @staticmethod
    async def create_with_upload(
        db: Session, kode_unik: str, user_id: int, vehicle_id: int, amount_rupiah: float, amount_liter: float,
        description: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None,
        odometer: Optional[int] = None, vehicle_photo: Optional[UploadFile] = None,
        odometer_photo: Optional[UploadFile] = None, invoice_photo: Optional[UploadFile] = None,
        mypertamina_photo: Optional[UploadFile] = None
    ) -> ReportModel:
        # [UPDATED] Validasi & Auto-assign DinasID
        user = db.query(models.User).filter(models.User.ID == user_id).first()
        if not user: raise HTTPException(400, "UserID tidak ditemukan")
        
        if not db.query(models.Vehicle).filter(models.Vehicle.ID == vehicle_id).first():
            raise HTTPException(400, "VehicleID tidak ditemukan")
        
        v_path = await save_report_photo(vehicle_photo, "vehicle")
        o_path = await save_report_photo(odometer_photo, "odometer")
        i_path = await save_report_photo(invoice_photo, "invoice")
        m_path = await save_report_photo(mypertamina_photo, "mypertamina")
        
        try:
            report = ReportModel(
                KodeUnik=kode_unik, UserID=user_id, VehicleID=vehicle_id, AmountRupiah=amount_rupiah,
                AmountLiter=amount_liter, Description=description, Status=ReportStatusEnum.Pending,
                Latitude=latitude, Longitude=longitude, Odometer=odometer,
                VehiclePhysicalPhotoPath=v_path, OdometerPhotoPath=o_path,
                InvoicePhotoPath=i_path, MyPertaminaPhotoPath=m_path,
                DinasID=user.DinasID # [NEW] Simpan DinasID
            )
            db.add(report)
            db.flush()
            ReportService._create_report_log(db, report.ID, ReportStatusEnum.Pending, user_id, "Report dengan foto")
            db.commit()
            return ReportService.get(db, report.ID) # type: ignore
        except Exception as e:
            db.rollback()
            raise HTTPException(500, f"Failed: {str(e)}")

    # ... (update_status, delete tetap sama) ...
    @staticmethod
    def update_status(db: Session, report_id: int, new_status: ReportStatusEnum, updated_by_user_id: int, notes: str | None) -> ReportModel:
        r = db.query(ReportModel).filter(ReportModel.ID == report_id).first()
        if not r: raise HTTPException(404, "Report not found")
        setattr(r, "Status", new_status)
        ReportService._create_report_log(db, r.ID, new_status, updated_by_user_id, notes)
        db.commit()
        return ReportService.get(db, r.ID) # type: ignore

    @staticmethod
    def delete(db: Session, report_id: int) -> None:
        r = db.query(ReportModel).filter(ReportModel.ID == report_id).first()
        if not r: raise HTTPException(404, "Not found")
        db.delete(r)
        db.commit()