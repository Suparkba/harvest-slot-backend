from functools import lru_cache
from typing import Any

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "harvest-slot-backend"
    api_v1_prefix: str = "/api/v1"
    debug: bool | str = True
    testing: bool = False

    database_host: str = "localhost"
    database_port: int = 3306
    database_user: str = "root"
    database_password: str = "your-password"
    database_name: str = "harvest_slot_db"
    database_charset: str = "utf8mb4"

    jwt_secret_key: str = "change-this-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
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
    dl_quality_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("DL_QUALITY_ANALYSIS_ENABLED", "DL_QUALITY_ENABLED"),
    )
    dl_quality_api_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DL_API_BASE_URL", "DL_QUALITY_API_URL"),
    )
    dl_quality_timeout_seconds: int = Field(
        default=10,
        validation_alias=AliasChoices("DL_API_TIMEOUT_SECONDS", "DL_QUALITY_TIMEOUT_SECONDS"),
    )
    kma_asos_service_key: str | None = None
    kma_asos_base_url: str = "http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"
    kma_default_stn_id: str = "136"
    kma_asos_timeout_seconds: int = 20

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
