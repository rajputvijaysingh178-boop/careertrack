"""OWNER: M1"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "CareerTrack"
    DATABASE_URL: str = "sqlite:///./careertrack.db"   # use postgresql://... in production
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    LLM_API_KEY: str = ""        # M3: optional, for AI features
    LLM_MODEL: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
