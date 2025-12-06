from pydantic import BaseModel
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    app_name: str
    debug: bool
    environment: str
    database_url: str
    secret_key: str
    access_token_expire_minutes: int
    log_level: str
    request_id_header: str = "X-Request-ID"
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_tls: bool = True
    mail_from: str | None = None
    mail_from_name: str | None = None

    @staticmethod
    def load() -> "Settings":
        
        secret_key = os.getenv("SECRET_KEY")
        environment = os.getenv("ENVIRONMENT", "development")
        
        if not secret_key:
            if environment == "production":
                raise ValueError("SECRET_KEY environment variable is required in production!")
            
            import warnings
            warnings.warn("SECRET_KEY not set! Using insecure default. Set SECRET_KEY in .env for production.")
            secret_key = "dev_insecure_key_not_for_production"
        
        return Settings(
            app_name=os.getenv("APP_NAME", "SIBEDA API"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            environment=environment,
            database_url=os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/sibeda_db"),
            secret_key=secret_key,
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            request_id_header=os.getenv("REQUEST_ID_HEADER", "X-Request-ID"),
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_HOST") else None,
            smtp_user=os.getenv("SMTP_USER"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            smtp_tls=os.getenv("SMTP_TLS", "true").lower() == "true",
            mail_from=os.getenv("MAIL_FROM"),
            mail_from_name=os.getenv("MAIL_FROM_NAME"),
        )

@lru_cache
def get_settings() -> Settings:
    return Settings.load()
