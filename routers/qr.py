from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database.database import SessionLocal
import controller.auth as auth
import schemas.schemas as schemas
import model.models as models
from utils.otp import get_or_create_qr_code, verify_qr_code, consume_qr_code, encode_qr_token, decode_qr_token, extract_kode_unik_from_qr
from utils.responses import detect_lang
from i18n.messages import get_message

router = APIRouter(prefix="/qr", tags=["QR"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/my", response_model=schemas.SuccessResponse[schemas.QRGetResponse])
def get_my_qr(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    lang = detect_lang(request)
    # Jika user sudah punya Dinas -> sudah scan
    if getattr(current_user, "DinasID", None):
        return schemas.SuccessResponse[schemas.QRGetResponse](data=schemas.QRGetResponse(code=None, expiresAt=None), message=get_message("user_already_has_dinas", lang))
    rec = get_or_create_qr_code(db, current_user)
    # Kembalikan kode unik yang bisa ditampilkan sebagai QR
    code_val = getattr(rec, "KodeUnik", None)
    detail = str(code_val) if code_val is not None else ""
    # Try to include expiry if available
    exp = getattr(rec, "expired_at", None)
    exp_str = exp.isoformat() if (exp is not None and hasattr(exp, "isoformat")) else None
    # Also provide a signed token for safer transport
    token = encode_qr_token(current_user, detail) if detail else None
    return schemas.SuccessResponse[schemas.QRGetResponse](data=schemas.QRGetResponse(code=token or detail, expiresAt=exp_str), message=get_message("qr_ready", lang))

@router.post("/assign", response_model=schemas.SuccessResponse[schemas.Message])
def assign_dinas_with_qr(payload: schemas.QRAssignRequest, request: Request, db: Session = Depends(get_db)):
    lang = detect_lang(request)
    # Temukan user yang akan di-assign berdasarkan NIP
    user = db.query(models.User).filter(models.User.NIP == payload.NIP).first()
    if not user:
        raise HTTPException(status_code=404, detail=get_message("user_not_found", lang))
    # Jika user sudah punya Dinas, anggap sudah scan
    if getattr(user, "DinasID", None):
        return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="already_scanned"), message=get_message("user_already_has_dinas", lang))
    # Pastikan Dinas ada
    dinas = db.query(models.Dinas).filter(models.Dinas.ID == payload.DinasID).first()
    if not dinas:
        raise HTTPException(status_code=404, detail=get_message("dinas_not_found", lang))
    # Terima raw code atau signed token
    raw_code = payload.UniqueCode
    if "." in raw_code:  # kemungkinan token bertanda tangan
        ok_tok, _reason_tok, uid_tok, code_tok = decode_qr_token(raw_code)
        uid_user = int(getattr(user, "ID", 0))
        if not ok_tok or uid_tok != uid_user or not code_tok:
            raise HTTPException(status_code=400, detail=get_message("qr_invalid", lang))
        raw_code = code_tok
    # Verifikasi kode QR
    ok, reason = verify_qr_code(db, user, raw_code)
    if not ok:
        key = "invalid_or_expired"
        if reason == "invalid":
            key = "invalid"
        elif reason == "expired":
            key = "expired"
        raise HTTPException(status_code=400, detail=get_message(f"qr_{key}", lang))
    # Set Dinas ke user
    setattr(user, "DinasID", int(payload.DinasID))
    db.add(user)
    # Konsumsi kode agar tidak bisa dipakai lagi
    consume_qr_code(db, user, raw_code)
    db.commit()
    return schemas.SuccessResponse[schemas.Message](data=schemas.Message(detail="assigned"), message=get_message("dinas_assigned", lang))


@router.post("/scan")
def scan_qr_code(payload: schemas.QRScanRequest, request: Request, db: Session = Depends(get_db)):
   
    lang = detect_lang(request)
    
    try:
        # Extract kode unik dari input (handle signed token & raw code)
        raw_code = extract_kode_unik_from_qr(payload.kode_unik)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Cari kode unik di database
    qr_record = db.query(models.UniqueCodeGenerator).filter(
        models.UniqueCodeGenerator.KodeUnik == raw_code
    ).first()
    
    if not qr_record:
        raise HTTPException(status_code=404, detail=get_message("not_found", lang))
    
    # Ambil data user
    user = db.query(models.User).filter(models.User.ID == qr_record.UserID).first()
    
    if not user:
        raise HTTPException(status_code=404, detail=get_message("user_not_found", lang))
    
    # Convert ke UserResponse
    user_data = schemas.UserResponse.model_validate(user)
    
    # Return data user
    return schemas.SuccessResponse[schemas.UserResponse](
        data=user_data,
        message=get_message("qr_ready", lang)
    )

