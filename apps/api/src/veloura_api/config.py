from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root .env, resolved by file location rather than cwd so `make migrate`,
# pytest, and running uvicorn all find the same file regardless of where
# they're invoked from. Falls back to a cwd-relative lookup in shallower
# layouts (e.g. inside the Docker image), where real env vars are used instead.
_PARENTS = list(Path(__file__).resolve().parents)
REPO_ROOT_ENV_FILE = _PARENTS[4] / ".env" if len(_PARENTS) > 4 else Path(".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT_ENV_FILE, extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://veloura:veloura@localhost:5432/veloura"

    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440

    veloura_cors_allowed_origins: str = "http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.veloura_cors_allowed_origins.split(",") if o.strip()]

    @property
    def is_ai_enabled(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
