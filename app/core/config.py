"""OWNER: M1 - environment settings (read from .env)"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "CareerTrack"
    DATABASE_URL: str = "sqlite:///./careertrack.db"   # use postgresql://... in production
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # first admin account, created on startup when both are set
    ADMIN_NAME: str = "Admin"
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""

    CORS_ORIGINS: str = "*"                 # comma separated list, e.g. http://localhost:3000,http://localhost:8501
    ENABLE_SCHEDULER: bool = True           # job expiry (M1) + reminders (M2)
    SEED_DEFAULT_SKILLS: bool = True        # fill the skills table on first start

    LLM_API_KEY: str = ""                   # M3: optional AI features
    LLM_MODEL: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_list(self) -> list:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()] or ["*"]


settings = Settings()
