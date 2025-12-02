from __future__ import annotations

import logging
import os
import sys

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/seeder", tags=["System Utility"])
logger = logging.getLogger(__name__)


@router.post(
    "/run",
    summary="Run Database Seeder",
    description="Menjalankan script seeding database untuk mengisi data dummy.",
)
def run_database_seeder():
    """
    Endpoint untuk memicu proses seeding database.
    Berguna untuk development/testing via Postman.
    """
    try:
        # 1. Pastikan root directory ada di sys.path agar bisa import 'seed.py'
        current_dir = os.path.dirname(os.path.abspath(__file__))  # path ke /routers
        root_dir = os.path.dirname(current_dir)  # path ke root project

        if root_dir not in sys.path:
            sys.path.append(root_dir)

        # 2. Import module seed secara dinamis
        # (Kita import di sini agar tidak error jika file seed.py belum ada saat server start)
        import seeder

        # 3. Jalankan fungsi seeding
        logger.info("Memicu seeding dari API...")
        seeder.seed_database()

        return {
            "success": True,
            "message": "Database berhasil di-seed dengan data dummy!",
            "credentials_info": {
                "password_all_users": "11111111",
                "accounts": [
                    {"role": "Admin", "email": "admin@sibeda.local"},
                    {"role": "Kadis", "email": "budi@sibeda.local"},
                    {"role": "PIC", "email": "andi@sibeda.local"},
                ],
            },
        }

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="File 'seeder.py' tidak ditemukan di root directory. Pastikan file tersebut ada.",
        )
    except Exception as e:
        logger.error(f"Seeding failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gagal melakukan seeding: {str(e)}")