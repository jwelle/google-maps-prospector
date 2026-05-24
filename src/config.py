import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # Allows `--help` and syntax checks before dependencies are installed.
    load_dotenv = None


@dataclass(frozen=True)
class Config:
    google_maps_api_key: str
    default_max_results: int
    request_timeout_seconds: float
    crawl_delay_seconds: float
    max_pages_per_site: int


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def load_config() -> Config:
    if load_dotenv is not None:
        root_dir = Path(__file__).resolve().parent.parent
        load_dotenv(root_dir / ".env.local")
        load_dotenv(root_dir / ".env", override=False)

    return Config(
        google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY", "").strip(),
        default_max_results=_get_int("DEFAULT_MAX_RESULTS", 100),
        request_timeout_seconds=_get_float("REQUEST_TIMEOUT_SECONDS", 10.0),
        crawl_delay_seconds=_get_float("CRAWL_DELAY_SECONDS", 1.0),
        max_pages_per_site=_get_int("MAX_PAGES_PER_SITE", 5),
    )
