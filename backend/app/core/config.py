"""Application configuration.

Settings are loaded once from environment variables and validated at startup by
pydantic-settings. Nothing here is hard-coded with a real secret; every sensitive
value comes from the environment (see `.env.example`). Inject `get_settings()` as a
FastAPI dependency rather than importing a global — it keeps things testable.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> parents[3] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Always the repo-root .env, regardless of the working directory the app
        # is launched from (`uvicorn` from backend/, pytest, alembic, …). Real
        # environment variables still take precedence, which is how Docker and
        # production inject config.
        env_file=str(_REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- Core ----
    environment: str = "development"
    log_level: str = "INFO"
    project_name: str = "Catchy"
    api_v1_prefix: str = "/api/v1"

    # ---- Scanning limits ----
    # Cap the raw email size we will parse. Emails larger than this are rejected
    # before parsing, bounding memory use and blunting a trivial DoS vector.
    max_email_bytes: int = 2_000_000  # 2 MB

    # ---- ML serving ----
    # Path to the M3 model bundle. Absent (e.g. CI, or before first training) is
    # fine: scoring degrades gracefully to the rule engine. Override via env in prod.
    model_path: str = str(_REPO_ROOT / "ml" / "models" / "catchy_model.joblib")
    # On a confirmed-malicious signal, the fused score is floored to at least this,
    # so a single decisive indicator can't be averaged away into "looks fine".
    critical_override_floor: int = 90

    # ---- Database ----
    postgres_user: str = "catchy"
    postgres_password: str = "change-me-in-prod"
    postgres_db: str = "catchy"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # ---- Redis (cache + Celery broker) ----
    redis_url: str = "redis://redis:6379/0"

    # ---- Auth (M7) ----
    # JWT signing secret. The default is dev-only; set a long random value in prod.
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60 * 12

    # ---- Threat intelligence (M5) ----
    # Master switch. Off by default: with no keys the enrichment is a no-op, and
    # keeping it explicit means the local pipeline stays deterministic in tests/CI.
    intel_enabled: bool = False
    virustotal_api_key: str = ""
    urlscan_api_key: str = ""
    hibp_api_key: str = ""
    intel_cache_ttl_seconds: int = 86_400  # reputation changes slowly; cache a day
    intel_provider_timeout_seconds: float = 4.0  # bound each external call
    intel_max_urls: int = 5  # only enrich the top-N URLs to respect rate limits

    # ---- LLM analyst (Gemini first; provider-swappable) ----
    llm_enabled: bool = True  # off => never call the LLM even with a key
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    # Google retires older models for new API keys, so keep this current.
    # flash-lite is fast and has the most headroom on the free tier;
    # `gemini-3-flash-preview` is more capable but sheds load under demand.
    llm_model: str = "gemini-3.1-flash-lite"
    llm_timeout_seconds: float = 8.0
    # Cap the email text handed to the LLM: bounds tokens/cost and shrinks the
    # prompt-injection surface. The verdict is already decided, so this is lossy
    # only for the *explanation*, never for detection.
    llm_max_input_chars: int = 4_000

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor. Wrapped so it can be overridden in tests."""
    return Settings()
