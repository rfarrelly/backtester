from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")

    database_url: str = Field(alias="DATABASE_URL")
    secret_key: str = Field(default="dev_secret_key", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(
        default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


settings = Settings()
