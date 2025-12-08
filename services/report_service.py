from __future__ import annotations
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract, func
from fastapi import HTTPException, UploadFile
import model.models as models
from schemas.schemas import ReportCreate
from utils.file_upload import save_report_photo

class ReportService:
    @staticmethod
    def _get_base_query(db: Session):
        return db.query(models.Report).options(
            joinedload(models.Report.user),
            joinedload(models.Report.dinas),
            joinedload(models.Report.vehicle).joinedload(models.Vehicle.vehicle_type),
            joinedload(models.Report.logs).joinedload(models.ReportLog.updater)
        )

    @staticmethod
    def list(
        db: Session, 
        user_id: int | None = None, 
        vehicle_id: int | None = None,
        month: int | None = None,
        year: int | None = None,
        dinas_id: int | None = None,
        limit: int = 10,
        offset: int = 0,
        current_user: models.User | None = None,
        status: str | None = None
    ) -> Dict[str, Any]:
        q = ReportService._get_base_query(db)

        if user_id: q = q.filter(models.Report.user_id == user_id)
        if vehicle_id: q = q.filter(models.Report.vehicle_id == vehicle_id)
        if month: q = q.filter(extract('month', models.Report.timestamp) == month)
        if year: q = q.filter(extract('year', models.Report.timestamp) == year)
        if dinas_id: q = q.filter(models.Report.dinas_id == dinas_id)
        if status: q = q.filter(models.Report.status == status)

        q = q.order_by(models.Report.timestamp.desc()).filter(models.Report.dinas_id == current_user.dinas_id)
        data = q.offset(offset).limit(limit).all()

        count_q = db.query(func.count(models.Report.id))
        if user_id: count_q = count_q.filter(models.Report.user_id == user_id)
        if vehicle_id: count_q = count_q.filter(models.Report.vehicle_id == vehicle_id)
        if month: count_q = count_q.filter(extract('month', models.Report.timestamp) == month)
        if year: count_q = count_q.filter(extract('year', models.Report.timestamp) == year)
        if dinas_id: count_q = count_q.filter(models.Report.dinas_id == dinas_id)
        if status: count_q = count_q.filter(models.Report.status == status)
        
        total_records = count_q.scalar() or 0
        has_more = (offset + len(data)) < total_records

        stat_q = db.query(models.Report.status, func.count(models.Report.id)).filter(models.Report.dinas_id == current_user.dinas_id)
        if user_id: stat_q = stat_q.filter(models.Report.user_id == user_id)
        if vehicle_id: stat_q = stat_q.filter(models.Report.vehicle_id == vehicle_id)
        if month: stat_q = stat_q.filter(extract('month', models.Report.timestamp) == month)
        if year: stat_q = stat_q.filter(extract('year', models.Report.timestamp) == year)
        if dinas_id: stat_q = stat_q.filter(models.Report.dinas_id == dinas_id)
        if status: stat_q = stat_q.filter(models.Report.status == status)
        
        stats_result = stat_q.group_by(models.Report.status).all()
        
        stat_dict = {"total_data": total_records}
        for s in models.ReportStatusEnum:
            stat_dict[f"total_{s.value.lower()}"] = 0
        
        for status_enum, count in stats_result:
            key = f"total_{status_enum.value.lower()}"
            stat_dict[key] = count

        stat_dict["total_amounted"] = db.query(func.coalesce(func.sum(models.Report.amount_rupiah), 0.0)).filter(
            True if not user_id else models.Report.user_id == user_id,
            True if not vehicle_id else models.Report.vehicle_id == vehicle_id,
            True if not month else extract('month', models.Report.timestamp) == month,
            True if not year else extract('year', models.Report.timestamp) == year,
            True if not dinas_id else models.Report.dinas_id == dinas_id,
            True if not status else models.Report.status == status,
            models.Report.status == models.ReportStatusEnum.accepted
        ).scalar() or 0.0

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
    def get_my_reports(
        db: Session, 
        user_id: int, 
        vehicle_id: int | None = None,
        month: int | None = None,
        year: int | None = None,
        limit: int = 100, 
        offset: int = 0
    ) -> Dict[str, Any]:
        
        q = db.query(
            models.Report, 
            models.Submission.status.label("sub_status"),
            models.Submission.total_cash_advance.label("sub_total")
        ).outerjoin(
            models.Submission, models.Submission.kode_unik == models.Report.kode_unik
        ).options(
            joinedload(models.Report.user),
            joinedload(models.Report.dinas),
            joinedload(models.Report.vehicle).joinedload(models.Vehicle.vehicle_type),
            joinedload(models.Report.logs)
        )

        q = q.filter(models.Report.user_id == user_id)
        if vehicle_id:
            q = q.filter(models.Report.vehicle_id == vehicle_id)
        
        if month: q = q.filter(extract('month', models.Report.timestamp) == month)
        if year: q = q.filter(extract('year', models.Report.timestamp) == year)
        
        total_records = q.count()
        total_amounted = q.filter(models.Report.status == models.ReportStatusEnum.accepted).with_entities(func.coalesce(func.sum(models.Report.amount_rupiah), 0.0)).scalar() or 0.0
        total_accepted = q.filter(models.Report.status == models.ReportStatusEnum.accepted).count() or 0
        total_pending = q.filter(models.Report.status == models.ReportStatusEnum.pending).count() or 0
        total_rejected = q.filter(models.Report.status == models.ReportStatusEnum.rejected).count() or 0

        
        q = q.order_by(models.Report.timestamp.desc())
        raw_results = q.offset(offset).limit(limit).all()
        
        result_list = []
        for report, sub_status, sub_total in raw_results:
            item = {
                "id": report.id,
                "kode_unik": report.kode_unik,
                "user": report.user, 
                "vehicle": report.vehicle, 
                "dinas": report.dinas,
                "amount_rupiah": report.amount_rupiah,
                "amount_liter": report.amount_liter,
                "description": report.description,
                "status": report.status,
                "timestamp": report.timestamp,
                "latitude": report.latitude,
                "longitude": report.longitude,
                "odometer": report.odometer,
                "vehicle_physical_photo_path": report.vehicle_physical_photo_path,
                "odometer_photo_path": report.odometer_photo_path,
                "invoice_photo_path": report.invoice_photo_path,
                "my_pertamina_photo_path": report.my_pertamina_photo_path,
                "logs": report.logs,
                "submission_status": sub_status.value if sub_status else None,
                "submission_total": float(sub_total) if sub_total else None
            }
            result_list.append(item)

        has_more = (offset + len(result_list)) < total_records
        
        return {
            "list": result_list,
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
            "month": month,
            "year": year,
            "stat": {"total_data": total_records, "total_accepted": total_accepted, "total_pending": total_pending, "total_rejected": total_rejected, "total_amounted": total_amounted}
        }

    @staticmethod
    def get(db: Session, report_id: int) -> Optional[models.Report]:
        return ReportService._get_base_query(db).filter(models.Report.id == report_id).first()

    @staticmethod
    def _create_report_log(db, report_id, status, user_id, notes):
        log = models.ReportLog(report_id=report_id, status=status, updated_by_user_id=user_id, notes=notes)
        db.add(log)

    @staticmethod
    def create(db: Session, payload: ReportCreate) -> models.Report:
        user = db.query(models.User).filter(models.User.id == payload.user_id).first()
        if not user: raise HTTPException(400, "UserID tidak ditemukan")
        
        if not db.query(models.Vehicle).filter(models.Vehicle.id == payload.vehicle_id).first():
            raise HTTPException(400, "VehicleID tidak ditemukan")
        
        status = models.ReportStatusEnum[payload.status.value] if payload.status else models.ReportStatusEnum.pending
        
        report = models.Report(
            kode_unik=payload.kode_unik, 
            user_id=payload.user_id, 
            vehicle_id=payload.vehicle_id,
            amount_rupiah=payload.amount_rupiah, 
            amount_liter=payload.amount_liter, 
            description=payload.description,
            status=status, 
            latitude=payload.latitude, 
            longitude=payload.longitude,
            vehicle_physical_photo_path=payload.vehicle_physical_photo_path, 
            odometer_photo_path=payload.odometer_photo_path,
            invoice_photo_path=payload.invoice_photo_path, 
            my_pertamina_photo_path=payload.my_pertamina_photo_path,
            odometer=payload.odometer, 
            dinas_id=user.dinas_id 
        )
        db.add(report)
        db.flush()
        ReportService._create_report_log(db, report.id, status, payload.user_id, "Report dibuat")
        db.commit()
        return ReportService.get(db, report.id) # type: ignore

    @staticmethod
    async def create_with_upload(
        db: Session, kode_unik: str, user_id: int, vehicle_id: int, amount_rupiah: float, amount_liter: float,
        description: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None,
        odometer: Optional[int] = None, vehicle_photo: Optional[UploadFile] = None,
        odometer_photo: Optional[UploadFile] = None, invoice_photo: Optional[UploadFile] = None,
        mypertamina_photo: Optional[UploadFile] = None
    ) -> models.Report:
        
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user: raise HTTPException(400, "UserID tidak ditemukan")
        
        if not db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first():
            raise HTTPException(400, "VehicleID tidak ditemukan")
        
        v_path = await save_report_photo(vehicle_photo, "vehicle")
        o_path = await save_report_photo(odometer_photo, "odometer")
        i_path = await save_report_photo(invoice_photo, "invoice")
        m_path = await save_report_photo(mypertamina_photo, "mypertamina")
        
        try:
            report = models.Report(
                kode_unik=kode_unik, user_id=user_id, vehicle_id=vehicle_id, amount_rupiah=amount_rupiah,
                amount_liter=amount_liter, description=description, status=models.ReportStatusEnum.pending,
                latitude=latitude, longitude=longitude, odometer=odometer,
                vehicle_physical_photo_path=v_path, odometer_photo_path=o_path,
                invoice_photo_path=i_path, my_pertamina_photo_path=m_path,
                dinas_id=user.dinas_id
            )
            db.add(report)
            db.flush()
            ReportService._create_report_log(db, report.id, models.ReportStatusEnum.pending, user_id, "Report dengan foto")
            db.commit()
            return ReportService.get(db, report.id) # type: ignore
        except Exception as e:
            db.rollback()
            raise HTTPException(500, f"Failed: {str(e)}")

    @staticmethod
    async def update_with_upload(
        db: Session, 
        report_id: int,
        kode_unik: Optional[str] = None,
        user_id: Optional[int] = None, 
        vehicle_id: Optional[int] = None, 
        amount_rupiah: Optional[float] = None, 
        amount_liter: Optional[float] = None,
        description: Optional[str] = None, 
        latitude: Optional[float] = None, 
        longitude: Optional[float] = None,
        odometer: Optional[int] = None, 
        vehicle_photo: Optional[UploadFile] = None,
        odometer_photo: Optional[UploadFile] = None, 
        invoice_photo: Optional[UploadFile] = None,
        mypertamina_photo: Optional[UploadFile] = None
    ) -> models.Report:
        
        report = db.query(models.Report).filter(models.Report.id == report_id).first()
        if not report:
            raise HTTPException(404, "Report tidak ditemukan")
        
        # Upload foto baru jika ada
        if vehicle_photo and vehicle_photo.filename:
            report.vehicle_physical_photo_path = await save_report_photo(vehicle_photo, "vehicle")
        if odometer_photo and odometer_photo.filename:
            report.odometer_photo_path = await save_report_photo(odometer_photo, "odometer")
        if invoice_photo and invoice_photo.filename:
            report.invoice_photo_path = await save_report_photo(invoice_photo, "invoice")
        if mypertamina_photo and mypertamina_photo.filename:
            report.my_pertamina_photo_path = await save_report_photo(mypertamina_photo, "mypertamina")
        
        # Update field lainnya jika ada nilai
        if kode_unik is not None:
            report.kode_unik = kode_unik
        if user_id is not None:
            report.user_id = user_id
        if vehicle_id is not None:
            report.vehicle_id = vehicle_id
        if amount_rupiah is not None:
            report.amount_rupiah = amount_rupiah
        if amount_liter is not None:
            report.amount_liter = amount_liter
        if description is not None:
            report.description = description
        if latitude is not None:
            report.latitude = latitude
        if longitude is not None:
            report.longitude = longitude
        if odometer is not None:
            report.odometer = odometer
        
        db.commit()
        return ReportService.get(db, report.id)  # type: ignore

    @staticmethod
    def update_status(db: Session, report_id: int, new_status: str, updated_by_user_id: int, notes: str | None) -> models.Report:
        r = db.query(models.Report).filter(models.Report.id == report_id).first()
        if not r: raise HTTPException(404, "Report not found")
        # Convert string to enum
        status_enum = models.ReportStatusEnum(new_status)
        r.status = status_enum
        ReportService._create_report_log(db, r.id, status_enum, updated_by_user_id, notes)
        db.commit()
        return ReportService.get(db, r.id) # type: ignore

    @staticmethod
    def delete(db: Session, report_id: int) -> None:
        r = db.query(models.Report).filter(models.Report.id == report_id).first()
        if not r: raise HTTPException(404, "Not found")
        db.delete(r)
        db.commit()
        
    @staticmethod
    def get_report_logs(db: Session, report_id: int):
        return db.query(models.ReportLog).filter(models.ReportLog.report_id == report_id).order_by(models.ReportLog.timestamp.desc()).all()