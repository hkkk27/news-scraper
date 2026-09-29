"""Load a tracker profile (the config/ folder) into typed settings.

A profile is a directory with:
    settings.yaml          global knobs (this module)
    taxonomy/*.yaml        sectors, categories and streams
    geography/*.yaml       states/UTs, cities and aliases
    sources/*.yaml         feeds, query packs, watched pages, X handles

Secrets never live in YAML; they come from environment variables (or a local .env).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# settings.yaml
# ---------------------------------------------------------------------------


class ProfileSettings(BaseModel):
    name: str = "News Tracker"
    country: str = "IN"
    timezone: str = "Asia/Kolkata"


class StorageSettings(BaseModel):
    backend: Literal["sqlite"] = "sqlite"
    path: str = "data/tracker.db"


class FullTextSettings(BaseModel):
    enabled: bool = True
    max_per_run: int = 40
    min_score: int = 55


class CollectionSettings(BaseModel):
    lookback_hours: int = 72
    http_timeout_seconds: float = 20
    max_items_per_source: int = 150
    user_agent: str = "Mozilla/5.0 NewsTracker/0.1"
    full_text: FullTextSettings = Field(default_factory=FullTextSettings)


class DedupSettings(BaseModel):
    window_hours: int = 72
    story_similarity: float = 0.4


class Bands(BaseModel):
    core: int = 80
    relevant: int = 60
    peripheral: int = 40

    def band(self, score: float) -> str:
        if score >= self.core:
            return "core"
        if score >= self.relevant:
            return "relevant"
        if score >= self.peripheral:
            return "peripheral"
        return "not_relevant"


class ModelSettings(BaseModel):
    enabled: bool = True
    min_labels: int = 20
    full_weight_at: int = 200
    max_weight: float = 0.7


class LLMSettings(BaseModel):
    provider: Literal["none", "openrouter"] = "none"
    models: list[str] = Field(default_factory=lambda: ["openrouter/free"])
    uncertain_low: int = 40
    uncertain_high: int = 65
    batch_size: int = 20
    max_requests_per_day: int = 40
    max_seconds_per_run: int = 150


class RelevanceSettings(BaseModel):
    bands: Bands = Field(default_factory=Bands)
    model: ModelSettings = Field(default_factory=ModelSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)


class ReportSettings(BaseModel):
    exec_top_n: int = 8
    digest_min_band: Literal["core", "relevant", "peripheral"] = "relevant"
    output_dir: str = "output/reports"


class TelegramSettings(BaseModel):
    brief_max_items: int = 10


class DashboardSettings(BaseModel):
    days: int = 30
    min_band: Literal["core", "relevant", "peripheral", "not_relevant"] = "peripheral"
    output_dir: str = "output/site"


class RetentionSettings(BaseModel):
    not_relevant_days: int = 30


class Settings(BaseModel):
    profile: ProfileSettings = Field(default_factory=ProfileSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    collection: CollectionSettings = Field(default_factory=CollectionSettings)
    dedup: DedupSettings = Field(default_factory=DedupSettings)
    relevance: RelevanceSettings = Field(default_factory=RelevanceSettings)
    reports: ReportSettings = Field(default_factory=ReportSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    dashboard: DashboardSettings = Field(default_factory=DashboardSettings)
    retention: RetentionSettings = Field(default_factory=RetentionSettings)


# ---------------------------------------------------------------------------
# Secrets (environment)
# ---------------------------------------------------------------------------


class Secrets(BaseModel):
    telegram_bot_token: str = ""
    telegram_allowed_chat_ids: list[int] = Field(default_factory=list)
    gemini_api_key: str = ""
    apify_token: str = ""
    openrouter_api_keys: list[str] = Field(default_factory=list)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    report_email_to: list[str] = Field(default_factory=list)
    report_email_to_exec: list[str] = Field(default_factory=list)

    @classmethod
    def from_env(cls) -> "Secrets":
        def env(name: str, default: str = "") -> str:
            return os.environ.get(name, default).strip()

        def split(value: str) -> list[str]:
            return [part.strip() for part in value.split(",") if part.strip()]

        return cls(
            telegram_bot_token=env("TELEGRAM_BOT_TOKEN"),
            telegram_allowed_chat_ids=[int(x) for x in split(env("TELEGRAM_ALLOWED_CHAT_IDS")) if x.lstrip("-").isdigit()],
            gemini_api_key=env("GEMINI_API_KEY"),
            apify_token=env("APIFY_TOKEN"),
            openrouter_api_keys=split(env("OPENROUTER_API_KEYS").replace(";", ",")),
            smtp_host=env("SMTP_HOST", "smtp.gmail.com") or "smtp.gmail.com",
            smtp_port=int(env("SMTP_PORT", "587") or 587),
            smtp_user=env("SMTP_USER"),
            smtp_password=env("SMTP_PASSWORD"),
            report_email_to=split(env("REPORT_EMAIL_TO")),
            report_email_to_exec=split(env("REPORT_EMAIL_TO_EXEC")),
        )


def load_dotenv(path: Path) -> None:
    """Minimal .env reader: KEY=VALUE lines; existing environment variables win."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


def read_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a mapping at the top level")
    return data


def read_yaml_dir(directory: Path) -> list[tuple[Path, dict]]:
    """All *.yaml files in a directory, sorted by name, as (path, data) pairs."""
    if not directory.is_dir():
        return []
    return [(p, read_yaml(p)) for p in sorted(directory.glob("*.yaml"))]


class AppConfig:
    """Everything the pipeline needs: settings, secrets and (later) taxonomy and sources."""

    def __init__(self, config_dir: Path, settings: Settings, secrets: Secrets):
        self.config_dir = config_dir
        self.settings = settings
        self.secrets = secrets

    def resolve(self, relative: str) -> Path:
        """Resolve a path from settings relative to the project root."""
        path = Path(relative)
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def db_path(self) -> Path:
        return self.resolve(self.settings.storage.path)


def default_config_dir() -> Path:
    override = os.environ.get("TRACKER_CONFIG_DIR", "").strip()
    return Path(override) if override else PROJECT_ROOT / "config"


def load_config(config_dir: Path | str | None = None) -> AppConfig:
    load_dotenv(PROJECT_ROOT / ".env")
    directory = Path(config_dir) if config_dir else default_config_dir()
    settings_file = directory / "settings.yaml"
    settings = Settings.model_validate(read_yaml(settings_file)) if settings_file.exists() else Settings()
    return AppConfig(directory, settings, Secrets.from_env())
