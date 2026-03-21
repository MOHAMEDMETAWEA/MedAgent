import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Global settings for MedAgent system."""

    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    JWT_SECRET_KEY: Optional[str] = None
    CLERK_PUBLISHABLE_KEY: Optional[str] = None
    CLERK_SECRET_KEY: Optional[str] = None

    # Paths
    BASE_DIR: Path = Path(__file__).parent
    PROMPTS_DIR: Path = BASE_DIR / "prompts"
    DATA_DIR: Path = BASE_DIR / "data"
    RAG_DIR: Path = BASE_DIR / "rag"
    INDEX_DIR: Path = RAG_DIR / "faiss_index"

    # Medical Data
    MEDICAL_GUIDELINES_PATH: Path = DATA_DIR / "medical_guidelines.json"

    # RAG Configuration
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 3
    RAG_RELEVANCE_THRESHOLD: float = 0.5  # Increased for safety

    # LLM Configuration
    LLM_TEMPERATURE_DIAGNOSIS: float = 0.0  # Strict for reasoning
    LLM_TEMPERATURE_REASONING: float = 0.2  # Balanced for CoT
    LLM_TEMPERATURE_PATIENT: float = 0.3
    LLM_TEMPERATURE_DOCTOR: float = 0.1
    LLM_MAX_RETRIES: int = 3

    # Safety Configuration
    MAX_INPUT_LENGTH: int = 2000
    ENABLE_SAFETY_CHECKS: bool = True
    CRITICAL_SCORE_THRESHOLD: float = 0.8  # For heuristic checks
    BLOCK_UNSAFE_REQUESTS: bool = True

    # Global / Generic Settings
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: List[str] = ["en", "es", "fr", "ar", "de"]
    ENABLE_PROVIDER_INTEGRATION: bool = False
    PROVIDER_API_URL: Optional[str] = None

    # Security
    DATA_ENCRYPTION_KEY: Optional[str] = None
    ADMIN_API_KEY: Optional[str] = None
    AUDIT_SIGNING_KEY: Optional[str] = None

    # Monitoring
    MLFLOW_TRACKING_URI: Optional[str] = None
    ENABLE_LOGGING: bool = True
    LOG_LEVEL: str = "INFO"

    # --- MODEL ROUTING ---
    MODEL_MODE: str = "cloud"  # cloud | local
    LOCAL_MODEL_NAME: str = "meditron"
    OLLAMA_URL: str = "http://localhost:11434"
    VLLM_URL: str = "http://localhost:8000/v1"

    # --- EHR / FHIR INTEGRATION ---
    FHIR_BASE_URL: str = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
    FHIR_CLIENT_ID: Optional[str] = None
    FHIR_CLIENT_SECRET: Optional[str] = None

    # Database
    DATABASE_URL: str = "sqlite:///./medagent.db"

    # API
    MEDAGENT_API_URL: str = "http://localhost:8000"
    CORS_ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Feature Flags
    ENABLE_AUDIO: bool = False

    # Security
    RATE_LIMIT_ENABLED: bool = True
    MAX_REQUESTS_PER_MINUTE: int = 60
    REDIS_URL: Optional[str] = None

    # Notifications (SMTP)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@medagent.local"
    ENABLE_NOTIFICATIONS: bool = True

    # Calendar Integration
    CALENDAR_CREDENTIALS_FILE: Path = BASE_DIR / "credentials.json"
    CALENDAR_TOKEN_FILE: Path = BASE_DIR / "token.json"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()


def get_prompt_path(filename: str) -> Path:
    """Get absolute path to a prompt file with validation."""
    path = settings.PROMPTS_DIR / filename
    if not path.exists():
        # Fallback check or error
        raise FileNotFoundError(
            f"Critical Safety Error: Prompt file {filename} not found at {path}"
        )
    return path


def ensure_directories():
    """Ensure all required directories exist."""
    settings.PROMPTS_DIR.mkdir(exist_ok=True)
    settings.DATA_DIR.mkdir(exist_ok=True)
    settings.RAG_DIR.mkdir(exist_ok=True)
    settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)


# Initialize directories on import
ensure_directories()
