from functools import lru_cache
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Harvest Slot API"
    api_v1_prefix: str = "/api/v1"
    debug: bool | str = True
    testing: bool = False

    database_host: str = "your-db-host"
    database_port: int = 3306
    database_user: str = "your-db-user"
    database_password: str = "your-db-password"
    database_name: str = "harvest_slot_db"
    database_charset: str = "utf8mb4"

    jwt_secret_key: str = "change-this-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_allowed_origins: str | list[str] = "*"
    email_verification_required: bool = True
    email_verification_expire_minutes: int = 5
    email_verification_resend_cooldown_seconds: int = 60
    email_verification_max_attempts: int = 5
    email_dev_mode: bool = True
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool = True
    image_upload_url: str = "https://cheng80.myqnapcloud.com/upload_image.php"
    image_upload_timeout_seconds: int = 20
    image_default_product_subfolder: str = "products"
    image_default_quality_subfolder: str = "quality-inspections"
    image_allowed_extensions: str | list[str] = "jpg,jpeg,png,gif,webp"
    image_max_size_mb: int = 5
    dl_quality_enabled: bool = False
    dl_quality_api_url: str = ""
    dl_quality_timeout_seconds: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
            f"?charset={self.database_charset}"
        )

    @property
    def cors_origins(self) -> list[str]:
        raw_value: Any = self.cors_allowed_origins
        if isinstance(raw_value, list):
            return raw_value or ["*"]
        if not raw_value:
            return ["*"]
        if raw_value == "*":
            return ["*"]
        return [origin.strip() for origin in str(raw_value).split(",") if origin.strip()]

    @property
    def allowed_image_extensions(self) -> set[str]:
        raw_value: Any = self.image_allowed_extensions
        if isinstance(raw_value, list):
            values = raw_value
        else:
            values = str(raw_value).split(",")
        return {value.strip().lower() for value in values if value.strip()}

    @property
    def image_api_base_url(self) -> str:
        return self.image_upload_url

    @property
    def image_api_timeout_seconds(self) -> int:
        return self.image_upload_timeout_seconds


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
