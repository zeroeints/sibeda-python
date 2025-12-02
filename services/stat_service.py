from sqlalchemy.orm import Session
from sqlalchemy import func, extract, distinct, or_
from datetime import datetime
import model.models as models
from schemas.schemas import (
    PicStatResponse, MonthlyData, 
    KadisStatResponse, AdminStatResponse
)

class StatService:
    @staticmethod
    def get_pic_stats(db: Session, user_id: int) -> PicStatResponse:
        current_year = datetime.now().year
        
        user = db.query(models.User).filter(models.User.id == user_id).first()
        vehicle_count = len(user.vehicles) if user else 0
        
        report_count = db.query(models.Report).filter(models.Report.user_id == user_id).count()
        
        usage_query = db.query(
            extract('month', models.Report.timestamp).label('month'),
            func.sum(models.Report.amount_rupiah).label('total')
        ).filter(
            models.Report.user_id == user_id,
            models.Report.status == models.ReportStatusEnum.accepted,
            extract('year', models.Report.timestamp) == current_year
        ).group_by(
            extract('month', models.Report.timestamp)
        ).all()
        
        usage_map = {row.month: float(row.total) for row in usage_query}
        
        money_usage_list = []
        total_year = 0.0
        
        for i in range(1, 13):
            val = usage_map.get(i, 0.0)
            money_usage_list.append(MonthlyData(month=i-1, value=val))
            total_year += val
            
        average = total_year / 12 if total_year > 0 else 0.0
        
        return PicStatResponse(
            vehicle_count=vehicle_count,
            report_count=report_count,
            money_usage=money_usage_list,
            average=average
        )

    @staticmethod
    def _fill_monthly_data(query_result, year_avg_divisor=12) -> tuple[list[MonthlyData], float]:
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
        
        dinas_user_ids = db.query(models.User.id).filter(models.User.dinas_id == user_dinas_id).all()
        user_ids = [u.id for u in dinas_user_ids]
        
        if not user_ids:
            empty_months = [MonthlyData(month=i, value=0) for i in range(12)]
            return KadisStatResponse(
                dinas_proposal_count=0,
                dinas_report_count=0,
                dinas_proposal_monthly=empty_months,
                dinas_proposal_average=0,
                dinas_money_usage_monthly=empty_months,
                dinas_money_usage_average=0
            )

        proposal_reviewed_count = db.query(models.Submission).filter(
            models.Submission.creator_id.in_(user_ids),
            or_(
                models.Submission.status == models.SubmissionStatusEnum.accepted,
                models.Submission.status == models.SubmissionStatusEnum.rejected
            )
        ).count()

        report_count = db.query(models.Report).filter(
            models.Report.user_id.in_(user_ids)
        ).count()

        proposal_monthly_query = db.query(
            extract('month', models.Submission.created_at).label('month'),
            func.count(models.Submission.id).label('total')
        ).filter(
            models.Submission.creator_id.in_(user_ids),
            extract('year', models.Submission.created_at) == current_year
        ).group_by(
            extract('month', models.Submission.created_at)
        ).all()
        
        proposal_monthly, proposal_avg = StatService._fill_monthly_data(proposal_monthly_query)

        money_monthly_query = db.query(
            extract('month', models.Report.timestamp).label('month'),
            func.sum(models.Report.amount_rupiah).label('total')
        ).filter(
            models.Report.user_id.in_(user_ids),
            models.Report.status == models.ReportStatusEnum.accepted,
            extract('year', models.Report.timestamp) == current_year
        ).group_by(
            extract('month', models.Report.timestamp)
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

        dinas_user_ids = db.query(models.User.id).filter(models.User.dinas_id == target_dinas_id).all()
        user_ids = [u.id for u in dinas_user_ids]

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

        stmt = db.query(func.count(distinct(models.user_vehicle_association.c.vehicle_id)))\
                 .filter(models.user_vehicle_association.c.user_id.in_(user_ids))
        vehicle_count = stmt.scalar() or 0

        users_count = len(user_ids)

        report_pending_count = db.query(models.Report).filter(
            models.Report.user_id.in_(user_ids),
            models.Report.status == models.ReportStatusEnum.pending
        ).count()

        proposal_made_count = db.query(models.Submission).filter(
            models.Submission.creator_id.in_(user_ids)
        ).count()

        proposal_monthly_query = db.query(
            extract('month', models.Submission.created_at).label('month'),
            func.count(models.Submission.id).label('total')
        ).filter(
            models.Submission.creator_id.in_(user_ids),
            extract('year', models.Submission.created_at) == current_year
        ).group_by(
            extract('month', models.Submission.created_at)
        ).all()
        
        proposal_monthly, proposal_avg = StatService._fill_monthly_data(proposal_monthly_query)

        money_monthly_query = db.query(
            extract('month', models.Report.timestamp).label('month'),
            func.sum(models.Report.amount_rupiah).label('total')
        ).filter(
            models.Report.user_id.in_(user_ids),
            models.Report.status == models.ReportStatusEnum.accepted,
            extract('year', models.Report.timestamp) == current_year
        ).group_by(
            extract('month', models.Report.timestamp)
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