from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/pharma_ops"
    jwt_secret_key: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    groq_api_key: str = "mock_key_for_local_dev"
    groq_model: str = "llama-3.1-8b-instant"
    groq_timeout_seconds: float = 8.0
    inventory_service_url: str = "http://127.0.0.1:8001"
    inventory_service_timeout_seconds: float = 5.0
    billing_service_url: str = "http://127.0.0.1:8003"
    sync_sqlite_path: str = "services/sync-service/data/sync_operations.db"
    sync_replay_timeout_seconds: float = 5.0

    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
