from pydantic import BaseModel
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()
from functools import lru_cache

class Settings(BaseModel):
    app_name: str
    debug: bool
    environment: str
    database_url: str
    secret_key: str
    access_token_expire_minutes: int
    log_level: str
    request_id_header: str = "X-Request-ID"

    @staticmethod
    def load() -> "Settings":
        return Settings(
            app_name=os.getenv("APP_NAME", "SIBEDA API"),
            debug=os.getenv("DEBUG", "true").lower() == "true",
            environment=os.getenv("ENVIRONMENT", "development"),
            database_url=os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/sibeda_db"),
            secret_key=os.getenv("SECRET_KEY", "dev_insecure_change_me"),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            request_id_header=os.getenv("REQUEST_ID_HEADER", "X-Request-ID"),
        )

@lru_cache
def get_settings() -> Settings:
    return Settings.load()
