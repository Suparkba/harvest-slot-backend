from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Harvest Slot API"
    api_v1_prefix: str = "/api/v1"
    debug: bool | str = True

    database_host: str = "your-db-host"
    database_port: int = 3306
    database_user: str = "your-db-user"
    database_password: str = "your-db-password"
    database_name: str = "harvest_slot_db"
    database_charset: str = "utf8mb4"

    jwt_secret_key: str = "change-this-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
