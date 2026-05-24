from __future__ import annotations

import csv
from datetime import UTC, datetime
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

    normalized_rows = []
    for row in sorted(rows, key=lambda item: item["date"]):
        normalized_rows.append(
            {
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
        )

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
