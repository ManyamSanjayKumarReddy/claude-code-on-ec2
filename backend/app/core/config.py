from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    allowed_origins: str = "http://localhost:5173"
    database_url: str = "postgres://postgres:postgres@localhost:5432/postgres"
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
