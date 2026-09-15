from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "CrediLens AI"
    app_version: str = "1.0.0"
    environment_name: str = "development"
    backend_port: int = 8000
    backend_cors_origins: str = "http://localhost:3000"
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_timeout_seconds: float = 8.0
    artifact_directory: Path = REPOSITORY_ROOT / "ml" / "artifacts"
    artifact_loading_required: bool = True
    preprocessing_mode: str = "separate"
    model_filename: str = "model.pkl"
    artifact_format: str = "portable"
    portable_manifest_filename: str = "portable/manifest.json"
    model_metadata_filename: str = "model_metadata.json"
    feature_metadata_filename: str = "feature_metadata.json"
    preprocessing_filename: str = "preprocessing_pipeline.joblib"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
