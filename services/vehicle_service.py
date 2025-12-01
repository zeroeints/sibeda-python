from __future__ import annotations
from typing import List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from sqlalchemy import func
import model.models as models
from model.models import Vehicle as VehicleModel, VehicleStatusEnum
from schemas.schemas import VehicleCreate

class VehicleService:
    @staticmethod
    def _get_base_query(db: Session):
        """
        Query dasar dengan Eager Loading lengkap.
        Menambahkan: VehicleType, Dinas
        """
        return db.query(VehicleModel).options(
            joinedload(VehicleModel.vehicle_type),
            joinedload(VehicleModel.dinas) # [NEW] Load Dinas
        )

    @staticmethod
    def list(db: Session, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        q = VehicleService._get_base_query(db)
        
        # Pagination
        total_records = q.count()
        data = q.offset(offset).limit(limit).all()
        has_more = (offset + len(data)) < total_records
        
        # Stats
        stat_dict = {"total_data": total_records}
        stats_result = db.query(VehicleModel.Status, func.count(VehicleModel.ID)).group_by(VehicleModel.Status).all()
        
        for s in VehicleStatusEnum:
            stat_dict[f"total_{s.value.lower()}"] = 0
            
        for status_enum, count in stats_result:
            key = f"total_{status_enum.value.lower()}"
            stat_dict[key] = count
            
        return {
            "list": data,
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
            "month": None, 
            "year": None,
            "stat": stat_dict
        }

    # ... (Create, Update, Delete tetap sama, pastikan menggunakan _get_base_query saat return) ...
    @staticmethod
    def create(db: Session, payload: VehicleCreate) -> VehicleModel:
        if not db.query(models.VehicleType).filter(models.VehicleType.ID == payload.VehicleTypeID).first():
            raise HTTPException(400, "VehicleTypeID tidak ditemukan")
        if db.query(VehicleModel).filter(VehicleModel.Plat == payload.Plat).first():
            raise HTTPException(400, "Plat sudah terdaftar")
        if payload.DinasID and not db.query(models.Dinas).filter(models.Dinas.ID == payload.DinasID).first():
             raise HTTPException(400, "DinasID tidak ditemukan")

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
            if k == "Status" and val: setattr(v, k, val.value)
            else: setattr(v, k, val)
        
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
        """
        Mendapatkan kendaraan milik user.
        Refactored: Query dari Vehicle join ke Owners agar bisa eager load children (Dinas, Type).
        """
        # Query Vehicle yang dimiliki User via table asosiasi
        vehicles = db.query(VehicleModel).join(
            models.user_vehicle_association,
            models.user_vehicle_association.c.vehicle_id == VehicleModel.ID
        ).filter(
            models.user_vehicle_association.c.user_id == user_id
        ).options(
            joinedload(VehicleModel.vehicle_type),
            joinedload(VehicleModel.dinas)
        ).all()

        result = []
        for v in vehicles:
            # Hitung statistik per kendaraan
            submission_count = db.query(func.count(models.Submission.ID)).filter(
                (models.Submission.CreatorID == user_id) | (models.Submission.ReceiverID == user_id)
            ).scalar() or 0
            
            report_count = db.query(func.count(models.Report.ID)).filter(
                models.Report.VehicleID == v.ID, models.Report.UserID == user_id
            ).scalar() or 0
            
            latest_report = db.query(models.Report).filter(
                models.Report.VehicleID == v.ID, models.Report.UserID == user_id
            ).order_by(models.Report.Timestamp.desc()).first()
            
            total_fuel = db.query(func.sum(models.Report.AmountLiter)).filter(
                models.Report.VehicleID == v.ID, models.Report.UserID == user_id
            ).scalar() or 0
            
            total_rupiah = db.query(func.sum(models.Report.AmountRupiah)).filter(
                models.Report.VehicleID == v.ID, models.Report.UserID == user_id
            ).scalar() or 0
            
            # Construct Dictionary (sesuai MyVehicleResponse)
            vehicle_detail = {
                "ID": v.ID, "Nama": v.Nama, "Plat": v.Plat, "Merek": v.Merek, "KapasitasMesin": v.KapasitasMesin,
                "JenisBensin": v.JenisBensin, "Odometer": v.Odometer, "Status": v.Status, 
                "FotoFisik": v.FotoFisik, "AssetIconName": v.AssetIconName, "AssetIconColor": v.AssetIconColor,
                "TipeTransmisi": v.TipeTransmisi, "TotalFuelBar": v.TotalFuelBar, "CurrentFuelBar": v.CurrentFuelBar,
                "VehicleType": v.vehicle_type, # Pydantic handles nested object
                "Dinas": v.dinas,              # Pydantic handles nested object
                "DinasID": v.DinasID,
                # Stats
                "TotalSubmissions": submission_count, 
                "TotalReports": report_count,
                "TotalFuelLiters": float(total_fuel), 
                "TotalRupiahSpent": float(total_rupiah),
                "LastRefuelDate": latest_report.Timestamp if latest_report else None,
            }
            result.append(vehicle_detail)
        
        return result

    @staticmethod
    def get_vehicle_detail(db: Session, vehicle_id: int, user_id: int) -> Dict[str, Any]:
        """
        Mendapatkan detail lengkap dengan history refuel.
        """
        # Load vehicle dengan relasi
        vehicle = db.query(VehicleModel).options(
            joinedload(VehicleModel.vehicle_type),
            joinedload(VehicleModel.dinas)
        ).filter(VehicleModel.ID == vehicle_id).first()
        
        if not vehicle: raise HTTPException(404, "Kendaraan tidak ditemukan")
        
        # Ambil Report History
        reports = db.query(models.Report).filter(
            models.Report.VehicleID == vehicle_id,
            models.Report.UserID == user_id
        ).order_by(models.Report.Timestamp.desc()).limit(10).all()
        
        # Calculate totals (Sama seperti get_my_vehicles, logic bisa diekstrak jika mau DRY)
        submission_count = db.query(func.count(models.Submission.ID)).filter(
            (models.Submission.CreatorID == user_id) | (models.Submission.ReceiverID == user_id)
        ).scalar() or 0
        report_count = db.query(func.count(models.Report.ID)).filter(models.Report.VehicleID == vehicle_id, models.Report.UserID == user_id).scalar() or 0
        total_fuel = db.query(func.sum(models.Report.AmountLiter)).filter(models.Report.VehicleID == vehicle_id, models.Report.UserID == user_id).scalar() or 0
        total_rupiah = db.query(func.sum(models.Report.AmountRupiah)).filter(models.Report.VehicleID == vehicle_id, models.Report.UserID == user_id).scalar() or 0
        
        # Format report history
        report_history = []
        for r in reports:
            report_history.append({
                "ID": r.ID, "KodeUnik": r.KodeUnik, 
                "AmountRupiah": float(r.AmountRupiah), "AmountLiter": float(r.AmountLiter),
                "Timestamp": r.Timestamp, "Odometer": r.Odometer
            })
        
        # Construct Response
        return {
            "ID": vehicle.ID, "Nama": vehicle.Nama, "Plat": vehicle.Plat, "Merek": vehicle.Merek,
            "KapasitasMesin": vehicle.KapasitasMesin, "JenisBensin": vehicle.JenisBensin, 
            "Odometer": vehicle.Odometer, "Status": vehicle.Status, 
            "FotoFisik": vehicle.FotoFisik, "AssetIconName": vehicle.AssetIconName, "AssetIconColor": vehicle.AssetIconColor,
            "TipeTransmisi": vehicle.TipeTransmisi, "TotalFuelBar": vehicle.TotalFuelBar, "CurrentFuelBar": vehicle.CurrentFuelBar,
            "VehicleType": vehicle.vehicle_type,
            "Dinas": vehicle.dinas,
            "DinasID": vehicle.DinasID,
            # Stats
            "TotalSubmissions": submission_count,
            "TotalReports": report_count,
            "TotalFuelLiters": float(total_fuel),
            "TotalRupiahSpent": float(total_rupiah),
            "RecentRefuelHistory": report_history,
        }

    # ... (get_by_dinas update to use _get_base_query) ...
    @staticmethod
    def get_by_dinas(db: Session, dinas_id: int, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        q = VehicleService._get_base_query(db).filter(VehicleModel.DinasID == dinas_id)
        
        total = q.count()
        data = q.offset(offset).limit(limit).all()
        has_more = (offset + len(data)) < total
        
        return {
            "list": data,
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
            "stat": {"total_data": total}
        }
    
    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> List[VehicleModel]:
        """
        Mendapatkan list kendaraan yang di-assign ke user tertentu.
        """
        # Cek user exists
        user = db.query(models.User).filter(models.User.ID == user_id).first()
        if not user:
            raise HTTPException(404, "User tidak ditemukan")

        # Query via relationship table
        vehicles = db.query(VehicleModel).join(
            models.user_vehicle_association,
            models.user_vehicle_association.c.vehicle_id == VehicleModel.ID
        ).filter(
            models.user_vehicle_association.c.user_id == user_id
        ).options(
            joinedload(VehicleModel.vehicle_type),
            joinedload(VehicleModel.dinas)
        ).all()
        
        return vehicles

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