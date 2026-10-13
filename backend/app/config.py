from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./avas.db"
    jwt_secret: str = "local-development-only-change-this-secret"
    access_token_minutes: int = 120
    environment: str = "development"
    frontend_origin: str = "http://localhost:5173"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
