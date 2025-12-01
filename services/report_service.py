from __future__ import annotations
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
import model.models as models
from model.models import Report as ReportModel, ReportLog as ReportLogModel, ReportStatusEnum
from schemas.schemas import ReportCreate, ReportUpdate
from utils.file_upload import save_report_photo, delete_file

def _get_photo_url(file_path: Optional[str] | Any) -> Optional[str]:
    """Helper to convert file path to URL"""
    if not file_path:
        return None
    # Convert to string in case it's a SQLAlchemy column
    path_str = str(file_path) if file_path else None
    if not path_str or path_str == "None":
        return None
    return f"http://localhost:8000/{path_str.replace(chr(92), '/')}"

class ReportService:
    @staticmethod
    def _create_report_log(
        db: Session,
        report_id: int,
        status: ReportStatusEnum,
        updated_by_user_id: int | None = None,
        notes: str | None = None
    ) -> ReportLogModel:
        """Helper method to create a report log entry"""
        log = ReportLogModel(
            ReportID=report_id,
            Status=status,
            UpdatedByUserID=updated_by_user_id,
            Notes=notes
        )
        db.add(log)
        return log
    
    @staticmethod
    def list(db: Session, user_id: int | None = None, vehicle_id: int | None = None) -> List[ReportModel]:
        q = db.query(ReportModel)
        if user_id is not None:
            q = q.filter(ReportModel.UserID == user_id)
        if vehicle_id is not None:
            q = q.filter(ReportModel.VehicleID == vehicle_id)
        return q.order_by(ReportModel.ID.desc()).all()

    @staticmethod
    def get(db: Session, report_id: int) -> Optional[ReportModel]:
        return db.query(ReportModel).filter(ReportModel.ID == report_id).first()

    @staticmethod
    def create(db: Session, payload: ReportCreate) -> ReportModel:
        # basic FK validation
        if not db.query(models.User).filter(models.User.ID == payload.UserID).first():
            raise HTTPException(status_code=400, detail="UserID tidak ditemukan")
        if not db.query(models.Vehicle).filter(models.Vehicle.ID == payload.VehicleID).first():
            raise HTTPException(status_code=400, detail="VehicleID tidak ditemukan")
        
        # Set default status if not provided (convert from schema enum to model enum)
        if payload.Status:
            status = ReportStatusEnum[payload.Status.value]
        else:
            status = ReportStatusEnum.Pending
        
        report = ReportModel(
            KodeUnik=payload.KodeUnik,
            UserID=payload.UserID,
            VehicleID=payload.VehicleID,
            AmountRupiah=payload.AmountRupiah,
            AmountLiter=payload.AmountLiter,
            Description=payload.Description,
            Status=status,
            Latitude=payload.Latitude,
            Longitude=payload.Longitude,
            VehiclePhysicalPhotoPath=payload.VehiclePhysicalPhotoPath,
            OdometerPhotoPath=payload.OdometerPhotoPath,
            InvoicePhotoPath=payload.InvoicePhotoPath,
            MyPertaminaPhotoPath=payload.MyPertaminaPhotoPath,
            Odometer=payload.Odometer,
        )
        db.add(report)
        db.flush()  # Get the report ID
        
        # Create initial log entry
        ReportService._create_report_log(
            db=db,
            report_id=report.ID,  # type: ignore
            status=status,
            updated_by_user_id=payload.UserID,
            notes="Report dibuat"
        )
        
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    async def create_with_upload(
        db: Session,
        kode_unik: str,
        user_id: int,
        vehicle_id: int,
        amount_rupiah: float,
        amount_liter: float,
        description: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        odometer: Optional[int] = None,
        vehicle_photo: Optional[UploadFile] = None,
        odometer_photo: Optional[UploadFile] = None,
        invoice_photo: Optional[UploadFile] = None,
        mypertamina_photo: Optional[UploadFile] = None
    ) -> ReportModel:
        """
        Create report dengan upload foto
        """
        # Validate FK
        if not db.query(models.User).filter(models.User.ID == user_id).first():
            raise HTTPException(status_code=400, detail="UserID tidak ditemukan")
        if not db.query(models.Vehicle).filter(models.Vehicle.ID == vehicle_id).first():
            raise HTTPException(status_code=400, detail="VehicleID tidak ditemukan")
        
        # Upload photos
        vehicle_path = await save_report_photo(vehicle_photo, "vehicle")
        odometer_path = await save_report_photo(odometer_photo, "odometer")
        invoice_path = await save_report_photo(invoice_photo, "invoice")
        mypertamina_path = await save_report_photo(mypertamina_photo, "mypertamina")
        
        # Create report
        try:
            report = ReportModel(
                KodeUnik=kode_unik,
                UserID=user_id,
                VehicleID=vehicle_id,
                AmountRupiah=amount_rupiah,
                AmountLiter=amount_liter,
                Description=description,
                Status=ReportStatusEnum.Pending,
                Latitude=latitude,
                Longitude=longitude,
                VehiclePhysicalPhotoPath=vehicle_path,
                OdometerPhotoPath=odometer_path,
                InvoicePhotoPath=invoice_path,
                MyPertaminaPhotoPath=mypertamina_path,
                Odometer=odometer,
            )
            db.add(report)
            db.flush()  # Get the report ID
            
            # Create initial log entry
            ReportService._create_report_log(
                db=db,
                report_id=report.ID,  # type: ignore
                status=ReportStatusEnum.Pending,
                updated_by_user_id=user_id,
                notes="Report dibuat dengan upload foto"
            )
            
            db.commit()
            db.refresh(report)
            return report
        except Exception as e:
            # Rollback and cleanup uploaded files
            db.rollback()
            delete_file(vehicle_path)
            delete_file(odometer_path)
            delete_file(invoice_path)
            delete_file(mypertamina_path)
            raise HTTPException(status_code=500, detail=f"Failed to create report: {str(e)}")

    @staticmethod
    def update(db: Session, report_id: int, payload: ReportUpdate) -> ReportModel:
        r = db.query(ReportModel).filter(ReportModel.ID == report_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Report tidak ditemukan")
        
        # Track if status changed
        old_status = r.Status
        status_changed = False
        
        # optional FK validations if changed
        if payload.UserID is not None and payload.UserID != r.UserID:
            if not db.query(models.User).filter(models.User.ID == payload.UserID).first():
                raise HTTPException(status_code=400, detail="UserID tidak ditemukan")
            setattr(r, "UserID", payload.UserID)  # avoid static type checker complaining
        if payload.VehicleID is not None and payload.VehicleID != r.VehicleID:
            if not db.query(models.Vehicle).filter(models.Vehicle.ID == payload.VehicleID).first():
                raise HTTPException(status_code=400, detail="VehicleID tidak ditemukan")
            setattr(r, "VehicleID", payload.VehicleID)  # avoid static type checker complaining
        
        # Update Status if provided
        if payload.Status is not None and payload.Status != old_status:
            # Convert schema enum to model enum
            new_status = ReportStatusEnum[payload.Status.value]
            setattr(r, "Status", new_status)
            status_changed = True
            payload_status_for_log = new_status
        else:
            payload_status_for_log = None
        
        mutable_fields = [
            "KodeUnik","AmountRupiah","AmountLiter","Description","Latitude","Longitude",
            "VehiclePhysicalPhotoPath","OdometerPhotoPath","InvoicePhotoPath","MyPertaminaPhotoPath","Odometer"
        ]
        for field in mutable_fields:
            value = getattr(payload, field, None)
            if value is not None:
                setattr(r, field, value)
        
        # Create log if status changed
        if status_changed and payload_status_for_log:
            ReportService._create_report_log(
                db=db,
                report_id=report_id,
                status=payload_status_for_log,
                notes="Status diubah"
            )
        
        db.commit()
        db.refresh(r)
        return r
    
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
    ) -> ReportModel:
        """
        Update report dengan opsi upload foto baru (partial update)
        """
        # Get existing report
        r = db.query(ReportModel).filter(ReportModel.ID == report_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Report tidak ditemukan")
        
        # Validate FK if changed
        if user_id is not None and user_id != r.UserID:
            if not db.query(models.User).filter(models.User.ID == user_id).first():
                raise HTTPException(status_code=400, detail="UserID tidak ditemukan")
        
        if vehicle_id is not None and vehicle_id != r.VehicleID:
            if not db.query(models.Vehicle).filter(models.Vehicle.ID == vehicle_id).first():
                raise HTTPException(status_code=400, detail="VehicleID tidak ditemukan")
        
        # Store old photo paths for cleanup if update successful
        old_vehicle_path = str(r.VehiclePhysicalPhotoPath) if r.VehiclePhysicalPhotoPath else None
        old_odometer_path = str(r.OdometerPhotoPath) if r.OdometerPhotoPath else None
        old_invoice_path = str(r.InvoicePhotoPath) if r.InvoicePhotoPath else None
        old_mypertamina_path = str(r.MyPertaminaPhotoPath) if r.MyPertaminaPhotoPath else None
        
        # Upload new photos if provided
        new_vehicle_path = await save_report_photo(vehicle_photo, "vehicle") if vehicle_photo else None
        new_odometer_path = await save_report_photo(odometer_photo, "odometer") if odometer_photo else None
        new_invoice_path = await save_report_photo(invoice_photo, "invoice") if invoice_photo else None
        new_mypertamina_path = await save_report_photo(mypertamina_photo, "mypertamina") if mypertamina_photo else None
        
        try:
            # Update fields if provided (using setattr to avoid type checker issues)
            if kode_unik is not None:
                setattr(r, "KodeUnik", kode_unik)
            if user_id is not None:
                setattr(r, "UserID", user_id)
            if vehicle_id is not None:
                setattr(r, "VehicleID", vehicle_id)
            if amount_rupiah is not None:
                setattr(r, "AmountRupiah", amount_rupiah)
            if amount_liter is not None:
                setattr(r, "AmountLiter", amount_liter)
            if description is not None:
                setattr(r, "Description", description)
            if latitude is not None:
                setattr(r, "Latitude", latitude)
            if longitude is not None:
                setattr(r, "Longitude", longitude)
            if odometer is not None:
                setattr(r, "Odometer", odometer)
            
            # Update photo paths if new photos uploaded
            if new_vehicle_path:
                setattr(r, "VehiclePhysicalPhotoPath", new_vehicle_path)
            if new_odometer_path:
                setattr(r, "OdometerPhotoPath", new_odometer_path)
            if new_invoice_path:
                setattr(r, "InvoicePhotoPath", new_invoice_path)
            if new_mypertamina_path:
                setattr(r, "MyPertaminaPhotoPath", new_mypertamina_path)
            
            db.commit()
            db.refresh(r)
            
            # Delete old photos if new ones uploaded successfully
            if new_vehicle_path and old_vehicle_path:
                delete_file(old_vehicle_path)
            if new_odometer_path and old_odometer_path:
                delete_file(old_odometer_path)
            if new_invoice_path and old_invoice_path:
                delete_file(old_invoice_path)
            if new_mypertamina_path and old_mypertamina_path:
                delete_file(old_mypertamina_path)
            
            return r
        except Exception as e:
            # Rollback and cleanup new uploaded files
            db.rollback()
            delete_file(new_vehicle_path)
            delete_file(new_odometer_path)
            delete_file(new_invoice_path)
            delete_file(new_mypertamina_path)
            raise HTTPException(status_code=500, detail=f"Failed to update report: {str(e)}")

    @staticmethod
    def delete(db: Session, report_id: int) -> None:
        r = db.query(ReportModel).filter(ReportModel.ID == report_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Report tidak ditemukan")
        db.delete(r)
        db.commit()
    
    @staticmethod
    def update_status(
        db: Session,
        report_id: int,
        new_status: ReportStatusEnum,
        updated_by_user_id: int | None = None,
        notes: str | None = None
    ) -> ReportModel:
        """
        Update report status dan create log entry
        """
        report = db.query(ReportModel).filter(ReportModel.ID == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report tidak ditemukan")
        
        # Check if status actually changed
        if report.Status == new_status:
            return report
        
        # Update status
        old_status = report.Status
        setattr(report, "Status", new_status)
        
        # Create log entry
        ReportService._create_report_log(
            db=db,
            report_id=report_id,
            status=new_status,
            updated_by_user_id=updated_by_user_id,
            notes=notes or f"Status diubah dari {old_status.value} ke {new_status.value}"
        )
        
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    def get_report_logs(db: Session, report_id: int) -> List[Dict[str, Any]]:
        """
        Get all logs for a report with user information
        """
        logs = db.query(ReportLogModel).filter(
            ReportLogModel.ReportID == report_id
        ).order_by(ReportLogModel.Timestamp.asc()).all()
        
        result: List[Dict[str, Any]] = []
        for log in logs:
            user_name = None
            if log.UpdatedByUserID:
                user = db.query(models.User).filter(models.User.ID == log.UpdatedByUserID).first()
                user_name = user.NamaLengkap if user else None
            
            result.append({
                "ID": log.ID,
                "ReportID": log.ReportID,
                "Status": log.Status.value,
                "Timestamp": log.Timestamp.isoformat() if log.Timestamp else None,  # type: ignore
                "UpdatedByUserID": log.UpdatedByUserID,
                "UpdatedByUserName": user_name,
                "Notes": log.Notes
            })
        
        return result
    
    @staticmethod
    def get_my_reports(
        db: Session,
        user_id: int,
        vehicle_id: int | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Mendapatkan semua report user dengan detail lengkap (vehicle, submission info)
        Returns: (list of reports, total count)
        """
        
        # Base query
        query = db.query(ReportModel).filter(ReportModel.UserID == user_id)
        
        # Apply filters
        if vehicle_id is not None:
            query = query.filter(ReportModel.VehicleID == vehicle_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        reports = query.order_by(ReportModel.Timestamp.desc()).offset(offset).limit(limit).all()
        
        # Build detailed response
        detailed_reports: List[Dict[str, Any]] = []
        for report in reports:
            # Get vehicle info
            vehicle = db.query(models.Vehicle).filter(models.Vehicle.ID == report.VehicleID).first()
            vehicle_name = vehicle.Nama if vehicle else None
            vehicle_plat = vehicle.Plat if vehicle else None
            vehicle_type_id = vehicle.VehicleTypeID if vehicle else None
            
            # Get vehicle type
            vehicle_type_name = None
            if vehicle_type_id:  # type: ignore
                vehicle_type = db.query(models.VehicleType).filter(
                    models.VehicleType.ID == vehicle_type_id
                ).first()
                vehicle_type_name = vehicle_type.Nama if vehicle_type else None
            
            # Get submission info (if KodeUnik matches)
            submission = db.query(models.Submission).filter(
                models.Submission.KodeUnik == report.KodeUnik
            ).first()
            
            submission_status = None
            submission_total = None
            if submission:
                submission_status = submission.Status.value
                submission_total = float(submission.TotalCashAdvance)  # type: ignore
            
            report_detail: Dict[str, Any] = {
                "ID": report.ID,
                "KodeUnik": report.KodeUnik,
                "UserID": report.UserID,
                "VehicleID": report.VehicleID,
                "VehicleName": vehicle_name,
                "VehiclePlat": vehicle_plat,
                "VehicleType": vehicle_type_name,
                "AmountRupiah": float(report.AmountRupiah),  # type: ignore
                "AmountLiter": float(report.AmountLiter),  # type: ignore
                "Description": report.Description,
                "Status": report.Status.value,
                "Timestamp": report.Timestamp.isoformat() if report.Timestamp else None,  # type: ignore
                "Latitude": float(report.Latitude) if report.Latitude else None,  # type: ignore
                "Longitude": float(report.Longitude) if report.Longitude else None,  # type: ignore
                "Odometer": report.Odometer,
                "VehiclePhysicalPhotoPath": report.VehiclePhysicalPhotoPath,
                "OdometerPhotoPath": report.OdometerPhotoPath,
                "InvoicePhotoPath": report.InvoicePhotoPath,
                "MyPertaminaPhotoPath": report.MyPertaminaPhotoPath,
                # Photo URLs
                "VehiclePhysicalPhotoUrl": _get_photo_url(report.VehiclePhysicalPhotoPath),
                "OdometerPhotoUrl": _get_photo_url(report.OdometerPhotoPath),
                "InvoicePhotoUrl": _get_photo_url(report.InvoicePhotoPath),
                "MyPertaminaPhotoUrl": _get_photo_url(report.MyPertaminaPhotoPath),
                # Submission info
                "SubmissionStatus": submission_status,
                "SubmissionTotal": submission_total,
            }
            detailed_reports.append(report_detail)
        
        return detailed_reports, total
    
    @staticmethod
    def get_report_detail(db: Session, report_id: int, user_id: int) -> Dict[str, Any]:
        """
        Mendapatkan detail lengkap sebuah report termasuk info vehicle dan submission
        """
        
        # Get report
        report = db.query(ReportModel).filter(ReportModel.ID == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report tidak ditemukan")
        
        # Check ownership (optional: uncomment if you want to restrict)
        # if report.UserID != user_id:
        #     raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke report ini")
        
        # Get user info
        user = db.query(models.User).filter(models.User.ID == report.UserID).first()
        user_name = user.NamaLengkap if user else None
        user_nip = user.NIP if user else None
        
        # Get vehicle info
        vehicle = db.query(models.Vehicle).filter(models.Vehicle.ID == report.VehicleID).first()
        vehicle_info: Dict[str, Any] | None = None
        if vehicle:
            vehicle_type = db.query(models.VehicleType).filter(
                models.VehicleType.ID == vehicle.VehicleTypeID
            ).first()
            vehicle_info = {
                "ID": vehicle.ID,
                "Nama": vehicle.Nama,
                "Plat": vehicle.Plat,
                "Merek": vehicle.Merek,
                "KapasitasMesin": vehicle.KapasitasMesin,
                "JenisBensin": vehicle.JenisBensin,
                "Odometer": vehicle.Odometer,
                "Status": vehicle.Status.value,
                "VehicleType": vehicle_type.Nama if vehicle_type else None,
            }
        
        # Get submission info
        submission = db.query(models.Submission).filter(
            models.Submission.KodeUnik == report.KodeUnik
        ).first()
        
        submission_info: Dict[str, Any] | None = None
        if submission:
            creator = db.query(models.User).filter(models.User.ID == submission.CreatorID).first()
            receiver = db.query(models.User).filter(models.User.ID == submission.ReceiverID).first()
            
            submission_info = {
                "ID": submission.ID,
                "KodeUnik": submission.KodeUnik,
                "Status": submission.Status.value,
                "TotalCashAdvance": float(submission.TotalCashAdvance),  # type: ignore
                "CreatorID": submission.CreatorID,
                "CreatorName": creator.NamaLengkap if creator else None,
                "ReceiverID": submission.ReceiverID,
                "ReceiverName": receiver.NamaLengkap if receiver else None,
                "CreatedAt": submission.created_at.isoformat() if submission.created_at else None,  # type: ignore
            }
        
        # Get report logs
        report_logs = ReportService.get_report_logs(db, report_id)
        
        report_detail: Dict[str, Any] = {
            "ID": report.ID,
            "KodeUnik": report.KodeUnik,
            "UserID": report.UserID,
            "UserName": user_name,
            "UserNIP": user_nip,
            "VehicleID": report.VehicleID,
            "Vehicle": vehicle_info,
            "AmountRupiah": float(report.AmountRupiah),  # type: ignore
            "AmountLiter": float(report.AmountLiter),  # type: ignore
            "Description": report.Description,
            "Status": report.Status.value,
            "Timestamp": report.Timestamp.isoformat() if report.Timestamp else None,  # type: ignore
            "Latitude": float(report.Latitude) if report.Latitude else None,  # type: ignore
            "Longitude": float(report.Longitude) if report.Longitude else None,  # type: ignore
            "Odometer": report.Odometer,
            "Photos": {
                "VehiclePhysical": {
                    "path": report.VehiclePhysicalPhotoPath,
                    "url": _get_photo_url(report.VehiclePhysicalPhotoPath)
                },
                "Odometer": {
                    "path": report.OdometerPhotoPath,
                    "url": _get_photo_url(report.OdometerPhotoPath)
                },
                "Invoice": {
                    "path": report.InvoicePhotoPath,
                    "url": _get_photo_url(report.InvoicePhotoPath)
                },
                "MyPertamina": {
                    "path": report.MyPertaminaPhotoPath,
                    "url": _get_photo_url(report.MyPertaminaPhotoPath)
                }
            },
            "Submission": submission_info,
            "Logs": report_logs,
        }
        
        return report_detail
