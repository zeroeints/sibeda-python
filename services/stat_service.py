from sqlalchemy.orm import Session
from sqlalchemy import func, extract, distinct, and_, or_
from datetime import datetime
import model.models as models
from schemas.schemas import (
    PicStatResponse, MonthlyData, 
    KadisStatResponse, AdminStatResponse, MonthlyData
)

class StatService:
    @staticmethod
    def get_pic_stats(db: Session, user_id: int) -> PicStatResponse:
        current_year = datetime.now().year
        
        # 1. Vehicle Count (Many-to-Many logic)
        user = db.query(models.User).filter(models.User.ID == user_id).first()
        vehicle_count = len(user.vehicles) if user else 0
        
        # 2. Report Count
        report_count = db.query(models.Report).filter(models.Report.UserID == user_id).count()
        
        # 3. Money Usage per Month (Only Accepted Reports)
        # Query sum amount per bulan
        usage_query = db.query(
            extract('month', models.Report.Timestamp).label('month'),
            func.sum(models.Report.AmountRupiah).label('total')
        ).filter(
            models.Report.UserID == user_id,
            models.Report.Status == models.ReportStatusEnum.Accepted,
            extract('year', models.Report.Timestamp) == current_year
        ).group_by(
            extract('month', models.Report.Timestamp)
        ).all()
        
        # Mapping hasil query ke list 0-11 (Jan-Des)
        # Note: extract('month') di MySQL/Postgres biasanya return 1-12
        usage_map = {row.month: float(row.total) for row in usage_query}
        
        money_usage_list = []
        total_year = 0.0
        
        for i in range(1, 13): # 1 to 12
            val = usage_map.get(i, 0.0)
            # Schema minta month index 0 atau 1? Biasanya chart JS pakai index 0. 
            # Kita pakai index 0 (0 = Januari)
            money_usage_list.append(MonthlyData(month=i-1, value=val))
            total_year += val
            
        # 4. Average (Total setahun / 12 bulan)
        average = total_year / 12 if total_year > 0 else 0.0
        
        return PicStatResponse(
            vehicle_count=vehicle_count,
            report_count=report_count,
            money_usage=money_usage_list,
            average=average
        )

    @staticmethod
    def _fill_monthly_data(query_result, year_avg_divisor=12) -> tuple[list[MonthlyData], float]:
        """Helper untuk mengubah hasil query group by month menjadi list 0-11"""
        # query_result format: [(month_int, value), ...]
        # Note: extract('month') return 1-12
        
        data_map = {row[0]: float(row[1]) for row in query_result}
        result_list = []
        total_value = 0.0

        for i in range(1, 13):
            val = data_map.get(i, 0.0)
            result_list.append(MonthlyData(month=i-1, value=val))
            total_value += val
            
        avg = total_value / year_avg_divisor if total_value > 0 else 0.0
        return result_list, avg

    @staticmethod
    def get_kadis_stats(db: Session, user_dinas_id: int) -> KadisStatResponse:
        current_year = datetime.now().year
        
        # 1. Ambil List ID User yang ada di dinas ini
        # Kita butuh subquery atau list ID untuk filtering tabel lain
        dinas_user_ids = db.query(models.User.ID).filter(models.User.DinasID == user_dinas_id).all()
        user_ids = [u.ID for u in dinas_user_ids]
        
        if not user_ids:
            # Jika dinas kosong, return 0 semua
            empty_months = [MonthlyData(month=i, value=0) for i in range(12)]
            return KadisStatResponse(
                dinas_proposal_count=0,
                dinas_report_count=0,
                dinas_proposal_monthly=empty_months,
                dinas_proposal_average=0,
                dinas_money_usage_monthly=empty_months,
                dinas_money_usage_average=0
            )

        # 2. dinas_proposal_count (Approved + Rejected only)
        # Submission dibuat oleh user di dinas ini (CreatorID)
        proposal_reviewed_count = db.query(models.Submission).filter(
            models.Submission.CreatorID.in_(user_ids),
            or_(
                models.Submission.Status == models.SubmissionStatusEnum.Accepted,
                models.Submission.Status == models.SubmissionStatusEnum.Rejected
            )
        ).count()

        # 3. dinas_report_count (Total report dari user dinas ini)
        report_count = db.query(models.Report).filter(
            models.Report.UserID.in_(user_ids)
        ).count()

        # 4. dinas_proposal_monthly (Total proposal per bulan tahun ini)
        proposal_monthly_query = db.query(
            extract('month', models.Submission.created_at).label('month'),
            func.count(models.Submission.ID).label('total')
        ).filter(
            models.Submission.CreatorID.in_(user_ids),
            extract('year', models.Submission.created_at) == current_year
        ).group_by(
            extract('month', models.Submission.created_at)
        ).all()
        
        proposal_monthly, proposal_avg = StatService._fill_monthly_data(proposal_monthly_query)

        # 5. dinas_money_usage_monthly (Dari Report Approved tahun ini)
        money_monthly_query = db.query(
            extract('month', models.Report.Timestamp).label('month'),
            func.sum(models.Report.AmountRupiah).label('total')
        ).filter(
            models.Report.UserID.in_(user_ids),
            models.Report.Status == models.ReportStatusEnum.Accepted,
            extract('year', models.Report.Timestamp) == current_year
        ).group_by(
            extract('month', models.Report.Timestamp)
        ).all()

        money_monthly, money_avg = StatService._fill_monthly_data(money_monthly_query)

        return KadisStatResponse(
            dinas_proposal_count=proposal_reviewed_count,
            dinas_report_count=report_count,
            dinas_proposal_monthly=proposal_monthly,
            dinas_proposal_average=proposal_avg,
            dinas_money_usage_monthly=money_monthly,
            dinas_money_usage_average=money_avg
        )

    @staticmethod
    def get_admin_stats(db: Session, target_dinas_id: int) -> AdminStatResponse:
        current_year = datetime.now().year

        # Ambil User IDs dalam dinas target
        dinas_user_ids = db.query(models.User.ID).filter(models.User.DinasID == target_dinas_id).all()
        user_ids = [u.ID for u in dinas_user_ids]

        if not user_ids:
             empty_months = [MonthlyData(month=i, value=0) for i in range(12)]
             return AdminStatResponse(
                dinas_vehicle_count=0,
                dinas_users_count=0,
                dinas_report_pending_count=0,
                dinas_proposal_made_count=0,
                dinas_proposal_monthly=empty_months,
                dinas_proposal_average=0,
                dinas_money_usage_monthly=empty_months
             )

        # 1. dinas_vehicle_count
        # Hitung vehicle unik yg dimiliki user di dinas ini via tabel asosiasi
        # Perlu join: user_vehicle_association -> User
        # Karena kita sudah punya user_ids, kita bisa query langsung ke tabel asosiasi (jika dimapping)
        # Atau query via User.vehicles
        
        # Cara query many-to-many via association table secara raw/core SQLAlchemy:
        stmt = db.query(func.count(distinct(models.user_vehicle_association.c.vehicle_id)))\
                 .filter(models.user_vehicle_association.c.user_id.in_(user_ids))
        vehicle_count = stmt.scalar() or 0

        # 2. dinas_users_count
        users_count = len(user_ids)

        # 3. dinas_report_pending_count
        report_pending_count = db.query(models.Report).filter(
            models.Report.UserID.in_(user_ids),
            models.Report.Status == models.ReportStatusEnum.Pending
        ).count()

        # 4. dinas_proposal_made_count (Total semua submission yg dibuat)
        proposal_made_count = db.query(models.Submission).filter(
            models.Submission.CreatorID.in_(user_ids)
        ).count()

        # 5. dinas_proposal (Monthly submissions)
        proposal_monthly_query = db.query(
            extract('month', models.Submission.created_at).label('month'),
            func.count(models.Submission.ID).label('total')
        ).filter(
            models.Submission.CreatorID.in_(user_ids),
            extract('year', models.Submission.created_at) == current_year
        ).group_by(
            extract('month', models.Submission.created_at)
        ).all()
        
        proposal_monthly, proposal_avg = StatService._fill_monthly_data(proposal_monthly_query)

        # 6. dinas_money_usage (Monthly usage from Approved Reports)
        money_monthly_query = db.query(
            extract('month', models.Report.Timestamp).label('month'),
            func.sum(models.Report.AmountRupiah).label('total')
        ).filter(
            models.Report.UserID.in_(user_ids),
            models.Report.Status == models.ReportStatusEnum.Accepted,
            extract('year', models.Report.Timestamp) == current_year
        ).group_by(
            extract('month', models.Report.Timestamp)
        ).all()

        money_monthly, _ = StatService._fill_monthly_data(money_monthly_query)

        return AdminStatResponse(
            dinas_vehicle_count=vehicle_count,
            dinas_users_count=users_count,
            dinas_report_pending_count=report_pending_count,
            dinas_proposal_made_count=proposal_made_count,
            dinas_proposal_monthly=proposal_monthly,
            dinas_proposal_average=proposal_avg,
            dinas_money_usage_monthly=money_monthly
        )