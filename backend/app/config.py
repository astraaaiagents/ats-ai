from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "ATS AI API"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ats_ai"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440
    jwt_refresh_expiration_days: int = 30

    s3_bucket: str = "ats-ai-uploads"
    s3_region: str = "us-east-1"
    s3_access_key: str = ""
    s3_secret_key: str = ""

    cors_origins: list[str] = ["*"]

    rate_limit_tenant_per_minute: int = 1000
    rate_limit_user_per_minute: int = 200
    rate_limit_burst_per_second: int = 50


settings = Settings()
