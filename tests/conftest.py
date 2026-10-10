"""Keep pytest isolated from any DATABASE_URL in a developer's .env file."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("ENABLE_SCHEDULER", "false")
os.environ.setdefault("SECRET_KEY", "test-secret-key-is-not-used-outside-this-process")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
