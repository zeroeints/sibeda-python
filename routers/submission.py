# pyright: reportGeneralTypeIssues=false, reportUnknownMemberType=false
# type: ignore
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.database import SessionLocal
import controller.auth as auth
import schemas.schemas as schemas
from model.models import User as UserModel
from services.submission_service import SubmissionService
from i18n.messages import get_message

router = APIRouter(prefix="/submission", tags=["Submission"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=schemas.SuccessListResponse[schemas.SubmissionResponse])
def list_submissions(
    creator_id: int | None = None,
    receiver_id: int | None = None,
    vehicle_id: int | None = None,
    status: str | None = Query(None, description="Filter by status: Pending, Accepted, Rejected"),
    limit: int | None = Query(None, ge=1, le=1000, description="Limit jumlah data (max 1000)"),
    offset: int = Query(0, ge=0, description="Offset untuk pagination"),
    db: Session = Depends(get_db),
    _user: UserModel = Depends(auth.get_current_user),
) -> schemas.SuccessListResponse[schemas.SubmissionResponse]:
    """
    Mendapatkan semua submission dengan optional filtering dan pagination
    
    - **creator_id**: Filter berdasarkan ID pembuat
    - **receiver_id**: Filter berdasarkan ID penerima
    - **vehicle_id**: Filter berdasarkan ID kendaraan
    - **status**: Filter berdasarkan status (Pending, Accepted, Rejected)
    - **limit**: Batasi jumlah data yang dikembalikan
    - **offset**: Skip sejumlah data untuk pagination
    """
    data = SubmissionService.list(
        db, 
        creator_id=creator_id, 
        receiver_id=receiver_id, 
        vehicle_id=vehicle_id,
        status=status,
        limit=limit,
        offset=offset
    )
    return schemas.SuccessListResponse[schemas.SubmissionResponse](
        data=data, 
        message=f"Ditemukan {len(data)} submission"
    )


@router.get("/all/detailed", response_model=schemas.PaginatedResponse[schemas.SubmissionDetailResponse])
def list_all_submissions_detailed(
    creator_id: int | None = Query(None, description="Filter berdasarkan ID pembuat"),
    receiver_id: int | None = Query(None, description="Filter berdasarkan ID penerima"),
    vehicle_id: int | None = Query(None, description="Filter berdasarkan ID kendaraan"),
    status: str | None = Query(None, description="Filter by status: Pending, Accepted, Rejected"),
    limit: int | None = Query(100, ge=1, le=1000, description="Limit jumlah data (default 100, max 1000)"),
    offset: int = Query(0, ge=0, description="Offset untuk pagination"),
    db: Session = Depends(get_db),
    _user: UserModel = Depends(auth.get_current_user),
) -> schemas.PaginatedResponse[schemas.SubmissionDetailResponse]:
    """
    Mendapatkan semua submission dengan detail lengkap (nama creator, receiver, vehicle) dan pagination
    
    - **creator_id**: Filter berdasarkan ID pembuat
    - **receiver_id**: Filter berdasarkan ID penerima
    - **vehicle_id**: Filter berdasarkan ID kendaraan
    - **status**: Filter berdasarkan status (Pending, Accepted, Rejected)
    - **limit**: Batasi jumlah data yang dikembalikan (default 100)
    - **offset**: Skip sejumlah data untuk pagination
    
    Returns:
    - List submission dengan informasi lengkap creator, receiver, dan vehicle
    - Pagination info (total, limit, offset, has_more)
    """
    # Get total count
    total = SubmissionService.count_all(
        db,
        creator_id=creator_id,
        receiver_id=receiver_id,
        vehicle_id=vehicle_id,
        status=status
    )
    
    # Get data
    data = SubmissionService.list_all_detailed(
        db,
        creator_id=creator_id,
        receiver_id=receiver_id,
        vehicle_id=vehicle_id,
        status=status,
        limit=limit,
        offset=offset
    )
    
    # Calculate pagination info
    has_more = (offset + len(data)) < total
    
    return schemas.PaginatedResponse[schemas.SubmissionDetailResponse](
        data=data,
        message=f"Ditemukan {len(data)} dari {total} submission",
        pagination={
            "total": total,
            "limit": limit,
            "offset": offset,
            "returned": len(data),
            "has_more": has_more
        }
    )


@router.get("/{submission_id}", response_model=schemas.SuccessResponse[schemas.SubmissionResponse])
def get_submission(submission_id: int, db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.SubmissionResponse]:
    s = SubmissionService.get(db, submission_id)
    if not s:
        raise HTTPException(status_code=404, detail="Submission tidak ditemukan")
    return schemas.SuccessResponse[schemas.SubmissionResponse](data=s, message=get_message("create_success", None))


@router.post("/", response_model=schemas.SuccessResponse[schemas.SubmissionResponse])
def create_submission(payload: schemas.SubmissionCreate, db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.SubmissionResponse]:
    created = SubmissionService.create(db, payload)
    return schemas.SuccessResponse[schemas.SubmissionResponse](data=created, message=get_message("create_success", None))


@router.put("/{submission_id}", response_model=schemas.SuccessResponse[schemas.SubmissionResponse])
def update_submission(submission_id: int, payload: schemas.SubmissionUpdate, db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.SubmissionResponse]:
    updated = SubmissionService.update(db, submission_id, payload)
    return schemas.SuccessResponse[schemas.SubmissionResponse](data=updated, message=get_message("update_success", None))


@router.delete("/{submission_id}", response_model=schemas.SuccessResponse[schemas.Message])
def delete_submission(submission_id: int, db: Session = Depends(get_db), _user: UserModel = Depends(auth.get_current_user)) -> schemas.SuccessResponse[schemas.Message]:
    SubmissionService.delete(db, submission_id)
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="Submission dihapus"), message=get_message("delete_success", None))


