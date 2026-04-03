from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/pharma_ops"
    jwt_secret_key: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    groq_api_key: str = "mock_key_for_local_dev"
    inventory_service_url: str = "http://127.0.0.1:8001"
    inventory_service_timeout_seconds: float = 5.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
