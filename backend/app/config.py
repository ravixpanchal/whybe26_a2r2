from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "CrediLens AI"
    backend_port: int = 8000
    backend_cors_origins: str = "http://localhost:3000"
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
