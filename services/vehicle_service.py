from __future__ import annotations
from typing import List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from sqlalchemy import func as sql_func
import model.models as models
from model.models import Vehicle as VehicleModel
from schemas.schemas import VehicleCreate

class VehicleService:
    @staticmethod
    def _get_base_query(db: Session):
        return db.query(VehicleModel).options(joinedload(VehicleModel.vehicle_type))

    @staticmethod
    def list(db: Session) -> List[VehicleModel]:
        return VehicleService._get_base_query(db).all()

    @staticmethod
    def create(db: Session, payload: VehicleCreate) -> VehicleModel:
        if not db.query(models.VehicleType).filter(models.VehicleType.ID == payload.VehicleTypeID).first():
            raise HTTPException(400, "VehicleTypeID tidak ditemukan")
        if db.query(VehicleModel).filter(VehicleModel.Plat == payload.Plat).first():
            raise HTTPException(400, "Plat sudah terdaftar")
        
        data = payload.model_dump()
        if payload.Status: data["Status"] = payload.Status.value
        
        v = VehicleModel(**data)
        db.add(v)
        db.commit()
        return VehicleService._get_base_query(db).filter(VehicleModel.ID == v.ID).first() # type: ignore

    @staticmethod
    def update(db: Session, vehicle_id: int, payload: VehicleCreate) -> VehicleModel:
        v = db.query(VehicleModel).filter(VehicleModel.ID == vehicle_id).first()
        if not v: raise HTTPException(404, "Vehicle not found")
        
        for k, val in payload.model_dump(exclude_unset=True).items():
            if k == "Status" and val:
                setattr(v, k, val.value)
            else:
                setattr(v, k, val)
        
        db.commit()
        return VehicleService._get_base_query(db).filter(VehicleModel.ID == v.ID).first() # type: ignore

    @staticmethod
    def delete(db: Session, vehicle_id: int) -> None:
        v = db.query(VehicleModel).get(vehicle_id)
        if not v: raise HTTPException(404, "Not found")
        db.delete(v)
        db.commit()
    
    @staticmethod
    def get_my_vehicles(db: Session, user_id: int) -> List[Dict[str, Any]]:
        user = db.query(models.User).filter(models.User.ID == user_id).first()
        if not user: return []
        
        # Ambil vehicle via relation many-to-many
        # Pastikan relation di model sudah benar
        vehicles = user.vehicles
        result = []
        
        for v in vehicles:
            # # Query stats manual
            # sub_count = db.query(sql_func.count(models.Submission.ID)).filter(
            #     models.Submission.VehicleID == v.ID, 
            #     (models.Submission.CreatorID == user_id) | (models.Submission.ReceiverID == user_id)
            # ).scalar() or 0
            
            # Get vehicle type name
            vehicle_type = db.query(models.VehicleType).filter(
                models.VehicleType.ID == v.VehicleTypeID
            ).first()
            
            # Count submissions using this vehicle
            submission_count = db.query(sql_func.count(models.Submission.ID)).filter(
                (models.Submission.CreatorID == user_id) | (models.Submission.ReceiverID == user_id)
            ).scalar() or 0
            
            # Count reports using this vehicle
            report_count = db.query(sql_func.count(models.Report.ID)).filter(
                models.Report.VehicleID == v.ID,
                models.Report.UserID == user_id
            ).scalar() or 0
            
            # Get latest report for this vehicle by this user
            latest_report = db.query(models.Report).filter(
                models.Report.VehicleID == v.ID,
                models.Report.UserID == user_id
            ).order_by(models.Report.Timestamp.desc()).first()
            
            # Calculate total fuel (liters) from reports
            total_fuel_liters = db.query(
                sql_func.sum(models.Report.AmountLiter)
            ).filter(
                models.Report.VehicleID == v.ID,
                models.Report.UserID == user_id
            ).scalar() or 0
            
            # Calculate total rupiah spent from reports
            total_rupiah = db.query(
                sql_func.sum(models.Report.AmountRupiah)
            ).filter(
                models.Report.VehicleID == v.ID,
                models.Report.UserID == user_id
            ).scalar() or 0

            vt = db.query(models.VehicleType).get(v.VehicleTypeID)
            
            vehicle_detail: Dict[str, Any] = {
                "ID": v.ID,
                "Nama": v.Nama,
                "Plat": v.Plat,
                "Merek": v.Merek,
                "KapasitasMesin": v.KapasitasMesin,
                "JenisBensin": v.JenisBensin,
                "Odometer": v.Odometer,
                "Status": v.Status.value,
                "FotoFisik": v.FotoFisik,
                "VehicleTypeID": v.VehicleTypeID,
                "VehicleTypeName": vehicle_type.Nama if vehicle_type else None,
                "VehicleType": {"ID": vt.ID, "Nama": vt.Nama} if vt else None,
                # User usage statistics
                "TotalSubmissions": submission_count,
                "TotalReports": report_count,
                "TotalFuelLiters": float(total_fuel_liters),  # type: ignore
                "TotalRupiahSpent": float(total_rupiah),  # type: ignore
                # Latest refuel info
                "LastRefuelDate": latest_report.Timestamp.isoformat() if latest_report else None,
                "LastRefuelLiters": float(latest_report.AmountLiter) if latest_report else None,  # type: ignore
                "LastRefuelRupiah": float(latest_report.AmountRupiah) if latest_report else None,  # type: ignore
                "LastOdometer": latest_report.Odometer if latest_report else None,
            }
            result.append(vehicle_detail)
            
            
        return result

