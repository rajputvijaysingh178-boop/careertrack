"""OWNER: M1 - environment settings (read from .env)"""
from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "CareerTrack"
    DATABASE_URL: str = "sqlite:///./careertrack.db"
    SECRET_KEY: str = Field(default="change-me", validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET"))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # first admin account, created on startup when both are set
    ADMIN_NAME: str = "Admin"
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""

    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    ENABLE_SCHEDULER: bool = True           # job expiry (M1) + reminders (M2)
    SEED_DEFAULT_SKILLS: bool = True        # fill the skills table on first start
    AUTO_CREATE_SCHEMA: bool | None = None  # default: SQLite only; PostgreSQL uses reviewed migrations
    MATERIAL_UPLOAD_DIR: str = "uploads/materials"
    MAX_MATERIAL_UPLOAD_BYTES: int = 10 * 1024 * 1024

    LLM_API_KEY: str = ""                   # M3: optional AI features
    LLM_MODEL: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    @model_validator(mode="after")
    def require_secure_postgres_secret(self):
        postgres = self.DATABASE_URL.startswith(("postgres://", "postgresql://", "postgresql+"))
        placeholders = {"", "change-me", "change-me-to-a-long-random-string"}
        is_placeholder = self.SECRET_KEY.strip().lower().startswith(("change_me", "change-me", "replace_me", "replace-me"))
        if postgres and (self.SECRET_KEY in placeholders or is_placeholder or len(self.SECRET_KEY) < 32):
            raise ValueError("Set SECRET_KEY (or legacy JWT_SECRET) to a random value of at least 32 characters for PostgreSQL")
        admin_configured = bool(self.ADMIN_EMAIL or self.ADMIN_PASSWORD)
        admin_password_placeholder = self.ADMIN_PASSWORD.strip().lower().startswith(
            ("change_me", "change-me", "replace_me", "replace-me"))
        if postgres and admin_configured and (not self.ADMIN_EMAIL or len(self.ADMIN_PASSWORD) < 12
                                               or admin_password_placeholder):
            raise ValueError("When bootstrapping an admin on PostgreSQL, set both ADMIN_EMAIL and a non-placeholder ADMIN_PASSWORD of at least 12 characters")
        return self

    @property
    def sqlalchemy_database_url(self) -> str:
        """Use the installed psycopg 3 driver for standard Neon PostgreSQL URLs."""
        if self.DATABASE_URL.startswith("postgres://"):
            return "postgresql+psycopg://" + self.DATABASE_URL[len("postgres://"):]
        if self.DATABASE_URL.startswith("postgresql://"):
            return "postgresql+psycopg://" + self.DATABASE_URL[len("postgresql://"):]
        return self.DATABASE_URL

    @property
    def should_auto_create_schema(self) -> bool:
        if self.AUTO_CREATE_SCHEMA is not None:
            return self.AUTO_CREATE_SCHEMA
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def cors_list(self) -> list:
        return [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
