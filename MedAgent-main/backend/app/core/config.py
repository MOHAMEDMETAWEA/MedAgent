from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        extra="ignore",
    )

    # App
    ENV: str = "local"
    VERSION: str = "0.1.0"
    COMMIT_SHA: str = "unknown"
    SECRET_KEY: str = "change-me-in-production"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    FRONTEND_URL: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://hossamhassan@localhost:5432/medagent"

    # Redis
    REDIS_URL: str | None = None

    # JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security
    MAX_LOGIN_ATTEMPTS: int = 10
    ACCOUNT_LOCKOUT_MINUTES: int = 30
    DISABLE_RATE_LIMIT: bool = False

    # Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_ADDRESS: str = "ai@hossam7asan.com"
    EMAILS_FROM_NAME: str = "MedAgent"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Notifications scheduler
    NOTIFICATION_POLL_INTERVAL_SECONDS: int = 60

    # ── LLM / AI ──────────────────────────────────────────
    LLM_PROVIDER: str = "openai_compat"
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "qwen/qwen-2.5-72b-instruct"

    # Optional cheaper / faster model for verification / safety checks
    VERIFIER_MODEL: str | None = None

    # Vision analysis (OpenAI-compatible vision endpoint)
    VISION_PROVIDER: str = "openai_compat"
    VISION_MODEL: str | None = None

    # ── PHI Encryption ────────────────────────────────────
    PHI_ENCRYPTION_ENABLED: bool = False
    DATA_ENCRYPTION_KEY: str | None = None

    # ── Observability ─────────────────────────────────────
    SENTRY_DSN: str | None = None
    MLFLOW_TRACKING_URI: str | None = None

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"

    def model_post_init(self, __context: object) -> None:
        """Fail fast in production if critical secrets are missing."""
        if self.is_production:
            if not self.SECRET_KEY or self.SECRET_KEY == "change-me-in-production":
                raise ValueError("SECRET_KEY must be set in production")
            if self.PHI_ENCRYPTION_ENABLED and not self.DATA_ENCRYPTION_KEY:
                raise ValueError("DATA_ENCRYPTION_KEY is required when PHI_ENCRYPTION_ENABLED=true")


settings = Settings()
