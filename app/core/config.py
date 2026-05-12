from pydantic_settings import BaseSettings, SettingsConfigDict


class ApifuseSettings(BaseSettings):
    """Application settings loaded from environment variables and optional .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "apifuse"
    app_version: str = "0.1.0"

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"


apifuse_settings = ApifuseSettings()
