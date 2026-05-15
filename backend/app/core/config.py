import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str
    env: str
    log_level: str
    sqlite_path: str
    gemini_api_key: str
    gemini_model: str
    gemini_temperature: float
    gemini_max_retries: int
    gemini_timeout_s: int


def _read_env(key: str, default: str) -> str:
    return os.getenv(key, default)


def _load_env_file() -> None:
    if load_dotenv is None:
        return
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)


def _read_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _read_float(key: str, default: float) -> float:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@lru_cache
def get_settings() -> Settings:
    _load_env_file()
    return Settings(
        app_name=_read_env("APP_NAME", "Emergent Fraud Lab"),
        env=_read_env("APP_ENV", "local"),
        log_level=_read_env("LOG_LEVEL", "INFO"),
        sqlite_path=_read_env("SQLITE_PATH", "data/app.db"),
        gemini_api_key=_read_env("GEMINI_API_KEY", ""),
        gemini_model=_read_env("GEMINI_MODEL", "gemini-1.5-flash"),
        gemini_temperature=_read_float("GEMINI_TEMPERATURE", 0.2),
        gemini_max_retries=_read_int("GEMINI_MAX_RETRIES", 2),
        gemini_timeout_s=_read_int("GEMINI_TIMEOUT_S", 30),
    )
