from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DATA_DIR = PROJECT_ROOT / "data" / "private"
DEFAULT_DATABASE_PATH = PRIVATE_DATA_DIR / "eodwin.sqlite"
DEFAULT_EOD_DIR = PRIVATE_DATA_DIR / "eod"


@dataclass(frozen=True)
class Settings:
    database_path: Path = DEFAULT_DATABASE_PATH
    eod_dir: Path = DEFAULT_EOD_DIR
    eodhd_api_key: str | None = None


def load_env(path: Path | None = None) -> None:
    env_path = path or PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_settings() -> Settings:
    load_env()
    return Settings(eodhd_api_key=os.getenv("EODHD_API_KEY"))
