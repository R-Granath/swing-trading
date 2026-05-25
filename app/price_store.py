from __future__ import annotations

import csv
from datetime import UTC, date, datetime
from pathlib import Path

from app.config import DEFAULT_EOD_DIR


PRICE_COLUMNS = [
    "date",
    "open",
    "high",
    "low",
    "close",
    "adjusted_close",
    "volume",
    "source",
    "fetched_at",
]


def symbol_to_filename(symbol: str) -> str:
    return f"{symbol.upper().replace('/', '_')}.csv"


def price_path(symbol: str, eod_dir: Path = DEFAULT_EOD_DIR) -> Path:
    return eod_dir / symbol_to_filename(symbol)


def save_prices(symbol: str, rows: list[dict], eod_dir: Path = DEFAULT_EOD_DIR) -> Path:
    eod_dir.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(UTC).isoformat()
    path = price_path(symbol, eod_dir)

    merged_rows = {row["date"]: row for row in load_prices(symbol, eod_dir)}
    for row in rows:
        merged_rows[row["date"]] = {
            "date": row.get("date"),
            "open": row.get("open"),
            "high": row.get("high"),
            "low": row.get("low"),
            "close": row.get("close"),
            "adjusted_close": row.get("adjusted_close"),
            "volume": row.get("volume"),
            "source": "eodhd",
            "fetched_at": fetched_at,
        }

    normalized_rows = [merged_rows[key] for key in sorted(merged_rows)]

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PRICE_COLUMNS)
        writer.writeheader()
        writer.writerows(normalized_rows)

    return path


def load_prices(symbol: str, eod_dir: Path = DEFAULT_EOD_DIR) -> list[dict]:
    path = price_path(symbol, eod_dir)
    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def latest_price_date(symbol: str, eod_dir: Path = DEFAULT_EOD_DIR) -> date | None:
    rows = load_prices(symbol, eod_dir)
    if not rows:
        return None
    return max(date.fromisoformat(row["date"]) for row in rows)


def earliest_price_date(symbol: str, eod_dir: Path = DEFAULT_EOD_DIR) -> date | None:
    rows = load_prices(symbol, eod_dir)
    if not rows:
        return None
    return min(date.fromisoformat(row["date"]) for row in rows)