@router.get("/monthly/summary", response_model=schemas.SuccessResponse[schemas.SubmissionSummary])
def get_monthly_summary(
    month: int = Query(..., ge=1, le=12, description="Bulan (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Tahun"),
    db: Session = Depends(get_db),
    _user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.SubmissionSummary]:
    """
    Mendapatkan ringkasan pengajuan penggunaan dana per bulan
    
    - **month**: Bulan yang ingin ditampilkan (1-12)
    - **year**: Tahun yang ingin ditampilkan
    
    Returns:
    - Total pengajuan
    - Jumlah pengajuan berdasarkan status (Pending, Accepted, Rejected)
    - Total dana yang diajukan
    - Total dana berdasarkan status
    """
    summary = SubmissionService.get_monthly_summary(db, month, year)
    return schemas.SuccessResponse[schemas.SubmissionSummary](
        data=summary, 
        message=f"Ringkasan pengajuan bulan {month}/{year}"
    )


@router.get("/monthly/details", response_model=schemas.SuccessListResponse[schemas.SubmissionDetailResponse])
def get_monthly_details(
    month: int = Query(..., ge=1, le=12, description="Bulan (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Tahun"),
    db: Session = Depends(get_db),
    _user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessListResponse[schemas.SubmissionDetailResponse]:
    """
    Mendapatkan detail lengkap pengajuan penggunaan dana per bulan
    
    - **month**: Bulan yang ingin ditampilkan (1-12)
    - **year**: Tahun yang ingin ditampilkan
    
    Returns:
    - List detail pengajuan dengan informasi creator, receiver, dan vehicle
    """
    details = SubmissionService.get_monthly_details(db, month, year)
    return schemas.SuccessListResponse[schemas.SubmissionDetailResponse](
        data=details,
        message=f"Detail pengajuan bulan {month}/{year}"
    )


@router.get("/monthly/report", response_model=schemas.SuccessResponse[schemas.SubmissionMonthlyReport])
def get_monthly_report(
    month: int = Query(..., ge=1, le=12, description="Bulan (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Tahun"),
    db: Session = Depends(get_db),
    _user: UserModel = Depends(auth.get_current_user)
) -> schemas.SuccessResponse[schemas.SubmissionMonthlyReport]:
    """
    Mendapatkan laporan lengkap pengajuan penggunaan dana per bulan (ringkasan + detail)
    
    - **month**: Bulan yang ingin ditampilkan (1-12)
    - **year**: Tahun yang ingin ditampilkan
    
    Returns:
    - Summary: Ringkasan statistik pengajuan
    - Details: List detail lengkap setiap pengajuan
    """
    summary = SubmissionService.get_monthly_summary(db, month, year)
    details = SubmissionService.get_monthly_details(db, month, year)
    
    report = schemas.SubmissionMonthlyReport(
        summary=summary,
        details=details
    )
    
    return schemas.SuccessResponse[schemas.SubmissionMonthlyReport](
        data=report,
        message=f"Laporan lengkap pengajuan bulan {month}/{year}"
    )
