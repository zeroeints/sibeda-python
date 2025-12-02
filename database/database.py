from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from config import get_settings

# Load settings
settings = get_settings()

# Create Database Engine
# echo=True jika debug aktif, berguna untuk melihat raw SQL query
engine = create_engine(settings.database_url, echo=settings.debug)

# Create Session Factory
# autocommit=False & autoflush=False adalah standar untuk kontrol transaksi manual
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk ORM Models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency Injection untuk Database Session.
    Membuat session baru untuk setiap request dan menutupnya setelah request selesai.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()