from __future__ import annotations
from typing import List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from sqlalchemy import func
import model.models as models
from schemas.schemas import VehicleCreate, VehicleUpdate

class VehicleService:
    @staticmethod
    def _get_base_query(db: Session):
        return db.query(models.Vehicle).options(
            joinedload(models.Vehicle.vehicle_type),
            joinedload(models.Vehicle.dinas)
        )

    @staticmethod
    def list(db: Session, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        q = VehicleService._get_base_query(db)
        total_records = q.count()
        data = q.offset(offset).limit(limit).all()
        has_more = (offset + len(data)) < total_records
        
        stat_dict = {"total_data": total_records}
        stats_result = db.query(models.Vehicle.status, func.count(models.Vehicle.id)).group_by(models.Vehicle.status).all()
        
        for s in models.VehicleStatusEnum:
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

    @staticmethod
    def create(db: Session, payload: VehicleCreate) -> models.Vehicle:
        if not db.query(models.VehicleType).filter(models.VehicleType.id == payload.vehicle_type_id).first():
            raise HTTPException(400, "VehicleTypeID tidak ditemukan")
        
        if db.query(models.Vehicle).filter(models.Vehicle.plat == payload.plat).first():
            raise HTTPException(400, "Plat sudah terdaftar")
        
        if payload.dinas_id and not db.query(models.Dinas).filter(models.Dinas.id == payload.dinas_id).first():
             raise HTTPException(400, "DinasID tidak ditemukan")

        # Map snake_case schema to snake_case model
        v = models.Vehicle(
            nama=payload.nama,
            plat=payload.plat,
            vehicle_type_id=payload.vehicle_type_id,
            dinas_id=payload.dinas_id,
            kapasitas_mesin=payload.kapasitas_mesin,
            odometer=payload.odometer,
            jenis_bensin=payload.jenis_bensin,
            merek=payload.merek,
            foto_fisik=payload.foto_fisik,
            asset_icon_name=payload.asset_icon_name,
            asset_icon_color=payload.asset_icon_color,
            tipe_transmisi=payload.tipe_transmisi,
            total_fuel_bar=payload.total_fuel_bar,
            current_fuel_bar=payload.current_fuel_bar,
            status=payload.status.value if payload.status else models.VehicleStatusEnum.active.value
        )
        
        db.add(v)
        db.commit()
        return VehicleService._get_base_query(db).filter(models.Vehicle.id == v.id).first() # type: ignore

    @staticmethod
    def update(db: Session, vehicle_id: int, payload: VehicleCreate | VehicleUpdate) -> models.Vehicle:
        v = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
        if not v: raise HTTPException(404, "Vehicle not found")
        
        update_data = payload.model_dump(exclude_unset=True)
        
        for key, val in update_data.items():
            if key == "status" and val:
                setattr(v, key, val.value)
            elif hasattr(v, key):
                setattr(v, key, val)
        
        db.commit()
        return VehicleService._get_base_query(db).filter(models.Vehicle.id == v.id).first() # type: ignore

    @staticmethod
    def delete(db: Session, vehicle_id: int) -> None:
        v = db.query(models.Vehicle).get(vehicle_id)
        if not v: raise HTTPException(404, "Not found")
        db.delete(v)
        db.commit()
    
    @staticmethod
    def get_my_vehicles(db: Session, user_id: int) -> List[Dict[str, Any]]:
        vehicles = db.query(models.Vehicle).join(
            models.user_vehicle_association,
            models.user_vehicle_association.c.vehicle_id == models.Vehicle.id
        ).filter(
            models.user_vehicle_association.c.user_id == user_id
        ).options(
            joinedload(models.Vehicle.vehicle_type),
            joinedload(models.Vehicle.dinas)
        ).all()

        result = []
        for v in vehicles:
            submission_count = db.query(func.count(models.Submission.id)).filter(
                (models.Submission.creator_id == user_id) | (models.Submission.receiver_id == user_id)
            ).scalar() or 0
            
            report_count = db.query(func.count(models.Report.id)).filter(
                models.Report.vehicle_id == v.id, models.Report.user_id == user_id
            ).scalar() or 0
            
            latest_report = db.query(models.Report).filter(
                models.Report.vehicle_id == v.id, models.Report.user_id == user_id
            ).order_by(models.Report.timestamp.desc()).first()
            
            total_fuel = db.query(func.sum(models.Report.amount_liter)).filter(
                models.Report.vehicle_id == v.id, models.Report.user_id == user_id
            ).scalar() or 0
            
            total_rupiah = db.query(func.sum(models.Report.amount_rupiah)).filter(
                models.Report.vehicle_id == v.id, models.Report.user_id == user_id
            ).scalar() or 0
            
            vehicle_detail = {
                "id": v.id, 
                "nama": v.nama, 
                "plat": v.plat, 
                "merek": v.merek, 
                "kapasitas_mesin": v.kapasitas_mesin,
                "jenis_bensin": v.jenis_bensin, 
                "odometer": v.odometer, 
                "status": v.status, 
                "foto_fisik": v.foto_fisik, 
                "asset_icon_name": v.asset_icon_name, 
                "asset_icon_color": v.asset_icon_color,
                "tipe_transmisi": v.tipe_transmisi, 
                "total_fuel_bar": v.total_fuel_bar, 
                "current_fuel_bar": v.current_fuel_bar,
                "vehicle_type": v.vehicle_type,
                "dinas": v.dinas,
                "dinas_id": v.dinas_id,
                "total_submissions": submission_count, 
                "total_reports": report_count,
                "total_fuel_liters": float(total_fuel), 
                "total_rupiah_spent": float(total_rupiah),
                "last_refuel_date": latest_report.timestamp if latest_report else None,
            }
            result.append(vehicle_detail)
        
        return result

    @staticmethod
    def get_vehicle_detail(db: Session, vehicle_id: int, user_id: int) -> Dict[str, Any]:
        vehicle = db.query(models.Vehicle).options(
            joinedload(models.Vehicle.vehicle_type),
            joinedload(models.Vehicle.dinas)
        ).filter(models.Vehicle.id == vehicle_id).first()
        
        if not vehicle: raise HTTPException(404, "Kendaraan tidak ditemukan")
        
        reports = db.query(models.Report).filter(
            models.Report.vehicle_id == vehicle_id,
            models.Report.user_id == user_id
        ).order_by(models.Report.timestamp.desc()).limit(10).all()
        
        submission_count = db.query(func.count(models.Submission.id)).filter(
            (models.Submission.creator_id == user_id) | (models.Submission.receiver_id == user_id)
        ).scalar() or 0
        report_count = db.query(func.count(models.Report.id)).filter(models.Report.vehicle_id == vehicle_id, models.Report.user_id == user_id).scalar() or 0
        total_fuel = db.query(func.sum(models.Report.amount_liter)).filter(models.Report.vehicle_id == vehicle_id, models.Report.user_id == user_id).scalar() or 0
        total_rupiah = db.query(func.sum(models.Report.amount_rupiah)).filter(models.Report.vehicle_id == vehicle_id, models.Report.user_id == user_id).scalar() or 0
        
        report_history = []
        for r in reports:
            report_history.append({
                "id": r.id, 
                "kode_unik": r.kode_unik, 
                "amount_rupiah": float(r.amount_rupiah), 
                "amount_liter": float(r.amount_liter),
                "timestamp": r.timestamp, 
                "odometer": r.odometer
            })
        
        return {
            "id": vehicle.id, 
            "nama": vehicle.nama, 
            "plat": vehicle.plat, 
            "merek": vehicle.merek,
            "kapasitas_mesin": vehicle.kapasitas_mesin, 
            "jenis_bensin": vehicle.jenis_bensin, 
            "odometer": vehicle.odometer, 
            "status": vehicle.status, 
            "foto_fisik": vehicle.foto_fisik, 
            "asset_icon_name": vehicle.asset_icon_name, 
            "asset_icon_color": vehicle.asset_icon_color,
            "tipe_transmisi": vehicle.tipe_transmisi, 
            "total_fuel_bar": vehicle.total_fuel_bar, 
            "current_fuel_bar": vehicle.current_fuel_bar,
            "vehicle_type": vehicle.vehicle_type,
            "dinas": vehicle.dinas,
            "dinas_id": vehicle.dinas_id,
            "total_submissions": submission_count,
            "total_reports": report_count,
            "total_fuel_liters": float(total_fuel),
            "total_rupiah_spent": float(total_rupiah),
            "recent_refuel_history": report_history,
        }

    @staticmethod
    def get_by_dinas(db: Session, dinas_id: int, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        q = VehicleService._get_base_query(db).filter(models.Vehicle.dinas_id == dinas_id)
        
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
    def get_by_user_id(db: Session, user_id: int) -> List[models.Vehicle]:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(404, "User tidak ditemukan")

        vehicles = db.query(models.Vehicle).join(
            models.user_vehicle_association,
            models.user_vehicle_association.c.vehicle_id == models.Vehicle.id
        ).filter(
            models.user_vehicle_association.c.user_id == user_id
        ).options(
            joinedload(models.Vehicle.vehicle_type),
            joinedload(models.Vehicle.dinas)
        ).all()
        
        return vehicles

    @staticmethod
    def assign_user(db: Session, vehicle_id: int, user_id: int) -> None:
        vehicle = db.query(models.Vehicle).get(vehicle_id)
        user = db.query(models.User).get(user_id)
        
        if not vehicle or not user:
            raise HTTPException(status_code=404, detail="Data tidak ditemukan")
            
        if vehicle not in user.vehicles:
            user.vehicles.append(vehicle)
            db.commit()

    @staticmethod
    def unassign_user(db: Session, vehicle_id: int, user_id: int) -> None:
        user = db.query(models.User).get(user_id)
        vehicle = db.query(models.Vehicle).get(vehicle_id)

        if user and vehicle and vehicle in user.vehicles:
            user.vehicles.remove(vehicle)
            db.commit()