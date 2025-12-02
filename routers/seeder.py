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
        # 1. Pastikan root directory ada di sys.path
        current_dir = os.path.dirname(os.path.abspath(__file__))  # path ke /routers
        root_dir = os.path.dirname(current_dir)  # path ke root project

        if root_dir not in sys.path:
            sys.path.append(root_dir)

        # 2. Import module seeder yang BARU (db_seeder.py)
        # Pastikan Anda sudah merename 'seeder.py' di root menjadi 'db_seeder.py'
        import db_seeder 

        # 3. Jalankan fungsi seeding
        logger.info("Memicu seeding dari API...")
        db_seeder.seed_database() # Panggil fungsi dari file baru

        return {
            "success": True,
            "message": "Database berhasil di-seed dengan data dummy!",
            "credentials_info": {
                "password_all_users": "11111111",
                "accounts": [
                    {"role": "Admin", "email": "admin@sibeda.local", "NIP": "100000000000000001"},
                    {"role": "Kadis", "email": "budi@sibeda.local", "NIP": "100000000000000002"},
                    {"role": "PIC", "email": "andi@sibeda.local", "NIP": "100000000000000003"},
                ],
            },
        }

    except ImportError as e:
        logger.error(f"Import Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="File 'db_seeder.py' tidak ditemukan. Pastikan Anda sudah me-rename 'seeder.py' menjadi 'db_seeder.py'.",
        )
    except Exception as e:
        logger.error(f"Seeding failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gagal melakukan seeding: {str(e)}")