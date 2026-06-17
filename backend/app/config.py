from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "Controle Almoxarifado"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = f"sqlite:///{Path(__file__).parent.parent / 'data' / 'almoxarifado.db'}"
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    USP_DIGITAL_BASE_URL: str = "https://uspdigital.usp.br/administrativo"
    USP_DIGITAL_LOGIN_URL: str = "https://uspdigital.usp.br/wsusuario"
    USP_DIGITAL_TIMEOUT: int = 30

    DATA_DIR: Path = Path(__file__).parent.parent / "data"
    REPORTS_DIR: Path = Path(__file__).parent.parent / "data" / "reports"
    UPLOAD_DIR: Path = Path(__file__).parent.parent / "data" / "uploads"

    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024

    BROWSER_HEADLESS: bool = True
    BROWSER_TIMEOUT: int = 30000

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:8000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
