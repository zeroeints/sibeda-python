from __future__ import annotations
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
import model.models as models
from model.models import Report as ReportModel
from schemas.schemas import ReportCreate, ReportUpdate

class ReportService:
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
        report = ReportModel(
            KodeUnik=payload.KodeUnik,
            UserID=payload.UserID,
            VehicleID=payload.VehicleID,
            AmountRupiah=payload.AmountRupiah,
            AmountLiter=payload.AmountLiter,
            Description=payload.Description,
            Latitude=payload.Latitude,
            Longitude=payload.Longitude,
            VehiclePhysicalPhotoPath=payload.VehiclePhysicalPhotoPath,
            OdometerPhotoPath=payload.OdometerPhotoPath,
            InvoicePhotoPath=payload.InvoicePhotoPath,
            MyPertaminaPhotoPath=payload.MyPertaminaPhotoPath,
            Odometer=payload.Odometer,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def update(db: Session, report_id: int, payload: ReportUpdate) -> ReportModel:
        r = db.query(ReportModel).filter(ReportModel.ID == report_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Report tidak ditemukan")
        # optional FK validations if changed
        if payload.UserID is not None and payload.UserID != r.UserID:
            if not db.query(models.User).filter(models.User.ID == payload.UserID).first():
                raise HTTPException(status_code=400, detail="UserID tidak ditemukan")
            setattr(r, "UserID", payload.UserID)  # avoid static type checker complaining
        if payload.VehicleID is not None and payload.VehicleID != r.VehicleID:
            if not db.query(models.Vehicle).filter(models.Vehicle.ID == payload.VehicleID).first():
                raise HTTPException(status_code=400, detail="VehicleID tidak ditemukan")
            setattr(r, "VehicleID", payload.VehicleID)  # avoid static type checker complaining
        mutable_fields = [
            "KodeUnik","AmountRupiah","AmountLiter","Description","Latitude","Longitude",
            "VehiclePhysicalPhotoPath","OdometerPhotoPath","InvoicePhotoPath","MyPertaminaPhotoPath","Odometer"
        ]
        for field in mutable_fields:
            value = getattr(payload, field, None)
            if value is not None:
                setattr(r, field, value)
        db.commit()
        db.refresh(r)
        return r

    @staticmethod
    def delete(db: Session, report_id: int) -> None:
        r = db.query(ReportModel).filter(ReportModel.ID == report_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Report tidak ditemukan")
        db.delete(r)
        db.commit()
    
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
                "Timestamp": report.Timestamp.isoformat() if report.Timestamp else None,  # type: ignore
                "Latitude": float(report.Latitude) if report.Latitude else None,  # type: ignore
                "Longitude": float(report.Longitude) if report.Longitude else None,  # type: ignore
                "Odometer": report.Odometer,
                "VehiclePhysicalPhotoPath": report.VehiclePhysicalPhotoPath,
                "OdometerPhotoPath": report.OdometerPhotoPath,
                "InvoicePhotoPath": report.InvoicePhotoPath,
                "MyPertaminaPhotoPath": report.MyPertaminaPhotoPath,
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
            "Timestamp": report.Timestamp.isoformat() if report.Timestamp else None,  # type: ignore
            "Latitude": float(report.Latitude) if report.Latitude else None,  # type: ignore
            "Longitude": float(report.Longitude) if report.Longitude else None,  # type: ignore
            "Odometer": report.Odometer,
            "Photos": {
                "VehiclePhysical": report.VehiclePhysicalPhotoPath,
                "Odometer": report.OdometerPhotoPath,
                "Invoice": report.InvoicePhotoPath,
                "MyPertamina": report.MyPertaminaPhotoPath,
            },
            "Submission": submission_info,
        }
        
        return report_detail
