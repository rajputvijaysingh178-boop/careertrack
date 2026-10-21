"""Keep pytest isolated from developer and deployment environment settings."""
import os

# Force safe test-only settings before any application module creates its engine.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["ENABLE_SCHEDULER"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key-is-not-used-outside-this-process"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000"
