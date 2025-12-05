from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from config import get_settings

# Load settings
settings = get_settings()

# Create Database Engine
# echo=True jika debug aktif, berguna untuk melihat raw SQL query
engine = create_engine(settings.database_url, echo=settings.debug)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()