class VehicleService:
    @staticmethod
    def list(db: Session) -> List[VehicleModel]:
        return db.query(VehicleModel).all()

    @staticmethod
    def create(db: Session, payload: VehicleCreate) -> VehicleModel:
        # Ensure vehicle type exists
        if not db.query(models.VehicleType).filter(models.VehicleType.ID == payload.VehicleTypeID).first():
            raise HTTPException(status_code=400, detail="VehicleTypeID tidak ditemukan")
        # Unique plat
        if db.query(VehicleModel).filter(VehicleModel.Plat == payload.Plat).first():
            raise HTTPException(status_code=400, detail="Plat sudah terdaftar")
        data: Dict[str, Any] = {
            "Nama": payload.Nama,
            "Plat": payload.Plat,
            "VehicleTypeID": payload.VehicleTypeID,
            "KapasitasMesin": payload.KapasitasMesin,
            "Odometer": payload.Odometer,
            "JenisBensin": payload.JenisBensin,
            "Merek": payload.Merek,
            "FotoFisik": payload.FotoFisik,
            "AssetIconName": payload.AssetIconName,
            "AssetIconColor": payload.AssetIconColor,
        }
        if payload.Status:
            data["Status"] = payload.Status.value
        v = models.Vehicle(**data)
        db.add(v)
        db.commit()
        db.refresh(v)
        return v

    @staticmethod
    def update(db: Session, vehicle_id: int, payload: VehicleCreate) -> VehicleModel:
        v = db.query(VehicleModel).filter(VehicleModel.ID == vehicle_id).first()
        if not v:
            raise HTTPException(status_code=404, detail="Vehicle tidak ditemukan")
        if payload.Plat != v.Plat and db.query(VehicleModel).filter(VehicleModel.Plat == payload.Plat).first():
            raise HTTPException(status_code=400, detail="Plat sudah terdaftar")
        # ensure vehicle type still valid
        if not db.query(models.VehicleType).filter(models.VehicleType.ID == payload.VehicleTypeID).first():
            raise HTTPException(status_code=400, detail="VehicleTypeID tidak ditemukan")
        update_map: Dict[str, Any] = {
            "Nama": payload.Nama,
            "Plat": payload.Plat,
            "VehicleTypeID": payload.VehicleTypeID,
            "KapasitasMesin": payload.KapasitasMesin,
            "Odometer": payload.Odometer,
            "JenisBensin": payload.JenisBensin,
            "Merek": payload.Merek,
            "FotoFisik": payload.FotoFisik,
            "AssetIconName": payload.AssetIconName,
            "AssetIconColor": payload.AssetIconColor,
        }
        if payload.Status:
            update_map["Status"] = payload.Status.value
        for field, value in update_map.items():
            setattr(v, field, value)
        db.commit()
        db.refresh(v)
        return v

    @staticmethod
    def delete(db: Session, vehicle_id: int) -> None:
        v = db.query(VehicleModel).filter(VehicleModel.ID == vehicle_id).first()
        if not v:
            raise HTTPException(status_code=404, detail="Vehicle tidak ditemukan")
        db.delete(v)
        db.commit()
    
    @staticmethod
    def get_my_vehicles(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Mendapatkan kendaraan milik user berdasarkan relasi many-to-many.
        Tidak lagi query submission/report manual.
        """
        user = db.query(models.User).filter(models.User.ID == user_id).first()
        if not user:
            return []
            
        # Menggunakan relasi .vehicles yang baru dibuat
        vehicles = user.vehicles 
        
        result: List[Dict[str, Any]] = []
        for vehicle in vehicles:
            # Get vehicle type name
            vehicle_type = db.query(models.VehicleType).filter(
                models.VehicleType.ID == vehicle.VehicleTypeID
            ).first()
            
            # Count submissions using this vehicle
            submission_count = db.query(sql_func.count(models.Submission.ID)).filter(
                # models.Submission.VehicleID == vehicle.ID,
                (models.Submission.CreatorID == user_id) | (models.Submission.ReceiverID == user_id)
            ).scalar() or 0
            
            # Count reports using this vehicle
            report_count = db.query(sql_func.count(models.Report.ID)).filter(
                models.Report.VehicleID == vehicle.ID,
                models.Report.UserID == user_id
            ).scalar() or 0
            
            # Get latest report for this vehicle by this user
            latest_report = db.query(models.Report).filter(
                models.Report.VehicleID == vehicle.ID,
                models.Report.UserID == user_id
            ).order_by(models.Report.Timestamp.desc()).first()
            
            # Calculate total fuel (liters) from reports
            total_fuel_liters = db.query(
                sql_func.sum(models.Report.AmountLiter)
            ).filter(
                models.Report.VehicleID == vehicle.ID,
                models.Report.UserID == user_id
            ).scalar() or 0
            
            # Calculate total rupiah spent from reports
            total_rupiah = db.query(
                sql_func.sum(models.Report.AmountRupiah)
            ).filter(
                models.Report.VehicleID == vehicle.ID,
                models.Report.UserID == user_id
            ).scalar() or 0
            
            vehicle_detail: Dict[str, Any] = {
                "ID": vehicle.ID,
                "Nama": vehicle.Nama,
                "Plat": vehicle.Plat,
                "Merek": vehicle.Merek,
                "KapasitasMesin": vehicle.KapasitasMesin,
                "JenisBensin": vehicle.JenisBensin,
                "Odometer": vehicle.Odometer,
                "Status": vehicle.Status.value,
                "FotoFisik": vehicle.FotoFisik,
                "VehicleTypeID": vehicle.VehicleTypeID,
                "VehicleTypeName": vehicle_type.Nama if vehicle_type else None,
                # User usage statistics
                "TotalSubmissions": submission_count,
                "TotalReports": report_count,
                "TotalFuelLiters": float(total_fuel_liters),  # type: ignore
                "TotalRupiahSpent": float(total_rupiah),  # type: ignore
                # Latest refuel info
                "LastRefuelDate": latest_report.Timestamp.isoformat() if latest_report else None,
                "LastRefuelLiters": float(latest_report.AmountLiter) if latest_report else None,  # type: ignore
                "LastRefuelRupiah": float(latest_report.AmountRupiah) if latest_report else None,  # type: ignore
                "LastOdometer": latest_report.Odometer if latest_report else None,
            }
            result.append(vehicle_detail)
        
        return result
    
    @staticmethod
    def get_vehicle_detail(db: Session, vehicle_id: int, user_id: int) -> Dict[str, Any]:
        """
        Mendapatkan detail lengkap sebuah kendaraan termasuk riwayat penggunaan oleh user
        """
        from sqlalchemy import func as sql_func
        
        # Get vehicle
        vehicle = db.query(VehicleModel).filter(VehicleModel.ID == vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Kendaraan tidak ditemukan")
        
        # Get vehicle type
        vehicle_type = db.query(models.VehicleType).filter(
            models.VehicleType.ID == vehicle.VehicleTypeID
        ).first()
        
        # Get all reports for this vehicle by this user
        reports = db.query(models.Report).filter(
            models.Report.VehicleID == vehicle_id,
            models.Report.UserID == user_id
        ).order_by(models.Report.Timestamp.desc()).limit(10).all()
        
        # Count total submissions and reports
        submission_count = db.query(sql_func.count(models.Submission.ID)).filter(
            # models.Submission.VehicleID == vehicle_id,
            (models.Submission.CreatorID == user_id) | (models.Submission.ReceiverID == user_id)
        ).scalar() or 0
        
        report_count = db.query(sql_func.count(models.Report.ID)).filter(
            models.Report.VehicleID == vehicle_id,
            models.Report.UserID == user_id
        ).scalar() or 0
        
        # Calculate totals
        total_fuel_liters = db.query(
            sql_func.sum(models.Report.AmountLiter)
        ).filter(
            models.Report.VehicleID == vehicle_id,
            models.Report.UserID == user_id
        ).scalar() or 0
        
        total_rupiah = db.query(
            sql_func.sum(models.Report.AmountRupiah)
        ).filter(
            models.Report.VehicleID == vehicle_id,
            models.Report.UserID == user_id
        ).scalar() or 0
        
        # Format report history
        report_history: List[Dict[str, Any]] = []
        for report in reports:
            report_data: Dict[str, Any] = {
                "ID": report.ID,
                "KodeUnik": report.KodeUnik,
                "AmountRupiah": float(report.AmountRupiah),  # type: ignore
                "AmountLiter": float(report.AmountLiter),  # type: ignore
                "Description": report.Description,
                "Timestamp": report.Timestamp.isoformat(),
                "Odometer": report.Odometer,
                "Latitude": float(report.Latitude) if report.Latitude else None,  # type: ignore
                "Longitude": float(report.Longitude) if report.Longitude else None,  # type: ignore
            }
            report_history.append(report_data)
        
        vehicle_detail: Dict[str, Any] = {
            "ID": vehicle.ID,
            "Nama": vehicle.Nama,
            "Plat": vehicle.Plat,
            "Merek": vehicle.Merek,
            "KapasitasMesin": vehicle.KapasitasMesin,
            "JenisBensin": vehicle.JenisBensin,
            "Odometer": vehicle.Odometer,
            "Status": vehicle.Status.value,
            "FotoFisik": vehicle.FotoFisik,
            "VehicleTypeID": vehicle.VehicleTypeID,
            "VehicleTypeName": vehicle_type.Nama if vehicle_type else None,
            # Statistics
            "TotalSubmissions": submission_count,
            "TotalReports": report_count,
            "TotalFuelLiters": float(total_fuel_liters),  # type: ignore
            "TotalRupiahSpent": float(total_rupiah),  # type: ignore
            # Recent refuel history (last 10)
            "RecentRefuelHistory": report_history,
        }
        
        return vehicle_detail

    @staticmethod
    def assign_user(db: Session, vehicle_id: int, user_id: int) -> None:
        """Assign kendaraan ke user (Many-to-Many)"""
        vehicle = db.query(VehicleModel).get(vehicle_id)
        user = db.query(models.User).get(user_id)
        
        if not vehicle or not user:
            raise HTTPException(status_code=404, detail="Data tidak ditemukan")
            
        # Cek jika sudah ada
        if vehicle not in user.vehicles:
            user.vehicles.append(vehicle)
            db.commit()

    @staticmethod
    def unassign_user(db: Session, vehicle_id: int, user_id: int) -> None:
        """Hapus kepemilikan kendaraan dari user"""
        user = db.query(models.User).get(user_id)
        vehicle = db.query(VehicleModel).get(vehicle_id)

        if user and vehicle and vehicle in user.vehicles:
            user.vehicles.remove(vehicle)
            db.commit()