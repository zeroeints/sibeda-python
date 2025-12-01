from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid
from fastapi import UploadFile, HTTPException

# Konfigurasi
ASSETS_DIR = Path("assets")
REPORTS_DIR = ASSETS_DIR / "reports"
VEHICLES_DIR = ASSETS_DIR / "vehicles"

# Allowed image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_image_file(file: UploadFile) -> None:
    """Validasi file gambar"""
    # Check extension
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check content type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )

def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename dengan timestamp dan UUID"""
    file_ext = Path(original_filename).suffix.lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}{file_ext}"

async def save_upload_file(
    upload_file: UploadFile,
    destination_dir: Path,
    max_size: int = MAX_FILE_SIZE
) -> str:
    """
    Save uploaded file dan return relative path
    
    Args:
        upload_file: File yang diupload
        destination_dir: Directory tujuan (relative to project root)
        max_size: Maximum file size in bytes
    
    Returns:
        Relative path to saved file (e.g., "assets/reports/20251127_abc123.jpg")
    """
    # Validate
    validate_image_file(upload_file)
    
    # Check file size
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    
    # Create destination directory if not exists
    destination_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    if not upload_file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    unique_filename = generate_unique_filename(upload_file.filename)
    file_path = destination_dir / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            while chunk := await upload_file.read(chunk_size):
                file_size += len(chunk)
                if file_size > max_size:
                    # Remove partial file
                    buffer.close()
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Maximum size: {max_size / (1024*1024):.0f}MB"
                    )
                buffer.write(chunk)
    except Exception as e:
        # Cleanup on error
        file_path.unlink(missing_ok=True)
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    finally:
        await upload_file.close()
    
    # Return relative path (for database storage)
    return str(file_path).replace("\\", "/")

async def save_report_photo(
    upload_file: Optional[UploadFile],
    photo_type: str
) -> Optional[str]:
    """
    Save report photo (vehicle, odometer, invoice, mypertamina)
    
    Args:
        upload_file: Uploaded file or None
        photo_type: Type of photo (vehicle, odometer, invoice, mypertamina)
    
    Returns:
        Relative path to saved file or None
    """
    if not upload_file or not upload_file.filename:
        return None
    
    # Create subdirectory for photo type
    destination = REPORTS_DIR / photo_type
    return await save_upload_file(upload_file, destination)

async def save_vehicle_photo(upload_file: Optional[UploadFile]) -> Optional[str]:
    """
    Save vehicle photo
    
    Args:
        upload_file: Uploaded file or None
    
    Returns:
        Relative path to saved file or None
    """
    if not upload_file or not upload_file.filename:
        return None
    
    return await save_upload_file(upload_file, VEHICLES_DIR)

def delete_file(file_path: Optional[str]) -> None:
    """Delete file from filesystem"""
    if not file_path:
        return
    
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
    except Exception:
        # Silently fail - file might already be deleted
        pass

def get_file_url(file_path: Optional[str], base_url: str = "") -> Optional[str]:
    """
    Convert file path to accessible URL
    
    Args:
        file_path: Relative file path (e.g., "assets/reports/photo.jpg")
        base_url: Base URL (e.g., "http://localhost:8000")
    
    Returns:
        Full URL to file or None
    """
    if not file_path:
        return None
    
    # Remove leading slash if exists
    clean_path = file_path.lstrip("/")
    
    if base_url:
        return f"{base_url}/{clean_path}"
    
    return f"/{clean_path}"
